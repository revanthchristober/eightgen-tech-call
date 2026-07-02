from __future__ import annotations

import os
import re

from openai import OpenAI
from pydantic import BaseModel

from models import ChatAnswer, Chunk, Citation
from retrieval import retrieve

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

SYSTEM_PROMPT = (
    "You are a financial research assistant. You will be given a question "
    "and a numbered list of source passages, each tagged with a chunk id, "
    "company, period, and page number. Answer using ONLY information in "
    "those passages.\n"
    "Rules:\n"
    "- Every number (%, currency amount, bps, multiple) must be copied "
    "character-for-character from the source passage: same digits, same "
    "sign, same parentheses for negatives/losses. Never round, recompute, "
    "or paraphrase a number.\n"
    "- cited_chunk_ids must list only chunk ids you actually drew facts "
    "from, and every factual claim in the answer must trace to one of them.\n"
    "- If the passages do not contain the answer, set insufficient_data=true "
    "and the answer should state the data is not in the corpus. Do not guess."
)

# Numbers must match verbatim against source text: currency amounts,
# percentages (incl. negative/parenthesized losses), basis points, and
# multiples ("5.2x"), in that priority order (currency before bare percent
# so "$4.2 million" isn't split into two partial matches).
NUMBER_PATTERN = re.compile(
    r"[₹$]\(?-?[\d,]+(?:\.\d+)?\)?(?:\s?(?:crore|million|billion|bn|mn))?"
    r"|\d+(?:\.\d+)?\s?(?:basis points|bps)"
    r"|-?\(?\d[\d,]*(?:\.\d+)?\)?%"
    r"|\d+(?:\.\d+)?x\b"
)


class _LLMChatResponse(BaseModel):
    answer: str
    cited_chunk_ids: list[str]
    insufficient_data: bool


def _build_context(chunks: list[Chunk]) -> str:
    lines = []
    for c in chunks:
        lines.append(
            f"[{c.chunk_id}] ({c.company}, {c.period}, page {c.page}): {c.text}"
        )
    return "\n".join(lines)


def verify_numeric_fidelity(answer_text: str, chunks: list[Chunk]) -> list[str]:
    """Return numbers in answer_text that don't appear verbatim in the cited chunks."""
    source_text = "\n".join(c.text for c in chunks)
    numbers = NUMBER_PATTERN.findall(answer_text)
    return [n for n in numbers if n not in source_text]


def answer(question: str, client: OpenAI | None = None, model: str = DEFAULT_MODEL) -> ChatAnswer:
    chunks = retrieve(question)
    if not chunks:
        return ChatAnswer(
            answer="I don't have information about this in the ingested documents.",
            citations=[],
            insufficient_data=True,
        )

    client = client or OpenAI()
    completion = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nSource passages:\n{_build_context(chunks)}",
            },
        ],
        response_format=_LLMChatResponse,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Model did not return a parseable structured output")

    if parsed.insufficient_data or not parsed.cited_chunk_ids:
        return ChatAnswer(answer=parsed.answer, citations=[], insufficient_data=True)

    by_id = {c.chunk_id: c for c in chunks}
    cited_chunks = [by_id[cid] for cid in parsed.cited_chunk_ids if cid in by_id]

    unverified = verify_numeric_fidelity(parsed.answer, cited_chunks)
    if unverified:
        # Fail closed: don't surface a figure we can't verify against the
        # retrieved source text, per the no-hallucinated-numbers requirement.
        return ChatAnswer(
            answer=(
                "The generated answer contained figures that could not be "
                f"verified verbatim against the source documents ({', '.join(unverified)}) "
                "and was withheld."
            ),
            citations=[],
            insufficient_data=True,
        )

    citations = [
        Citation(doc_id=c.doc_id, page=c.page, quote=c.text) for c in cited_chunks
    ]
    return ChatAnswer(answer=parsed.answer, citations=citations, insufficient_data=False)
