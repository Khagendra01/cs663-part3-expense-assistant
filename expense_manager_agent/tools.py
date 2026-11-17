"""Tools for the expense manager agent.

Local version of the codelab tools. The codelab stored receipts in
Firestore and used text-embedding-004 for vector search. This version
stores receipts in a local SQLite file and uses keyword matching for
natural language search, so it runs with no billing and no cloud setup.
To swap back to Firestore, replace the SQLite helpers below with the
Firestore client from the codelab and restore the embedding call in
store_receipt_data and the vector query in
search_relevant_receipts_by_natural_language_query.
"""

import datetime
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from settings import get_settings

SETTINGS = get_settings()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _db_path() -> Path:
    path = Path(SETTINGS.DB_PATH)
    if path.is_absolute():
        return path
    return _PROJECT_ROOT / path


DB_PATH = _db_path()

INVALID_ITEMS_FORMAT_ERR = """
Invalid items format. Must be a list of dictionaries with 'name', 'price', and 'quantity' keys."""

RECEIPT_DESC_FORMAT = """
Store Name: {store_name}

Transaction Time: {transaction_time}

Total Amount: {total_amount}

Currency: {currency}

Purchased Items:

{purchased_items}

Receipt Image ID: {receipt_id}

"""


def sanitize_image_id(image_id: str) -> str:
    """Sanitize image ID by removing any leading/trailing whitespace."""
    if image_id.startswith("[IMAGE-"):
        image_id = image_id.split("ID ")[1].split("]")[0]
    return image_id.strip()


def _parse_iso(value: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def _connect() -> sqlite3.Connection:
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS receipts (
            receipt_id TEXT PRIMARY KEY,
            store_name TEXT NOT NULL,
            transaction_time TEXT NOT NULL,
            total_amount REAL NOT NULL,
            currency TEXT NOT NULL,
            items_json TEXT NOT NULL
        )"""
    )
    conn.commit()
    return conn


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "receipt_id": row["receipt_id"],
        "store_name": row["store_name"],
        "transaction_time": row["transaction_time"],
        "total_amount": float(row["total_amount"]),
        "currency": row["currency"],
        "purchased_items": json.loads(row["items_json"]),
    }


def _all_receipts() -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM receipts ORDER BY transaction_time").fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        conn.close()


def _format_receipt(data: Dict[str, Any]) -> str:
    return RECEIPT_DESC_FORMAT.format(**data)


def store_receipt_data(
    image_id: str,
    store_name: str,
    transaction_time: str,
    total_amount: float,
    purchased_items: List[Dict[str, Any]],
    currency: str = "USD",
) -> str:
    """
    Store receipt data in the database.

    Args:
        image_id (str): The unique identifier of the image. For example IMAGE-POSITION 0-ID 12345,
            the ID of the image is 12345.
        store_name (str): The name of the store.
        transaction_time (str): The time of purchase, in ISO format ("YYYY-MM-DDTHH:MM:SS.ssssssZ").
        total_amount (float): The total amount spent.
        purchased_items (List[Dict[str, Any]]): A list of items purchased with their prices. Each item must have:
            - name (str): The name of the item.
            - price (float): The price of the item.
            - quantity (int, optional): The quantity of the item. Defaults to 1 if not provided.
        currency (str, optional): The currency of the transaction, can be derived from the store location.
            If unsure, default is "USD". The codelab default was "IDR".

    Returns:
        str: A success message with the receipt ID.

    Raises:
        Exception: If the operation failed or input is invalid.
    """
    try:
        image_id = sanitize_image_id(image_id)

        doc = get_receipt_data_by_image_id(image_id)
        if doc:
            return f"Receipt with ID {image_id} already exists"

        if not isinstance(transaction_time, str):
            raise ValueError(
                "Invalid transaction time: must be a string in ISO format 'YYYY-MM-DDTHH:MM:SS.ssssssZ'"
            )
        try:
            _parse_iso(transaction_time)
        except ValueError:
            raise ValueError(
                "Invalid transaction time format. Must be in ISO format 'YYYY-MM-DDTHH:MM:SS.ssssssZ'"
            )

        if not isinstance(purchased_items, list):
            raise ValueError(INVALID_ITEMS_FORMAT_ERR)
        items = []
        for _item in purchased_items:
            if (
                not isinstance(_item, dict)
                or "name" not in _item
                or "price" not in _item
            ):
                raise ValueError(INVALID_ITEMS_FORMAT_ERR)
            item = dict(_item)
            if "quantity" not in item:
                item["quantity"] = 1
            items.append(item)

        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO receipts (receipt_id, store_name, transaction_time, total_amount, currency, items_json)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    image_id,
                    store_name,
                    transaction_time,
                    float(total_amount),
                    currency,
                    json.dumps(items),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return f"Receipt stored successfully with ID: {image_id}"
    except Exception as e:
        raise Exception(f"Failed to store receipt: {str(e)}")


def get_receipt_data_by_image_id(image_id: str) -> Dict[str, Any]:
    """
    Retrieve receipt data from the database using the image_id.

    Args:
        image_id (str): The unique identifier of the receipt image. For example, if the placeholder is
            [IMAGE-ID 12345], the ID to use is 12345.

    Returns:
        Dict[str, Any]: A dictionary containing the receipt data with the following keys:
            - receipt_id (str): The unique identifier of the receipt image.
            - store_name (str): The name of the store.
            - transaction_time (str): The time of purchase in UTC.
            - total_amount (float): The total amount spent.
            - currency (str): The currency of the transaction.
            - purchased_items (List[Dict[str, Any]]): List of items purchased with their details.
        Returns an empty dictionary if no receipt is found.
    """
    image_id = sanitize_image_id(image_id)
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM receipts WHERE receipt_id = ? LIMIT 1", (image_id,)
        ).fetchone()
        if row is None:
            return {}
        return _row_to_dict(row)
    finally:
        conn.close()


def search_receipts_by_metadata_filter(
    start_time: str,
    end_time: str,
    min_total_amount: float = -1.0,
    max_total_amount: float = -1.0,
) -> str:
    """
    Filter receipts by metadata within a specific time range and optionally by amount.

    Args:
        start_time (str): The start datetime for the filter (in ISO format, e.g. 'YYYY-MM-DDTHH:MM:SS.ssssssZ').
        end_time (str): The end datetime for the filter (in ISO format, e.g. 'YYYY-MM-DDTHH:MM:SS.ssssssZ').
        min_total_amount (float): The minimum total amount for the filter (inclusive). Defaults to -1.
        max_total_amount (float): The maximum total amount for the filter (inclusive). Defaults to -1.

    Returns:
        str: A string containing the list of receipt data matching all applied filters.

    Raises:
        Exception: If the search failed or input is invalid.
    """
    try:
        if not isinstance(start_time, str) or not isinstance(end_time, str):
            raise ValueError("start_time and end_time must be strings in ISO format")
        try:
            start = _parse_iso(start_time)
            end = _parse_iso(end_time)
        except ValueError:
            raise ValueError("start_time and end_time must be strings in ISO format")

        search_result_description = "Search by Metadata Results:\n"
        for data in _all_receipts():
            when = _parse_iso(data["transaction_time"])
            if when < start or when > end:
                continue
            if min_total_amount != -1 and data["total_amount"] < min_total_amount:
                continue
            if max_total_amount != -1 and data["total_amount"] > max_total_amount:
                continue
            search_result_description += f"\n{_format_receipt(data)}"
        return search_result_description
    except Exception as e:
        raise Exception(f"Error filtering receipts: {str(e)}")


def search_relevant_receipts_by_natural_language_query(
    query_text: str, limit: int = 5
) -> str:
    """
    Search for receipts with content most similar to the query using keyword matching.

    This is the local replacement for the codelab vector search. The codelab
    embedded the query with text-embedding-004 and ran a Firestore vector
    search. Here we score each receipt by keyword overlap with the store
    name, the item names, and the full receipt text. No embedding call is
    needed, so this works offline.

    This tool can be use for user query that is difficult to translate into metadata filters.
    Such as store name or item name which sensitive to string matching.
    Use this tool if you cannot utilize the search by metadata filter tool.

    Args:
        query_text (str): The search text (e.g., "coffee", "dinner", "groceries").
        limit (int, optional): Maximum number of results to return (default: 5).

    Returns:
        str: A string containing the list of contextually relevant receipt data.

    Raises:
        Exception: If the search failed or input is invalid.
    """
    try:
        tokens = [t for t in re.findall(r"[a-z0-9]+", query_text.lower()) if len(t) > 1]
        scored = []
        for data in _all_receipts():
            store = data["store_name"].lower()
            items_text = " ".join(
                str(item.get("name", "")).lower() for item in data["purchased_items"]
            )
            full_text = _format_receipt(data).lower()
            score = 0
            for token in tokens:
                if token in store:
                    score += 3
                if token in items_text:
                    score += 2
                if token in full_text:
                    score += 1
            if score > 0:
                scored.append((score, data))
        scored.sort(key=lambda pair: pair[0], reverse=True)

        search_result_description = "Search by Contextual Relevance Results:\n"
        for _, data in scored[:limit]:
            search_result_description += f"\n{_format_receipt(data)}"
        if not scored:
            search_result_description += "\nNo receipts matched the query."
        return search_result_description
    except Exception as e:
        raise Exception(f"Error searching receipts: {str(e)}")


def get_spending_summary(start_time: str = "", end_time: str = "") -> str:
    """
    Summarize spending across stored receipts.

    Args:
        start_time (str, optional): Start datetime in ISO format. Empty means no lower bound.
        end_time (str, optional): End datetime in ISO format. Empty means no upper bound.

    Returns:
        str: Total spent, receipt count, average per receipt, totals by store,
            and totals by month (YYYY-MM).
    """
    try:
        start = _parse_iso(start_time) if start_time else None
        end = _parse_iso(end_time) if end_time else None
    except ValueError:
        raise Exception("Error summarizing spending: start_time and end_time must be strings in ISO format")

    receipts = []
    for data in _all_receipts():
        when = _parse_iso(data["transaction_time"])
        if start is not None and when < start:
            continue
        if end is not None and when > end:
            continue
        receipts.append(data)

    total = sum(data["total_amount"] for data in receipts)
    count = len(receipts)
    average = total / count if count else 0.0
    currency = receipts[0]["currency"] if receipts else SETTINGS.CURRENCY

    by_store: Dict[str, float] = {}
    by_month: Dict[str, float] = {}
    for data in receipts:
        by_store[data["store_name"]] = by_store.get(data["store_name"], 0.0) + data["total_amount"]
        month = data["transaction_time"][:7]
        by_month[month] = by_month.get(month, 0.0) + data["total_amount"]

    lines = [
        "Spending Summary:",
        f"Total spent: {total:.2f} {currency}",
        f"Receipt count: {count}",
        f"Average per receipt: {average:.2f} {currency}",
        "Totals by store:",
    ]
    for store in sorted(by_store):
        lines.append(f"  {store}: {by_store[store]:.2f} {currency}")
    lines.append("Totals by month:")
    for month in sorted(by_month):
        lines.append(f"  {month}: {by_month[month]:.2f} {currency}")
    return "\n".join(lines) + "\n"
