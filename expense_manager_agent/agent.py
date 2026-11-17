"""Root agent for the personal expense assistant.

Backend choice:
- If GOOGLE_API_KEY is set in the environment, use Google AI Studio
  and do not force Vertex AI. This is the free key path.
- Otherwise use Vertex AI with the project and location from settings.
  That is the codelab default. It needs a Google Cloud project and
  credentials, for example from gcloud auth application-default login.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from expense_manager_agent.callbacks import modify_image_data_in_history
from expense_manager_agent.tools import (
    get_receipt_data_by_image_id,
    get_spending_summary,
    search_receipts_by_metadata_filter,
    search_relevant_receipts_by_natural_language_query,
    store_receipt_data,
)
from settings import get_settings

SETTINGS = get_settings()

_API_KEY = os.environ.get("GOOGLE_API_KEY", "").strip()
if _API_KEY:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
else:
    os.environ["GOOGLE_CLOUD_PROJECT"] = SETTINGS.GCLOUD_PROJECT_ID
    os.environ["GOOGLE_CLOUD_LOCATION"] = SETTINGS.GCLOUD_LOCATION
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

current_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(current_dir, "task_prompt.md")

with open(prompt_path, "r", encoding="utf-8") as file:
    task_prompt = file.read()

root_agent = Agent(
    name="expense_manager_agent",
    model="gemini-2.5-flash",
    description=(
        "Personal expense agent to help user track expenses, analyze receipts, and manage their financial records"
    ),
    instruction=task_prompt,
    tools=[
        store_receipt_data,
        get_receipt_data_by_image_id,
        search_receipts_by_metadata_filter,
        search_relevant_receipts_by_natural_language_query,
        get_spending_summary,
    ],
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            thinking_budget=2048,
        )
    ),
    before_model_callback=modify_image_data_in_history,
)
