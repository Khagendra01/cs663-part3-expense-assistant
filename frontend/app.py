"""Gradio frontend for the CS663 Part 3 expense assistant.

Chat box plus receipt image upload. It sends each turn to the
FastAPI backend at BACKEND_URL from settings
(default http://localhost:8081/chat). It does not call Gemini
directly and it does not read the SQLite file itself.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Gradio builds an httpx client at import time. On this VM the
# NO_PROXY list contains bracketed IPv6 entries like [::1], which
# httpx cannot parse and which make the import fail. Drop only the
# bracketed entries, keep localhost and 127.0.0.1, before importing
# gradio. On a normal machine this changes nothing.
for _key in ("NO_PROXY", "no_proxy"):
    _value = os.environ.get(_key)
    if _value:
        _kept = [p for p in _value.split(",") if "[" not in p]
        os.environ[_key] = ",".join(_kept)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr

from settings import get_settings

SETTINGS = get_settings()
BACKEND_URL = SETTINGS.BACKEND_URL
BACKEND_BASE = BACKEND_URL.rsplit("/chat", 1)[0]

EXAMPLE_PROMPTS = [
    "Please store this receipt",
    "How much did I spend at Target?",
    "What is my total spending in November?",
]


def _post_chat(message, image_path):
    payload = {"message": message}
    if image_path:
        path = Path(image_path)
        payload["image_base64"] = base64.b64encode(path.read_bytes()).decode("ascii")
        payload["image_filename"] = path.name
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BACKEND_URL, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
            detail = body.get("detail", str(exc))
        except Exception:
            detail = str(exc)
        return {"reply": f"Backend said ({exc.code}): {detail}", "tools_used": []}
    except Exception as exc:
        return {"reply": f"Could not reach the backend at {BACKEND_URL}: {exc}", "tools_used": []}


def _get_receipts():
    try:
        with urllib.request.urlopen(BACKEND_BASE + "/receipts", timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {"count": 0, "receipts": [], "error": str(exc)}


def respond(message, image_path, history):
    message = (message or "").strip()
    if not message and not image_path:
        return history, "", None
    if not message:
        message = "Please store this receipt"
    result = _post_chat(message, image_path)
    reply = result.get("reply", "No reply from the backend.")
    tools = result.get("tools_used") or []
    if tools:
        reply += "\n\nTools used: " + ", ".join(tools)
    history = history + [{"role": "user", "content": message}]
    if image_path:
        history[-1]["content"] += f" [receipt image: {Path(image_path).name}]"
    history = history + [{"role": "assistant", "content": reply}]
    return history, "", None


def show_receipts(history):
    data = _get_receipts()
    if data.get("error"):
        text = f"Could not list receipts: {data['error']}"
    elif data.get("count", 0) == 0:
        text = "No receipts stored yet. Upload one and ask the agent to store it."
    else:
        lines = [f"Stored receipts: {data['count']}"]
        for item in data["receipts"]:
            lines.append(
                f"{item['store_name']}, {item['transaction_time'][:10]}, "
                f"{item['total_amount']:.2f} {item['currency']}"
            )
        text = "\n".join(lines)
    history = history + [
        {"role": "user", "content": "Show stored receipts"},
        {"role": "assistant", "content": text},
    ]
    return history


def build_demo():
    with gr.Blocks(title="CS663 Part 3 Expense Assistant") as demo:
        gr.Markdown(
            "# CS663 Part 3 Expense Assistant\n"
            "Upload a receipt image, ask the agent to store it, "
            "then ask about your spending."
        )
        chatbot = gr.Chatbot(label="Expense assistant", type="messages")
        image = gr.Image(type="filepath", label="Receipt image (optional)")
        msg = gr.Textbox(
            label="Message",
            placeholder="Please store this receipt",
        )
        with gr.Row():
            send = gr.Button("Send", variant="primary")
            clear = gr.Button("Clear chat")
            receipts_btn = gr.Button("Show stored receipts")
        with gr.Row():
            example_buttons = [
                gr.Button(prompt, size="sm") for prompt in EXAMPLE_PROMPTS
            ]
        send.click(respond, inputs=[msg, image, chatbot], outputs=[chatbot, msg, image])
        msg.submit(respond, inputs=[msg, image, chatbot], outputs=[chatbot, msg, image])
        clear.click(lambda: [], outputs=[chatbot])
        receipts_btn.click(show_receipts, inputs=[chatbot], outputs=[chatbot])
        for button, prompt in zip(example_buttons, EXAMPLE_PROMPTS):
            button.click(lambda p=prompt: p, outputs=[msg])
    return demo


if __name__ == "__main__":
    build_demo().launch(server_name="0.0.0.0", server_port=7860)
