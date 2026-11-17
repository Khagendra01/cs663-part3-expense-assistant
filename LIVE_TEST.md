Khagendra Khatri
Nov 17, 2026
CS663 Computer Vision

# Live Gemini test: Part 3 Option 3 Personal Expense Assistant

AI use citation: this note was written with Muse assistance. I checked the
auth state and the sample images, and I am responsible for the result.

## Status: live test NOT run

The live Gemini test was not run on Nov 17, 2026, because no Gemini
auth was present in this VM. No key was invented and none was asked for.
The tool tests in TESTING.md still stand: 9 passed, 0 failed, with no
LLM call. This file records exactly what is missing and the exact test
to run once auth is present.

## Auth check, Nov 17, 2026

Checked in the shell that runs the agent:

- GOOGLE_API_KEY: absent (checked with Python os.environ, length 0)
- GOOGLE_APPLICATION_CREDENTIALS: absent
- ~/.config/gcloud/application_default_credentials.json: absent, and
  there is no ~/.config/gcloud directory at all
- gcloud CLI: not installed in this VM (which gcloud exits 1)
- settings.yaml: not created yet (only settings.yaml.example exists,
  with project cs663-dog-training and location us-central1)
- data/expenses.db: not created yet (it is created on the first store)

What this means: the agent code picks Vertex AI when no
GOOGLE_API_KEY is set, but Vertex AI needs application default
credentials, and there are none here. The browser sign in to Google
Cloud Console as khagendrakhatri365@gmail.com on Nov 17, 2026 does
not by itself give this VM credentials. It confirmed the project
cs663-dog-training and that the Vertex AI API is enabled, but a
separate auth step is still needed for a local run.

## Sample receipt images verified

All 3 files are readable PNG images, checked with `file` and Pillow:

- trader-joes-2026-11-10.png: PNG, 640 x 720, RGB. Trader Joe's,
  2026-11-10, total 42.18 USD, 6 items.
- starbucks-2026-11-12.png: PNG, 640 x 512, RGB. Starbucks,
  2026-11-12, total 6.45 USD, 2 items.
- target-2026-11-14.png: PNG, 640 x 668, RGB. Target, 2026-11-14,
  total 87.20 USD, 5 items.

Expected total across all 3: 135.83 USD. Average: 45.28 USD.

## Fix 1: free AI Studio key (fastest)

Get a free key at https://aistudio.google.com/apikey, then run this
one line in the project folder before starting the agent. Do not put
the key in any file.

```
export GOOGLE_API_KEY=your-key-here
```

## Fix 2: Vertex AI with the class project

In Cloud Shell, or on a machine with gcloud installed, run:

```
gcloud auth application-default login
```

Then set the project to cs663-dog-training. The agent reads the
project and location from settings.yaml, so first copy the example:

```
cp settings.yaml.example settings.yaml
```

## Exact 3-turn test script, once auth is present

Run from the project folder part3-expense-assistant. Use a fresh
database so the totals are clean: delete data/expenses.db first if
it exists, then start the ADK web UI:

```
.venv/bin/adk web
```

Open http://localhost:8000, pick expense_manager_agent, then do
these 3 turns in order, in the same chat session.

Turn 1. Upload data/sample_receipts/target-2026-11-14.png and type:

```
Please store this receipt.
```

Expected reply: the agent stores Target, 2026-11-14, total 87.20
USD, with 5 items, and says the receipt was stored successfully.

Turn 2. Type:

```
How much did I spend at Target?
```

Expected reply: 87.20 USD for the Target receipt on 2026-11-14.

Turn 3. First store the other 2 sample receipts the same way
(Trader Joe's, then Starbucks), so all 3 are stored. Then type:

```
What is my total spending in November?
```

Expected reply: total 135.83 USD across 3 receipts: Trader Joe's
42.18, Starbucks 6.45, Target 87.20. Average 45.28 USD.

Pass rule: turn 1 stores 87.20, turn 2 answers 87.20, turn 3
answers 135.83. If any total differs, copy the agent reply
verbatim into this file under a "Live run" section with the date,
and do not edit the expected values to match the reply.

## Runner script option (same 3 turns, no web UI)

Save the script below as /tmp/live_test.py and run it from the
project folder with .venv/bin/python /tmp/live_test.py. It uses
the ADK Runner with an in-memory session, sends the Target image
as a multimodal message, then asks the same 2 questions. It needs
the same auth as above, and a fresh data/expenses.db. If the
Runner import differs in the installed google-adk version, use
the adk web steps above instead.

```python
import asyncio
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from expense_manager_agent.agent import root_agent

PROJECT = Path(__file__).resolve().parent
BASE = Path("data/sample_receipts")

async def main():
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="expense_manager_agent",
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name="expense_manager_agent",
        user_id="khagendra",
    )
    image_bytes = (BASE / "target-2026-11-14.png").read_bytes()
    turns = [
        types.Content(
            role="user",
            parts=[
                types.Part(text="Please store this receipt."),
                types.Part.from_bytes(
                    data=image_bytes, mime_type="image/png"
                ),
            ],
        ),
        types.Content(
            role="user",
            parts=[types.Part(text="How much did I spend at Target?")],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text="What is my total spending in November?"
                )
            ],
        ),
    ]
    for turn in turns:
        print("--- TURN ---")
        async for event in runner.run_async(
            user_id="khagendra",
            session_id=session.id,
            new_message=turn,
        ):
            if event.is_final_response() and event.content:
                print(event.content.parts[0].text)

asyncio.run(main())
```

Note on turn 3 in the Runner script: the total is 135.83 USD only
if all 3 sample receipts are stored first. The script above stores
only Target, so add the Trader Joe's and Starbucks images the same
way before asking for the November total, or run the adk web steps
above instead.
