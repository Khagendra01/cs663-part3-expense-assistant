"""Tests for the expense tools. No LLM call is needed.

Each test uses a fresh temp SQLite file so tests never touch the real
data/expenses.db file.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import expense_manager_agent.tools as tools


def _load_expected():
    path = Path(__file__).resolve().parent.parent / "data" / "sample_receipts" / "expected.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture()
def seeded_db(tmp_path, monkeypatch):
    db_path = tmp_path / "expenses.db"
    monkeypatch.setattr(tools, "DB_PATH", db_path)
    for receipt in _load_expected():
        result = tools.store_receipt_data(
            image_id=receipt["receipt_id"],
            store_name=receipt["store_name"],
            transaction_time=receipt["transaction_time"],
            total_amount=receipt["total_amount"],
            purchased_items=receipt["items"],
            currency=receipt["currency"],
        )
        assert "stored successfully" in result
    return db_path


def test_store_then_get_by_id(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "DB_PATH", tmp_path / "expenses.db")
    result = tools.store_receipt_data(
        image_id="test-001",
        store_name="Trader Joe's",
        transaction_time="2026-11-10T14:32:00.000000Z",
        total_amount=42.18,
        purchased_items=[{"name": "Coffee Beans", "price": 10.93}],
        currency="USD",
    )
    assert "stored successfully" in result
    assert "test-001" in result
    got = tools.get_receipt_data_by_image_id("test-001")
    assert got["store_name"] == "Trader Joe's"
    assert got["total_amount"] == 42.18
    assert got["currency"] == "USD"
    assert got["purchased_items"][0]["quantity"] == 1
    assert tools.get_receipt_data_by_image_id("[IMAGE-ID test-001]")["store_name"] == "Trader Joe's"
    assert tools.get_receipt_data_by_image_id("missing-id") == {}


def test_duplicate_rejected(seeded_db):
    result = tools.store_receipt_data(
        image_id="starbucks-20261112",
        store_name="Starbucks",
        transaction_time="2026-11-12T09:15:00.000000Z",
        total_amount=6.45,
        purchased_items=[{"name": "Grande Pike Place Coffee", "price": 3.45}],
        currency="USD",
    )
    assert "already exists" in result


def test_invalid_time_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "DB_PATH", tmp_path / "expenses.db")
    with pytest.raises(Exception, match="Failed to store receipt"):
        tools.store_receipt_data(
            image_id="bad-time-001",
            store_name="Target",
            transaction_time="not-a-date",
            total_amount=10.00,
            purchased_items=[{"name": "Notebook", "price": 10.00}],
            currency="USD",
        )


def test_invalid_items_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "DB_PATH", tmp_path / "expenses.db")
    with pytest.raises(Exception, match="Failed to store receipt"):
        tools.store_receipt_data(
            image_id="bad-items-001",
            store_name="Target",
            transaction_time="2026-11-14T18:05:00.000000Z",
            total_amount=10.00,
            purchased_items=[{"name": "Notebook"}],
            currency="USD",
        )
    with pytest.raises(Exception, match="Failed to store receipt"):
        tools.store_receipt_data(
            image_id="bad-items-002",
            store_name="Target",
            transaction_time="2026-11-14T18:05:00.000000Z",
            total_amount=10.00,
            purchased_items="not-a-list",
            currency="USD",
        )


def test_metadata_filter_by_date(seeded_db):
    result = tools.search_receipts_by_metadata_filter(
        start_time="2026-11-11T00:00:00.000000Z",
        end_time="2026-11-13T23:59:59.000000Z",
    )
    assert "Starbucks" in result
    assert "Trader Joe's" not in result
    assert "Target" not in result


def test_metadata_filter_by_amount_range(seeded_db):
    result = tools.search_receipts_by_metadata_filter(
        start_time="2026-11-01T00:00:00.000000Z",
        end_time="2026-11-30T23:59:59.000000Z",
        min_total_amount=80.0,
        max_total_amount=100.0,
    )
    assert "Target" in result
    assert "Starbucks" not in result
    assert "Trader Joe's" not in result


def test_keyword_search_finds_starbucks(seeded_db):
    result = tools.search_relevant_receipts_by_natural_language_query("Starbucks")
    assert "Starbucks" in result
    assert "6.45" in result


def test_keyword_search_finds_coffee(seeded_db):
    result = tools.search_relevant_receipts_by_natural_language_query("coffee")
    assert "Starbucks" in result
    assert "Trader Joe's" in result


def test_spending_summary_totals_135_83(seeded_db):
    result = tools.get_spending_summary()
    assert "Total spent: 135.83 USD" in result
    assert "Receipt count: 3" in result
    assert "Average per receipt: 45.28 USD" in result
    assert "Trader Joe's: 42.18 USD" in result
    assert "Starbucks: 6.45 USD" in result
    assert "Target: 87.20 USD" in result
    assert "2026-11: 135.83 USD" in result
