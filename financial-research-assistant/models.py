from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class DocType(str, Enum):
    PRESENTATION = "presentation"
    TRANSCRIPT = "transcript"
    ANNUAL_REPORT = "annual_report"


class Document(BaseModel):
    doc_id: str
    company: str
    doc_type: DocType
    period: str  # e.g. "Q4FY24", "FY23"
    title: str


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    company: str
    period: str
    page: int
    text: str


class Citation(BaseModel):
    doc_id: str
    page: int
    quote: str


class ChatRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be empty")
        return v


class ChatAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    insufficient_data: bool = False


class ResearchRequest(BaseModel):
    brief: str

    @field_validator("brief")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("brief must not be empty")
        return v


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PARTIAL = "partial"
    DONE = "done"
    FAILED = "failed"


class SubQuestionResult(BaseModel):
    sub_question: str
    answer: Optional[ChatAnswer]
    error: Optional[str] = None


class ComparisonRow(BaseModel):
    metric: str
    company: str
    period: str
    value: str
    citation: Citation


class ResearchReport(BaseModel):
    summary: str
    comparison_table: list[ComparisonRow]
    trends: str
    risks: str
    conclusion: str
    sub_results: list[SubQuestionResult]
    dropped_unverified_rows: int = 0


class ResearchJob(BaseModel):
    job_id: str
    status: JobStatus
    brief: str
    progress: str = "queued"
    sub_questions_total: int = 0
    sub_questions_done: int = 0
    report: Optional[ResearchReport] = None
    error: Optional[str] = None
