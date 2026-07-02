from __future__ import annotations

import json
from pathlib import Path

from models import Chunk, DocType, Document

# Real corpus: page-level text extracted from real, publicly filed earnings
# call transcripts (TCS, HDFC Bank, Reliance Industries — Q2 FY26), fetched
# from company IR sites / BSE-NSE regulatory filing archives and parsed into
# per-page chunks in data/real_corpus.json. Page numbers for TCS and
# Reliance are the PDF's own printed page numbers (embedded running
# footers); HDFC Bank's are sequential section indices reconstructed from
# its repeated page header, since that extraction didn't carry literal page
# numbers.

_DATA_PATH = Path(__file__).parent / "data" / "real_corpus.json"
_DOC_TYPE_MAP = {
    "transcript": DocType.TRANSCRIPT,
    "presentation": DocType.PRESENTATION,
    "annual_report": DocType.ANNUAL_REPORT,
}

_raw_documents = json.loads(_DATA_PATH.read_text())

COMPANIES = sorted({d["company"] for d in _raw_documents})

DOCUMENTS = [
    Document(
        doc_id=d["doc_id"],
        company=d["company"],
        doc_type=_DOC_TYPE_MAP[d["doc_type"]],
        period=d["period"],
        title=d["title"],
    )
    for d in _raw_documents
]

CHUNKS = [
    Chunk(
        chunk_id=f"{d['doc_id']}-p{page}",
        doc_id=d["doc_id"],
        company=d["company"],
        period=d["period"],
        page=page,
        text=text,
    )
    for d in _raw_documents
    for page, text in d["pages"]
]


def get_documents() -> list[Document]:
    return DOCUMENTS


def get_chunks() -> list[Chunk]:
    return CHUNKS
