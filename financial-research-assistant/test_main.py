import time
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from models import ChatAnswer, Citation, JobStatus

client = TestClient(app)


def test_chat_endpoint_returns_grounded_answer_with_citations():
    fake_answer = ChatAnswer(
        answer="TCS's Q2 FY26 operating margin was 25.2%, up 70 basis points sequentially.",
        citations=[Citation(doc_id="tcs-transcript-q2fy26", page=6, quote="...")],
        insufficient_data=False,
    )
    with patch("chat.OpenAI"), patch("main.chat.answer", return_value=fake_answer):
        response = client.post("/chat", json={"question": "What was TCS's operating margin in Q2FY26?"})

    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_data"] is False
    assert body["citations"][0]["doc_id"] == "tcs-transcript-q2fy26"
    assert body["citations"][0]["page"] == 6


def test_chat_endpoint_rejects_empty_question():
    response = client.post("/chat", json={"question": "   "})
    assert response.status_code == 422


def test_research_endpoint_returns_job_id_immediately_then_pollable():
    terminal = {JobStatus.DONE.value, JobStatus.PARTIAL.value, JobStatus.FAILED.value}
    # A fresh, unscoped TestClient call tears down its event-loop portal after
    # each request, which would orphan the asyncio.create_task background job
    # before it progresses. Keep one client alive across post + polls instead.
    with TestClient(app) as c, \
         patch("research.OpenAI"), \
         patch("research.decompose_brief", return_value=["Q1"]), \
         patch(
             "chat.answer",
             return_value=ChatAnswer(answer="a", citations=[], insufficient_data=True),
         ):
        create_response = c.post(
            "/research", json={"brief": "Compare TCS and HDFC Bank"}
        )
        assert create_response.status_code == 202
        job_id = create_response.json()["job_id"]

        for _ in range(50):
            poll_response = c.get(f"/research/{job_id}")
            assert poll_response.status_code == 200
            if poll_response.json()["status"] in terminal:
                break
            time.sleep(0.05)

    final = poll_response.json()
    assert final["status"] in terminal
    assert final["report"] is not None


def test_research_poll_returns_404_for_unknown_job():
    response = client.get("/research/does-not-exist")
    assert response.status_code == 404
