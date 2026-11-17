"""Callbacks for the expense manager agent.

Adapted from the codelab. The codelab kept image data in the last 3 user
messages. This version keeps only the most recent image, which saves
more tokens and still leaves the image id placeholder in older turns
so the agent can fetch a stored receipt with get_receipt_data_by_image_id.
"""

import hashlib

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.genai import types


def modify_image_data_in_history(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> None:
    # We will only keep image data in the most recent user message.
    user_message_count = 0

    for content in reversed(llm_request.contents):
        if not content.parts:
            continue
        first = content.parts[0]
        if (content.role == "user") and (
            first.function_response is None
            and first.function_call is None
        ):
            user_message_count += 1
            modified_content_parts = []

            for idx, part in enumerate(content.parts):
                if part.inline_data is None:
                    modified_content_parts.append(part)
                    continue
                if (
                    (idx + 1 >= len(content.parts))
                    or (content.parts[idx + 1].text is None)
                    or (not content.parts[idx + 1].text.startswith("[IMAGE-ID "))
                ):
                    image_data = part.inline_data.data
                    hasher = hashlib.sha256(image_data)
                    image_hash_id = hasher.hexdigest()[:12]
                    placeholder = f"[IMAGE-ID {image_hash_id}]"
                    # Only keep image data in the most recent user message.
                    if user_message_count <= 1:
                        modified_content_parts.append(part)
                    modified_content_parts.append(types.Part(text=placeholder))
                else:
                    # Only keep image data in the most recent user message.
                    if user_message_count <= 1:
                        modified_content_parts.append(part)

            content.parts = modified_content_parts
