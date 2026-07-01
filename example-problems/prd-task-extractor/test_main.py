from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from models import Task

client = TestClient(app)

SAMPLE_PRD = """
Product: Notification Center

Users must be able to see unread notifications in a bell icon (critical).
Users should be able to mark notifications as read.
It would be nice to have notification grouping by type.
"""


def test_extract_tasks_returns_non_empty_list():
    fake_tasks = [
        Task(
            task_name="Add unread bell icon",
            description="Show unread notifications in a bell icon",
            priority="high",
        ),
        Task(
            task_name="Mark as read",
            description="Allow users to mark notifications as read",
            priority="medium",
        ),
    ]

    with patch("main.extract_tasks", return_value=fake_tasks):
        response = client.post("/extract-tasks", content=SAMPLE_PRD.encode("utf-8"))

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0
    assert all({"task_name", "description", "priority"} <= t.keys() for t in body)


@pytest.mark.skip(
    reason="ANTHROPIC_API_KEY has no credits (400 invalid_request_error). "
    "Top up at console.anthropic.com/billing, then remove this skip."
)
def test_extract_tasks_live_call_returns_non_empty_list():
    response = client.post("/extract-tasks", content=SAMPLE_PRD.encode("utf-8"))

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0
    assert all({"task_name", "description", "priority"} <= t.keys() for t in body)
    assert all(t["priority"] in {"high", "medium", "low"} for t in body)
