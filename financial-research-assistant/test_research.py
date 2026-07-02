import asyncio
from unittest.mock import patch

import chat
import research
from models import ChatAnswer, Citation, JobStatus, SubQuestionResult
from research import JobStore, _ComparisonRowDraft, _ReportSynthesis, _synthesize_report


def _sub_result(company: str, metric_answer: str, doc_id: str, page: int, quote: str) -> SubQuestionResult:
    return SubQuestionResult(
        sub_question=f"What was {company}'s metric?",
        answer=ChatAnswer(
            answer=metric_answer,
            citations=[Citation(doc_id=doc_id, page=page, quote=quote)],
            insufficient_data=False,
        ),
    )


class _FakeCompletions:
    def __init__(self, parsed_output):
        self._parsed_output = parsed_output

    def parse(self, **kwargs):
        message = type("Message", (), {"parsed": self._parsed_output})()
        choice = type("Choice", (), {"message": message})()
        return type("Completion", (), {"choices": [choice]})()


class _FakeChat:
    def __init__(self, parsed_output):
        self.completions = _FakeCompletions(parsed_output)


class _FakeClient:
    def __init__(self, parsed_output):
        self.chat = _FakeChat(parsed_output)


def test_synthesize_report_drops_row_citing_unlisted_chunk():
    sub_results = [
        _sub_result("Northbridge Bank", "NIM was 3.42%.", "nb-transcript-q4fy24", 1, "NIM was 3.42% in Q4FY24."),
    ]
    fake_report = _ReportSynthesis(
        summary="Comparison summary.",
        comparison_table=[
            _ComparisonRowDraft(
                metric="NIM", company="Northbridge Bank", period="Q4FY24",
                value="3.42%", cited_doc_id="some-other-doc-not-provided", cited_page=99,
            )
        ],
        trends="t", risks="r", conclusion="c",
    )
    report = _synthesize_report("brief", sub_results, _FakeClient(fake_report))
    assert report.comparison_table == []
    assert report.dropped_unverified_rows == 1


def test_synthesize_report_drops_row_with_non_verbatim_value():
    sub_results = [
        _sub_result("Northbridge Bank", "NIM was 3.42%.", "nb-transcript-q4fy24", 1, "NIM was 3.42% in Q4FY24."),
    ]
    fake_report = _ReportSynthesis(
        summary="s",
        comparison_table=[
            _ComparisonRowDraft(
                metric="NIM", company="Northbridge Bank", period="Q4FY24",
                value="3.4%",  # rounded -- not verbatim in the cited quote
                cited_doc_id="nb-transcript-q4fy24", cited_page=1,
            )
        ],
        trends="t", risks="r", conclusion="c",
    )
    report = _synthesize_report("brief", sub_results, _FakeClient(fake_report))
    assert report.comparison_table == []
    assert report.dropped_unverified_rows == 1


def test_synthesize_report_keeps_row_with_valid_whitelisted_citation():
    sub_results = [
        _sub_result("Northbridge Bank", "NIM was 3.42%.", "nb-transcript-q4fy24", 1, "NIM was 3.42% in Q4FY24."),
    ]
    fake_report = _ReportSynthesis(
        summary="s",
        comparison_table=[
            _ComparisonRowDraft(
                metric="NIM", company="Northbridge Bank", period="Q4FY24",
                value="3.42%", cited_doc_id="nb-transcript-q4fy24", cited_page=1,
            )
        ],
        trends="t", risks="r", conclusion="c",
    )
    report = _synthesize_report("brief", sub_results, _FakeClient(fake_report))
    assert len(report.comparison_table) == 1
    assert report.dropped_unverified_rows == 0


def test_run_research_job_survives_one_failed_sub_question_and_marks_partial():
    store = JobStore()
    job = store.create("Compare Northbridge Bank and Solstice Retail")

    good_answer = ChatAnswer(
        answer="NIM was 3.42%.",
        citations=[Citation(doc_id="nb-transcript-q4fy24", page=1, quote="NIM was 3.42% in Q4FY24.")],
        insufficient_data=False,
    )
    fake_report = _ReportSynthesis(
        summary="s", comparison_table=[], trends="t", risks="r", conclusion="c",
    )

    with patch("research.decompose_brief", return_value=["Q about A", "Q about B"]), \
         patch("research.time.sleep", return_value=None), \
         patch.object(chat, "answer", side_effect=[good_answer, RuntimeError("rate limited"), RuntimeError("rate limited"), RuntimeError("rate limited")]), \
         patch("research._synthesize_report", return_value=fake_report):
        asyncio.run(research.run_research_job(job.job_id, store, client=_FakeClient(None)))

    final = store.get(job.job_id)
    assert final.status == JobStatus.PARTIAL
    assert final.sub_questions_done == 2
    assert final.report is not None
