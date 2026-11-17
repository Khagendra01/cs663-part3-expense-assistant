Khagendra Khatri
Nov 17, 2026
CS663 Computer Vision

# CS663 Part 3 Option 3: Personal Expense Assistant

AI use citation: this build used Muse and Gemini assistance to write
code, tests, and docs. I checked the code, ran the tests, and I am
responsible for the result.

Grading note: projects are 70 percent of the grade in this course,
so this README stays focused on what was built, what was tested
with exact numbers, and the limits.

## What it does

This is a multimodal agent built with Google ADK and Gemini 2.5 Flash.
You upload a receipt image. The agent reads the store name, the date,
the items, and the total. It stores that data. Then you can ask it
questions about your spending.

It can store a receipt, find a receipt by its image id, search receipts
by date and amount, search receipts by words like coffee or Starbucks,
and give a spending summary by store and by month.

## What is local and what the codelab did

The codelab used Firestore for storage, text-embedding-004 for vector
search, Google Cloud Storage for receipt files, and Cloud Run for deploy.
That setup needs billing and a cloud project.

This version runs locally with no billing. Storage is a local SQLite
file at data/expenses.db. Receipt images live in data/receipts.
Natural language search uses keyword matching over the store name,
the item names, and the receipt text. No embedding call is needed.

To swap back to the codelab setup, replace the SQLite helpers in
expense_manager_agent/tools.py with the Firestore client from the
codelab, restore the text-embedding-004 call in store_receipt_data,
and restore the vector query in
search_relevant_receipts_by_natural_language_query.

One more change from the codelab: the callback keeps only the most
recent image in the chat history. The codelab kept the last 3 images.
Older images are still reachable by their [IMAGE-ID ...] placeholder
through get_receipt_data_by_image_id.

The codelab default currency was IDR. This version uses USD.

## Files

- expense_manager_agent/agent.py: the root agent, gemini-2.5-flash,
  BuiltInPlanner with thinking_budget 2048.
- expense_manager_agent/tools.py: the 5 tools, backed by SQLite.
- expense_manager_agent/callbacks.py: modify_image_data_in_history.
- expense_manager_agent/task_prompt.md: the agent instruction.
- settings.py and settings.yaml.example: config with pydantic-settings.
- backend/main.py: FastAPI backend on port 8081, /health, /receipts, /chat.
- frontend/app.py: Gradio frontend on port 7860, chat plus receipt upload.
- data/sample_receipts/: 3 sample receipt PNGs and expected.json.
- tests/test_tools.py: tool tests. No LLM call is needed.
- tests/test_website.py: website tests. No LLM call is needed.

## How to run

Create the venv and install the deps:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Copy the config example:

```
cp settings.yaml.example settings.yaml
```

Pick one backend. Option A is Vertex AI, the codelab default. It
uses the project cs663-dog-training in us-central1 from settings.yaml.
You need Google Cloud credentials, for example from
gcloud auth application-default login.

Option B is Google AI Studio, the free key path. Get a free key at
https://aistudio.google.com/apikey and set it before you start:

```
export GOOGLE_API_KEY=your-key-here
```

If GOOGLE_API_KEY is set, the agent uses AI Studio and does not force
Vertex AI. If it is not set, the agent uses Vertex AI.

Never put a real key in a file. The .env.example file has placeholders
only. The .gitignore file excludes settings.yaml, .env, and
data/expenses.db.

Start the ADK web UI:

```
.venv/bin/adk web
```

Open http://localhost:8000, pick expense_manager_agent, and upload a
receipt image. Or use the CLI:

```
.venv/bin/adk run expense_manager_agent
```

## Website demo

There is also a website version of the same agent, in backend/ and
frontend/. It uses the same agent and the same SQLite file, so
receipts stored in one demo show up in the other.

Run the backend first, in one terminal:

```
.venv/bin/python -m backend.main
```

It listens at http://localhost:8081. Check it with
curl http://localhost:8081/health, which should return ok.

Then run the frontend, in a second terminal:

```
.venv/bin/python -m frontend.app
```

It listens at http://localhost:7860. Open that page, upload a
receipt image, and use the example prompts: "Please store this
receipt", "How much did I spend at Target?", "What is my total
spending in November?"

The frontend calls BACKEND_URL from settings, default
http://localhost:8081/chat. The live chat still needs a Gemini
key, see the backend section above. The health check and the
stored receipts list work with no key.

Cloud Run deploy is a separate step and is not done here. It
would need a Dockerfile and the same settings as the codelab,
plus a Gemini key or Vertex AI credentials in the cloud project.

## Demo script

Record this as a short narrated screen recording, about 3 minutes,
in plain student voice. Film it on a phone if you record the screen
that way, or record the screen directly, then upload the video to
YouTube as UNLISTED, per the syllabus. The full word for word script
is in demo-narration-script.md.

Record this file: the ADK web UI at http://localhost:8000 with
expense_manager_agent selected, full screen, so the chat and the
uploaded receipt are both visible.

Step 1, about 1 minute. Show on screen: the ADK web UI and the
Target receipt file data/sample_receipts/target-2026-11-14.png.
Say: "Hi, I am Khagendra Khatri. This is my CS663 Part 3 expense
assistant. First I will upload a Target receipt and ask it to store
it." Then upload the file and type: "Please store this receipt."
Expected on screen: the agent stores Target, 2026-11-14, total
87.20 USD, with 5 items, and says the receipt was stored
successfully.

Step 2, about 1 minute. Show on screen: the same chat window.
Say: "Next I will ask how much I spent at one store." Then type:
"How much did I spend at Target?" Expected on screen: the agent
answers 87.20 USD for the Target receipt on 2026-11-14.

Step 3, about 1 minute. Show on screen: the same chat window.
Say: "Last, I will ask for my total for November." Then type:
"What is my total spending in November?" Expected on screen: the
agent uses get_spending_summary and answers with the total across
all stored receipts. With all 3 sample receipts stored the total
is 135.83 USD: Trader Joe's 42.18, Starbucks 6.45, and Target
87.20. The count is 3 and the average is 45.28 USD.

Close by saying: "That is the demo. The tools are tested with
9 passing tests and no LLM call, and the limits are in the README."

## Sample receipts

- Trader Joe's, 2026-11-10, 42.18 USD. 6 items.
- Starbucks, 2026-11-12, 6.45 USD. 2 items.
- Target, 2026-11-14, 87.20 USD. 5 items.

The exact values are in data/sample_receipts/expected.json. The item
prices in each receipt add up exactly to its total.

## Tests

Run the tool tests with no LLM call:

```
.venv/bin/pytest tests/test_tools.py -v
```

Result on 2026-11-17: 9 passed, 0 failed. See TESTING.md for the
exact commands and output.

Run the website tests the same way:

```
.venv/bin/pytest tests/test_website.py -v
```

See WEBSITE_TESTING.md for the exact commands and output.

## Source

Codelab: https://codelabs.developers.google.com/personal-expense-assistant-multimodal-adk
Starter repo: https://github.com/alphinside/personal-expense-assistant-adk-codelab-starter.git
Syllabus: https://borg.csueastbay.edu/~grewe/CS663/syllabus.htm, read Nov 17, 2026, for the name, date, and course header, the AI citation rule, the UNLISTED YouTube demo rule, and the 70 percent projects grading note.

Note on sources: the course outline page for Part 3 did not load
full text in the browser, so the codelab above is the source for
the Option 3 build: the agent shape, the 4 tools, the callback,
and the prompt. This local version changes only the storage and
search backend, as listed above.

## Limits

- The live agent turn was not run here yet. It needs a Gemini key.
  See TESTING.md.
- Keyword search is not vector search. It will miss receipts when
  the words do not match, for example a synonym for an item name.
- This demo assumes 1 user only, same as the codelab. There is no
  login and no per user data split.
- The sample receipts are generated images, not real store receipts.
