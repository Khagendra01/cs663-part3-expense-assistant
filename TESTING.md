Khagendra Khatri
Nov 17, 2026
CS663 Computer Vision

# Testing: Part 3 Option 3 Personal Expense Assistant

AI use citation: this build used Muse and Gemini assistance to write
code, tests, and docs. I checked the code, ran the tests, and I am
responsible for the result.

## Commands run

All commands were run from the project folder
part3-expense-assistant on Nov 17, 2026.

Install:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Result: pip exit 0. Installed google-adk 1.18.0, pydantic 2.14.3,
pydantic-settings 2.16.3, Pillow 13.0.0, pytest 9.2.0, PyYAML 6.0.3.

Agent import check:

```
.venv/bin/python -c "import expense_manager_agent.agent as a; print(a.root_agent.name, a.root_agent.model)"
```

Result: pass. Agent name expense_manager_agent, model
gemini-2.5-flash, 5 tools, planner BuiltInPlanner, callback
modify_image_data_in_history. One harmless warning appears from
google-adk itself about a deprecated vertexai rag module. It does
not stop the import.

Tool tests:

```
.venv/bin/pytest tests/test_tools.py -v
```

Result: 9 passed, 0 failed, in 7.44 seconds. The 2 warnings in
the output are from google-adk and pydantic deprecations, not
from this code.

Tests and what each covers:

1. test_store_then_get_by_id: pass. Store then get returns the
   same store, total, currency, and quantity default 1. A
   [IMAGE-ID ...] placeholder id also works. A missing id
   returns an empty dict.
2. test_duplicate_rejected: pass. Storing Starbucks a second
   time returns "already exists".
3. test_invalid_time_rejected: pass. A bad transaction time
   raises "Failed to store receipt".
4. test_invalid_items_rejected: pass. An item with no price,
   and items that are not a list, both raise
   "Failed to store receipt".
5. test_metadata_filter_by_date: pass. Nov 11 to Nov 13 returns
   only Starbucks, not Trader Joe's or Target.
6. test_metadata_filter_by_amount_range: pass. Amount 80 to 100
   returns only Target.
7. test_keyword_search_finds_starbucks: pass. Query "Starbucks"
   returns the Starbucks receipt, total 6.45.
8. test_keyword_search_finds_coffee: pass. Query "coffee"
   returns Starbucks and Trader Joe's.
9. test_spending_summary_totals_135_83: pass. Total 135.83 USD,
   count 3, average 45.28 USD, by store Trader Joe's 42.18,
   Starbucks 6.45, Target 87.20, by month 2026-11 135.83.

## Sample receipts: expected vs actual

Expected values are in data/sample_receipts/expected.json. Actual
values below come from storing all 3 with store_receipt_data and
reading them back with get_receipt_data_by_image_id.

| Receipt | Expected total | Actual total | Expected items | Actual items | Items sum | Match |
| --- | --- | --- | --- | --- | --- | --- |
| Trader Joe's, 2026-11-10 | 42.18 USD | 42.18 USD | 6 | 6 | 42.18 | yes |
| Starbucks, 2026-11-12 | 6.45 USD | 6.45 USD | 2 | 2 | 6.45 | yes |
| Target, 2026-11-14 | 87.20 USD | 87.20 USD | 5 | 5 | 87.20 | yes |

Spending summary actual output:

```
Total spent: 135.83 USD
Receipt count: 3
Average per receipt: 45.28 USD
Totals by store:
  Starbucks: 6.45 USD
  Target: 87.20 USD
  Trader Joe's: 42.18 USD
Totals by month:
  2026-11: 135.83 USD
```

Receipt images checked by eye: Trader Joe's 640x720, Starbucks
640x512, Target 640x668. Each shows the store name, the date,
the item lines with prices, and the total. One fix was made
during testing: the first images cut off the total line at the
bottom, so the image height formula in
scripts/generate_sample_receipts.py was changed from
260 + items * 52 to 408 + items * 52 and the images were
regenerated. The Target image was rechecked after the fix and
the TOTAL $87.20 USD line is fully visible.

## Live LLM turn: not run here

No live Gemini turn was run here. The environment had no
GOOGLE_API_KEY set, no GOOGLE_APPLICATION_CREDENTIALS, and no
application default credentials file. No key was invented and
none was asked for.

To run the live demo, set a free AI Studio key first:

```
export GOOGLE_API_KEY=your-key-here
.venv/bin/adk web
```

Then upload a sample receipt in the ADK web UI and run the 3
demo turns in the README. Or use Vertex AI with the project
cs663-dog-training in us-central1 after
gcloud auth application-default login.
