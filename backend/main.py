"""FastAPI backend for the CS663 Part 3 expense assistant.

Runs the existing ADK agent (expense_manager_agent) through a Runner
with an in-memory session service. It does not create a second
database. Receipt reads go through expense_manager_agent.tools,
which use the same local SQLite file at data/expenses.db.

Endpoints:
- GET /health: ok when the server is up. It does not call Gemini.
- GET /receipts: list of stored receipts from SQLite.
- POST /chat: send a message, with an optional receipt image, to the
  agent. Returns the agent reply and the tools it used.

A Gemini backend is needed for /chat. If no GOOGLE_API_KEY is set
and no Vertex AI application default credentials exist, /chat
returns HTTP 503 with a clear message instead of crashing.
"""

import base64
import hashlib
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from settings import get_settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS = get_settings()

APP_NAME = "expense_manager"
DEFAULT_USER_ID = "demo-user"
DEFAULT_SESSION_ID = "demo-session"

app = FastAPI(title="CS663 Part 3 Expense Assistant backend")


class ChatRequest(BaseModel):
    message: str
    image_base64: Optional[str] = None
    image_filename: Optional[str] = None
    user_id: str = DEFAULT_USER_ID
    session_id: str = DEFAULT_SESSION_ID


class ChatResponse(BaseModel):
    reply: str
    tools_used: List[str]


def _gemini_available() -> bool:
    """Return True when a Gemini backend can be reached."""
    if os.environ.get("GOOGLE_API_KEY"):
        return True
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds and Path(creds).is_file():
        return True
    adc = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    if adc.is_file():
        return True
    return False


def _missing_key_message() -> str:
    return (
        "No Gemini key is set. Set GOOGLE_API_KEY to a free Google AI Studio "
        "key (https://aistudio.google.com/apikey) or run "
        "gcloud auth application-default login for Vertex AI project "
        f"{SETTINGS.GCLOUD_PROJECT_ID}, then try again."
    )


def _get_runner():
    """Build the ADK Runner lazily, so /health and /receipts work with no key."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    from expense_manager_agent.agent import root_agent

    session_service = InMemorySessionService()
    return Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    ), session_service


_RUNNER = None
_SESSION_SERVICE = None


def _runner_and_sessions():
    global _RUNNER, _SESSION_SERVICE
    if _RUNNER is None:
        _RUNNER, _SESSION_SERVICE = _get_runner()
    return _RUNNER, _SESSION_SERVICE


async def _ensure_session(session_service, user_id: str, session_id: str):
    try:
        existing = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
    except Exception:
        existing = None
    if existing is None:
        await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "agent": "expense_manager_agent"}


@app.get("/receipts")
def list_receipts() -> Dict[str, Any]:
    from expense_manager_agent.tools import _all_receipts

    receipts = _all_receipts()
    return {"count": len(receipts), "receipts": receipts}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip() and not request.image_base64:
        raise HTTPException(status_code=400, detail="Send a message or a receipt image.")
    if not _gemini_available():
        raise HTTPException(status_code=503, detail=_missing_key_message())

    from google.genai import types

    runner, session_service = _runner_and_sessions()
    await _ensure_session(session_service, request.user_id, request.session_id)

    parts: List[Any] = []
    if request.image_base64:
        try:
            image_bytes = base64.b64decode(request.image_base64, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail="image_base64 is not valid base64.")
        filename = request.image_filename or "receipt.png"
        safe_name = Path(filename).name or "receipt.png"
        mime, _ = mimetypes.guess_type(safe_name)
        if mime is None or not mime.startswith("image/"):
            mime = "image/png"
        receipts_dir = PROJECT_ROOT / SETTINGS.RECEIPTS_DIR
        receipts_dir.mkdir(parents=True, exist_ok=True)
        image_id = hashlib.sha256(image_bytes).hexdigest()[:12]
        saved = receipts_dir / f"{image_id}-{safe_name}"
        saved.write_bytes(image_bytes)
        parts.append(types.Part(inline_data=types.Blob(mime_type=mime, data=image_bytes)))
        if not request.message.strip():
            request = request.model_copy(update={"message": "Please store this receipt."})
    parts.append(types.Part(text=request.message))

    content = types.Content(role="user", parts=parts)
    reply_parts: List[str] = []
    tools_used: List[str] = []
    try:
        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=content,
        ):
            for call in event.get_function_calls():
                if call.name and call.name not in tools_used:
                    tools_used.append(call.name)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        reply_parts.append(part.text)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Gemini call failed: {exc}. {_missing_key_message()}",
        )

    reply = "".join(reply_parts).strip()
    if not reply:
        reply = "The agent gave no text reply."
    return ChatResponse(reply=reply, tools_used=tools_used)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)
