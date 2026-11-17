Khagendra Khatri
Nov 17, 2026
CS663 Computer Vision

# Submission: Part 3 Option 3 Personal Expense Assistant

AI use citation: this build used Muse and Gemini assistance to write
code, tests, and docs. I checked the code, ran the tests, and I am
responsible for the result.

This file lists what is ready to submit for Part 3 Option 3, and
what is still missing. Nothing here has been submitted to Canvas
yet. Do not treat this file as a submission by itself.

## Links ready to submit

- GitHub repo (public, main, HEAD 5667f97):
  https://github.com/Khagendra01/cs663-part3-expense-assistant
- GitHub Pages website (chat layout, drag and drop):
  https://khagendra01.github.io/cs663-part3-expense-assistant/
  Checked Nov 17, 2026: HTTP 200.
- Cloud Run backend (API only, not a web page):
  https://cs663-expense-assistant-htdn76co5a-uc.a.run.app
  Checked Nov 17, 2026: GET /health returns
  {"status": "ok", "agent": "expense_manager_agent"}.
- Muse demo page (front end demo only, no live Gemini):
  https://muse.ai/s/cs663-part-3-expense-assistant-hg6zxvxxfjaxzh/ZqEgdNbgs1Q0qlBBQFlXT0PvA0-K1aiGy6ZJFsUSl8k

## Files ready to submit

From the repo, main branch:

- README.md: what it does, how to run, demo steps, limits.
- TESTING.md: tool tests, 9 passed, 0 failed, and the sample
  receipt table.
- WEBSITE_TESTING.md: website tests, 6 passed, 0 failed, and
  the local backend checks.
- DEPLOY.md: Cloud Run deploy steps and limits.
- LIVE_TEST.md: live test notes.
- demo-narration-script.md: word for word script, about 3 minutes.
- expense_manager_agent/agent.py, tools.py, callbacks.py,
  task_prompt.md: the agent, 5 tools, SQLite storage, Gemini 2.5 Flash.
- backend/main.py: FastAPI, /health, /receipts, /chat.
- frontend/app.py: Gradio, chat plus receipt upload.
- docs/index.html: the GitHub Pages website.
- data/sample_receipts/: 3 sample receipt PNGs and expected.json.
- tests/test_tools.py and tests/test_website.py.

Each file turned in here has my name, the date, and the course
name at the top. I checked all of them on Nov 17, 2026: no em
dashes in README.md, TESTING.md, WEBSITE_TESTING.md,
demo-narration-script.md, DEPLOY.md, or LIVE_TEST.md.

## Tests

- Tool tests: .venv/bin/pytest tests/test_tools.py -v
  Result Nov 17, 2026: 9 passed, 0 failed.
- Website tests: .venv/bin/pytest tests/test_website.py -v
  Result Nov 17, 2026: 6 passed, 0 failed.

## Sample receipts

- Trader Joe's, 2026-11-10, 42.18 USD, 6 items.
- Starbucks, 2026-11-12, 6.45 USD, 2 items.
- Target, 2026-11-14, 87.20 USD, 5 items.
- Total: 135.83 USD, count 3, average 45.28 USD, month 2026-11.

## Secrets check

Checked Nov 17, 2026, local folder and git tracked files:

- No .env file exists locally. No settings.yaml file exists locally.
- No key value is in any tracked file. Only .env.example and
  settings.yaml.example are tracked, and they have placeholders
  only. The export lines in the docs say your-key-here.
- data/expenses.db is not tracked. It is in .gitignore, along
  with .env and settings.yaml.
- No AI Studio key value is written in this file or in the repo.

## Known blocker: live Gemini chat does not work yet

Do not claim live Gemini works when it does not. The live
status on Nov 17, 2026 is:

- CORS fix is live on Cloud Run revision 00002. An OPTIONS
  request to /chat from https://khagendra01.github.io
  returns 200 with Access-Control-Allow-Origin for github.io.
- The first live /chat test returned 503, no Gemini key.
  The backend only checked for a local key file, not for
  Vertex AI on Cloud Run.
- Fix commit 5667f97, "Fix Gemini availability check for
  Cloud Run Vertex AI", is pushed to main, but it is NOT
  deployed. The rebuild was cancelled at my direction
  because it takes about 9 minutes.
- An AI Studio key was set on Cloud Run as GOOGLE_API_KEY,
  revision 00003, on Nov 17, 2026. Live /chat then returned
  402 RESOURCE_EXHAUSTED, prepayment credits are depleted
  for that AI Studio project. So the key is set, but its
  billing has no credits left.

To fix this, one of these is needed: a free AI Studio key
with no prepay, add prepay credits to the current AI Studio
project, or redeploy the Vertex fix 5667f97 and unset
GOOGLE_API_KEY so the service uses Vertex AI instead.

## Notes on older lines in the docs

Some lines in README.md, WEBSITE_TESTING.md, and DEPLOY.md
still say the Cloud Run deploy was not done yet, or that no
live Gemini turn was run. Those lines were true when the
files were written earlier on Nov 17, 2026. They are now
out of date. The live status above is the current one:
Cloud Run is live, /health is ok, CORS is live, and /chat
fails with 402 as described above.

## Still missing for submission

- Demo video: NOT recorded yet. The script is ready in
  demo-narration-script.md, about 3 minutes, 3 steps:
  store the Target receipt, ask Target spend, ask November
  total. After recording, upload to YouTube as UNLISTED
  and put the link in the Canvas submission.
- Live Gemini chat test: NOT passed yet, for the blocker
  above. The 3 demo turns have not been run live end to
  end against Cloud Run.
- Canvas submission itself: NOT submitted. The exact
  Canvas assignment name, due date, and required fields
  were still being read from Canvas on Nov 17, 2026.
  Submit only after the live Gemini path is fixed and
  the demo video link is ready, and after I approve the
  exact text and files to submit.
