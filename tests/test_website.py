"""Tests for the website demo: FastAPI backend and Gradio frontend.

No Gemini key is needed. The /chat tests check the no key path
returns a clear 503 instead of crashing. The /health and /receipts
tests check the server works with no key at all.
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def no_gemini(monkeypatch, tmp_path):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "agent": "expense_manager_agent"}


def test_receipts_shape(client):
    resp = client.get("/receipts")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["count"], int)
    assert isinstance(body["receipts"], list)
    for item in body["receipts"]:
        assert "store_name" in item
        assert "total_amount" in item


def test_chat_no_key_returns_503(client, no_gemini):
    resp = client.post("/chat", json={"message": "How much did I spend at Target?"})
    assert resp.status_code == 503
    assert "No Gemini key is set" in resp.json()["detail"]


def test_chat_no_key_with_image_returns_503(client, no_gemini):
    resp = client.post(
        "/chat",
        json={
            "message": "Please store this receipt",
            "image_base64": "iVBORw0KGgo=",
            "image_filename": "receipt.png",
        },
    )
    assert resp.status_code == 503
    assert "No Gemini key is set" in resp.json()["detail"]


def test_chat_empty_message_returns_400(client, no_gemini):
    resp = client.post("/chat", json={"message": "   "})
    assert resp.status_code == 400


def test_frontend_builds():
    # Import frontend.app first: it cleans the bracketed NO_PROXY
    # entries before gradio is imported, see tests/conftest.py.
    from frontend.app import EXAMPLE_PROMPTS, build_demo

    import gradio as gr

    assert len(EXAMPLE_PROMPTS) == 3
    assert "Target" in EXAMPLE_PROMPTS[1]
    assert "November" in EXAMPLE_PROMPTS[2]
    demo = build_demo()
    assert isinstance(demo, gr.Blocks)
