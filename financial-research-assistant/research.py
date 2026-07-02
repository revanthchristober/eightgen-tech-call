from __future__ import annotations

import asyncio
import time
import uuid
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel

import chat
from models import (
    ChatAnswer,
    Citation,
    ComparisonRow,
    JobStatus,
    ResearchJob,
    ResearchReport,
    SubQuestionResult,
)

DEFAULT_MODEL = chat.DEFAULT_MODEL
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0


class _SubQuestionList(BaseModel):
    sub_questions: list[str]


class _ComparisonRowDraft(BaseModel):
    metric: str
    company: str
    period: str
    value: str
    cited_doc_id: str
    cited_page: int


class _ReportSynthesis(BaseModel):
    summary: str
    comparison_table: list[_ComparisonRowDraft]
    trends: str
    risks: str
    conclusion: str


DECOMPOSE_SYSTEM_PROMPT = (
    "You are a financial research planner. Given a research brief that may "
    "span multiple companies, periods, and metrics, break it into a list of "
    "concrete, independently-answerable sub-questions, one per "
    "company/metric/period combination needed. Name the company and period "
    "explicitly in each sub-question."
)

SYNTHESIS_SYSTEM_PROMPT = (
    "You are a financial research analyst writing a structured comparative "
    "report from a set of already-verified question/answer pairs, each with "
    "citations (doc_id, page, quote). Write ONLY from these -- do not "
    "introduce any company, period, or figure not present in them. For the "
    "comparison_table, every 'value' must be copied character-for-character "
    "from the quote of the chunk you cite as cited_doc_id/cited_page, and "
    "that chunk must be one of the ones provided to you above."
)


class JobStore:
    """In-memory job store. Production swap-in: Redis/Postgres row per job,
    keyed the same way, so main.py's usage doesn't change."""

    def __init__(self) -> None:
        self._jobs: dict[str, ResearchJob] = {}

    def create(self, brief: str) -> ResearchJob:
        job = ResearchJob(job_id=str(uuid.uuid4()), status=JobStatus.PENDING, brief=brief)
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[ResearchJob]:
        return self._jobs.get(job_id)

    def save(self, job: ResearchJob) -> None:
        self._jobs[job.job_id] = job


def decompose_brief(brief: str, client: OpenAI, model: str = DEFAULT_MODEL) -> list[str]:
    completion = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": DECOMPOSE_SYSTEM_PROMPT},
            {"role": "user", "content": brief},
        ],
        response_format=_SubQuestionList,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None or not parsed.sub_questions:
        raise ValueError("Model did not return sub-questions")
    return parsed.sub_questions


def _answer_with_retry(sub_question: str, client: OpenAI) -> ChatAnswer:
    last_error: Exception = RuntimeError("unreachable")
    for attempt in range(MAX_RETRIES):
        try:
            return chat.answer(sub_question, client=client)
        except Exception as exc:  # transient API/rate-limit errors
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(BASE_DELAY_SECONDS * (2 ** attempt))
    raise last_error


def _synthesize_report(
    brief: str,
    sub_results: list[SubQuestionResult],
    client: OpenAI,
    model: str = DEFAULT_MODEL,
) -> ResearchReport:
    successful = [r for r in sub_results if r.answer and not r.answer.insufficient_data]
    if not successful:
        return ResearchReport(
            summary="No verifiable data was found in the corpus for this brief.",
            comparison_table=[],
            trends="",
            risks="",
            conclusion="Insufficient data to produce a comparison.",
            sub_results=sub_results,
        )

    # Whitelist of citations already gathered from grounded, numerically
    # verified sub-answers. Synthesis may only reference these -- never
    # invent a new doc/page/figure at report-writing time.
    citation_lookup: dict[tuple[str, int], Citation] = {
        (c.doc_id, c.page): c for r in successful for c in r.answer.citations
    }

    context_lines = []
    for r in successful:
        cites = ", ".join(f"{c.doc_id} p{c.page}" for c in r.answer.citations)
        context_lines.append(f"Q: {r.sub_question}\nA: {r.answer.answer}\nCitations: {cites}")
    context = "\n\n".join(context_lines)

    completion = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": f"Research brief: {brief}\n\nVerified Q&A pairs:\n{context}"},
        ],
        response_format=_ReportSynthesis,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Model did not return a parseable report")

    comparison_table: list[ComparisonRow] = []
    dropped = 0
    for draft in parsed.comparison_table:
        cited = citation_lookup.get((draft.cited_doc_id, draft.cited_page))
        if cited is None or draft.value not in cited.quote:
            dropped += 1
            continue
        comparison_table.append(
            ComparisonRow(
                metric=draft.metric,
                company=draft.company,
                period=draft.period,
                value=draft.value,
                citation=cited,
            )
        )

    return ResearchReport(
        summary=parsed.summary,
        comparison_table=comparison_table,
        trends=parsed.trends,
        risks=parsed.risks,
        conclusion=parsed.conclusion,
        sub_results=sub_results,
        dropped_unverified_rows=dropped,
    )


async def run_research_job(
    job_id: str, store: JobStore, client: Optional[OpenAI] = None
) -> None:
    job = store.get(job_id)
    if job is None:
        return

    job.status = JobStatus.RUNNING
    job.progress = "decomposing brief"
    store.save(job)

    try:
        client = client or OpenAI()
        sub_questions = await asyncio.to_thread(decompose_brief, job.brief, client)
    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error = f"Failed to decompose brief: {exc}"
        store.save(job)
        return

    job.sub_questions_total = len(sub_questions)
    job.progress = f"answering 0/{len(sub_questions)} sub-questions"
    store.save(job)

    sub_results: list[SubQuestionResult] = []
    for i, sub_q in enumerate(sub_questions, start=1):
        try:
            ans = await asyncio.to_thread(_answer_with_retry, sub_q, client)
            sub_results.append(SubQuestionResult(sub_question=sub_q, answer=ans))
        except Exception as exc:
            sub_results.append(SubQuestionResult(sub_question=sub_q, answer=None, error=str(exc)))

        job.sub_questions_done = i
        job.progress = f"answering {i}/{len(sub_questions)} sub-questions"
        store.save(job)

    failures = [r for r in sub_results if r.error is not None]

    try:
        job.progress = "synthesizing report"
        store.save(job)
        report = await asyncio.to_thread(_synthesize_report, job.brief, sub_results, client)
    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error = f"Failed to synthesize report: {exc}"
        store.save(job)
        return

    job.report = report
    job.progress = "done"
    if not failures:
        job.status = JobStatus.DONE
    elif len(failures) < len(sub_results):
        job.status = JobStatus.PARTIAL
    else:
        job.status = JobStatus.FAILED
        job.error = "All sub-questions failed"
    store.save(job)
