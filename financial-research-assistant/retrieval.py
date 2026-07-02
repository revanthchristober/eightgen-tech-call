from __future__ import annotations

import re
from collections import Counter

from corpus import get_chunks
from models import Chunk

# Scope cut: lexical (term-overlap) retrieval instead of embeddings — keeps
# the demo dependency-free (stdlib only) and works well here because
# financial terms/company names are distinctive. Production swap-in would be
# an embedding model + vector index behind the same retrieve() signature;
# callers wouldn't change.

COMPANY_ALIASES: dict[str, str] = {
    "tata consultancy services": "TCS",
    "tata consultancy": "TCS",
    "tcs": "TCS",
    "hdfc bank": "HDFC Bank",
    "hdfc": "HDFC Bank",
    "reliance industries": "Reliance Industries",
    "reliance": "Reliance Industries",
    "ril": "Reliance Industries",
}

PERIOD_PATTERN = re.compile(r"\bQ[1-4]FY\d{2}\b|\bFY\d{2}\b", re.IGNORECASE)
_STOPWORDS = {
    "the", "a", "an", "of", "in", "for", "was", "were", "is", "are", "and",
    "or", "to", "how", "what", "did", "vs", "versus", "compare", "with",
    "on", "by", "its", "it", "did", "move", "last", "this",
}


def extract_companies(question: str) -> list[str]:
    q_lower = question.lower()
    found: set[str] = set()
    for alias, canonical in COMPANY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", q_lower):
            found.add(canonical)
    return sorted(found)


def extract_periods(question: str) -> list[str]:
    return sorted({m.group(0).upper() for m in PERIOD_PATTERN.finditer(question)})


def _tokenize(text: str) -> list[str]:
    # len(t) > 1 drops single-character debris from contractions/possessives
    # ("TCS's" -> "tcs", "s"; "don't" -> "don", "t") -- those fragments carry
    # no topical signal but, left in, spuriously match any other chunk that
    # happens to contain an unrelated possessive.
    return [
        t for t in re.findall(r"[a-z0-9]+", text.lower())
        if t not in _STOPWORDS and len(t) > 1
    ]


_ALIAS_TOKENS = {tok for alias in COMPANY_ALIASES for tok in _tokenize(alias)}


def _score(query_tokens: Counter, chunk: Chunk) -> int:
    chunk_tokens = Counter(_tokenize(chunk.text))
    return sum(min(count, chunk_tokens[tok]) for tok, count in query_tokens.items())


def retrieve(question: str, k: int = 4) -> list[Chunk]:
    companies = extract_companies(question)
    periods = extract_periods(question)

    candidates = get_chunks()
    if companies:
        candidates = [c for c in candidates if c.company in companies]

    # Company match is already enforced by the candidate filter above; strip
    # alias tokens here so a question merely *naming* the company (which also
    # appears in every chunk's boilerplate title) doesn't itself count as
    # topical relevance and mask an off-corpus question.
    query_tokens = Counter(
        tok for tok in _tokenize(question) if tok not in _ALIAS_TOKENS
    )

    def sort_key(chunk: Chunk) -> tuple[int, int]:
        period_match = 1 if periods and chunk.period in periods else 0
        return (period_match, _score(query_tokens, chunk))

    ranked = sorted(candidates, key=sort_key, reverse=True)
    # Only return chunks with a real signal (company/period match or lexical
    # overlap). Returning low-signal chunks as filler risks the LLM
    # synthesizing an answer from irrelevant context instead of saying
    # "not in the corpus."
    return [c for c in ranked if sort_key(c) > (0, 0)][:k]
