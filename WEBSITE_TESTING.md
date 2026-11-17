Khagendra Khatri
Nov 17, 2026
CS663 Computer Vision

# Website testing: Part 3 Option 3 Personal Expense Assistant

AI use citation: this build used Muse and Gemini assistance to write
code, tests, and docs. I checked the code, ran the tests, and I am
responsible for the result.

## What was tested

The website is backend/main.py (FastAPI, port 8081) and
frontend/app.py (Gradio, port 7860). Both reuse the existing agent
and the same SQLite file at data/expenses.db. No second database
was created, and expense_manager_agent/agent.py and tools.py were
not changed.

## Install

Command, run from the project folder:

```
.venv/bin/pip install -q "gradio>=5.23.1,<6" "starlette>=0.46.2,<1.0.0" "fastapi>=0.115,<0.120"
```

Result: installed gradio 5.50.0, fastapi 0.119.1, starlette 0.48.0.
These are the versions now in requirements.txt.

Two install problems were found and fixed:

1. Gradio 6 pulled starlette 1.10.0, which google-adk 1.18.0
   rejects (it needs starlette below 1.0.0). Gradio was pinned
   to below 6, and starlette to below 1.0.0, to match the codelab
   version range.
2. On this VM the NO_PROXY list contains bracketed IPv6 entries
   like [::1], which httpx cannot parse. Gradio builds an httpx
   client at import time, so the import failed with
   httpx.InvalidURL: Invalid port: ':1]'. This is a VM
   environment problem, not a code problem. frontend/app.py and
   tests/conftest.py now drop only the bracketed entries from
   NO_PROXY before gradio is imported. After that fix the tests
   pass with the normal VM environment, no clean env needed.

## Automated tests

Command:

```
.venv/bin/pytest tests/test_website.py -v
```

Result: 6 passed, 0 failed, in about 19 seconds.

Tests and what each covers:

1. test_health_ok: pass. GET /health returns 200 and
   {"status": "ok", "agent": "expense_manager_agent"}.
2. test_receipts_shape: pass. GET /receipts returns 200 with a
   count and a receipts list, each item with store_name and
   total_amount.
3. test_chat_no_key_returns_503: pass. POST /chat with
   "How much did I spend at Target?" returns 503 and the detail
   starts "No Gemini key is set".
4. test_chat_no_key_with_image_returns_503: pass. POST /chat
   with a receipt image and no key also returns 503, it does
   not crash.
5. test_chat_empty_message_returns_400: pass. POST /chat with
   a blank message returns 400.
6. test_frontend_builds: pass. The Gradio app builds, it has
   the 3 example prompts, and it returns a gr.Blocks object.

Only warnings are upstream deprecation warnings from starlette,
google-adk, and pydantic, plus a Gradio 6.0 allow_tags notice.
None of them stop the tests.

## Live backend test

The backend was started with no Gemini key set, then stopped
again after the checks:

```
env -u GOOGLE_API_KEY -u GOOGLE_APPLICATION_CREDENTIALS .venv/bin/python -m backend.main
```

Results, all with curl:

- GET http://localhost:8081/health
  HTTP 200, {"status": "ok", "agent": "expense_manager_agent"}
- GET http://localhost:8081/receipts
  HTTP 200, {"count": 0, "receipts": []}
  The stored receipts list is empty here because the sample
  receipts were stored only inside the tool tests, not in this
  database file. The endpoint itself works.
- POST http://localhost:8081/chat with
  {"message": "How much did I spend at Target?"}
  HTTP 503, detail: "No Gemini key is set. Set GOOGLE_API_KEY
  to a free Google AI Studio key
  (https://aistudio.google.com/apikey) or run gcloud auth
  application-default login for Vertex AI project
  cs663-dog-training, then try again."
- POST http://localhost:8081/chat with {"message": "   "}
  HTTP 400, detail: "Send a message or a receipt image."

The backend was confirmed stopped after the test with
curl http://localhost:8081/health returning no response.

## Frontend live launch: not run

The Gradio frontend was not launched live here. The build test
above proves the app builds and has the chat box, image upload,
and example prompts. A live launch needs the backend running
first and a Gemini key for chat, so it is left for the demo run:

```
.venv/bin/python -m backend.main
.venv/bin/python -m frontend.app
```

Then open http://localhost:7860.

## Live Gemini turn: not run here

No live Gemini turn was run here, same as in TESTING.md. No
GOOGLE_API_KEY, no GOOGLE_APPLICATION_CREDENTIALS, and no
application default credentials file were present. No key was
invented. To run the live demo, set a free AI Studio key first:

```
export GOOGLE_API_KEY=your-key-here
.venv/bin/python -m backend.main
.venv/bin/python -m frontend.app
```

Then upload a sample receipt at http://localhost:7860 and use
the 3 example prompts. Or use Vertex AI with the project
cs663-dog-training in us-central1 after
gcloud auth application-default login.

## Not done

Cloud Run deploy was not done, as instructed. No GCP keys were
created. Nothing was submitted to Canvas.
