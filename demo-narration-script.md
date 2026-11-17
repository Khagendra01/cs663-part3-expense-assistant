Khagendra Khatri
Nov 17, 2026
CS663 Computer Vision

# Demo narration script: Part 3 Option 3 Personal Expense Assistant

AI use citation: this build used Muse and Gemini assistance to write
code, tests, and docs. I checked the code, ran the tests, and I am
responsible for the result.

## How to record

Record a short narrated screen recording, about 3 minutes, in plain
student voice. Record the ADK web UI at http://localhost:8000 with
expense_manager_agent selected, full screen, so the chat and the
uploaded receipt are both visible. Start the agent first with
`.venv/bin/adk web`, then store the 3 sample receipts in the tools
test data before you record, or store them live in step 1 and the
other 2 before step 3. For the totals in step 3 to match, all 3
sample receipts must be stored: Trader Joe's 42.18, Starbucks 6.45,
and Target 87.20, total 135.83 USD.

Upload the finished video to YouTube as UNLISTED, per the syllabus.
Do not set it to Public.

## Script

### Step 1, about 1 minute: upload a receipt and save it

Show on screen: the ADK web UI and the Target receipt file
data/sample_receipts/target-2026-11-14.png.

Say this:

"Hi, I am Khagendra Khatri. This is my CS663 Part 3 expense
assistant. It is built with Google ADK and Gemini 2.5 Flash.
First I will upload a Target receipt and ask it to store it."

Then upload the file and type: "Please store this receipt."

Say this after the answer appears:

"It stored the Target receipt from November 14, total 87.20
dollars, with 5 items."

### Step 2, about 1 minute: ask how much spent at one store

Show on screen: the same chat window.

Say this:

"Next I will ask how much I spent at one store."

Then type: "How much did I spend at Target?"

Say this after the answer appears:

"It says 87.20 dollars at Target. That matches the receipt."

### Step 3, about 1 minute: ask total for November

Show on screen: the same chat window.

Say this:

"Last, I will ask for my total for November."

Then type: "What is my total spending in November?"

Say this after the answer appears:

"The total is 135.83 dollars across 3 receipts. Trader Joe's
is 42.18, Starbucks is 6.45, and Target is 87.20. The average
is 45.28 dollars per receipt."

Close with this:

"That is the demo. The tools are tested with 9 passing tests
and no LLM call, and the limits are in the README. Thank you."

## What to check before you record

- The ADK web UI loads and expense_manager_agent is selected.
- A Gemini key is set, either GOOGLE_API_KEY for AI Studio or
  Vertex AI credentials for the cs663-dog-training project.
- The 3 sample receipts are stored, so the step 3 total is 135.83.
- The screen is full screen and the chat text is easy to read.
