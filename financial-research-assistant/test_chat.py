from chat import _LLMChatResponse, answer, verify_numeric_fidelity
from corpus import get_chunks
from models import Chunk
from retrieval import extract_companies, extract_periods, retrieve


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

# Real chunk from TCS's actual Q2 FY26 earnings call transcript (page 6):
# "Our Q2 operating margin stood at 25.2%, reflecting a sequential
# improvement of 70 basis points."
TCS_MARGIN_CHUNK = next(c for c in get_chunks() if c.chunk_id == "tcs-transcript-q2fy26-p6")


def test_verify_numeric_fidelity_accepts_verbatim_numbers():
    answer = "TCS's Q2 FY26 operating margin was 25.2%, up 70 basis points sequentially."
    assert verify_numeric_fidelity(answer, [TCS_MARGIN_CHUNK]) == []


def test_verify_numeric_fidelity_rejects_fabricated_number():
    answer = "TCS's Q2 FY26 operating margin was 99.9%."
    unverified = verify_numeric_fidelity(answer, [TCS_MARGIN_CHUNK])
    assert "99.9%" in unverified


def test_verify_numeric_fidelity_rejects_rounded_number():
    # 25.2% rounded to 25% must be caught -- numeric fidelity means verbatim,
    # not "close enough".
    answer = "Operating margin was approximately 25% in Q2 FY26."
    unverified = verify_numeric_fidelity(answer, [TCS_MARGIN_CHUNK])
    assert "25%" in unverified


def test_extract_companies_matches_alias():
    assert extract_companies("How is TCS doing?") == ["TCS"]


def test_extract_periods_matches_quarter_and_year():
    assert extract_periods("Compare Q4FY24 to FY23 results") == ["FY23", "Q4FY24"]


def test_retrieve_filters_by_company_and_prefers_matching_period():
    results = retrieve("What was TCS's operating margin in Q2FY26?")
    assert results, "expected at least one retrieved chunk"
    assert all(c.company == "TCS" for c in results)
    assert results[0].period == "Q2FY26"
    assert results[0].chunk_id == "tcs-transcript-q2fy26-p6"


def test_retrieve_returns_empty_for_unknown_topic():
    results = retrieve("What is TCS's stance on cryptocurrency mining?")
    assert results == []


def test_answer_builds_citations_from_retrieved_chunk_metadata_not_llm():
    fake_response = _LLMChatResponse(
        answer="TCS's Q2 FY26 operating margin was 25.2%, up 70 basis points sequentially.",
        cited_chunk_ids=["tcs-transcript-q2fy26-p6"],
        insufficient_data=False,
    )
    result = answer(
        "What was TCS's operating margin in Q2FY26?",
        client=_FakeClient(fake_response),
    )
    assert result.insufficient_data is False
    assert len(result.citations) == 1
    assert result.citations[0].doc_id == "tcs-transcript-q2fy26"
    assert result.citations[0].page == 6


def test_answer_ignores_chunk_id_llm_invented_outside_retrieved_set():
    fake_response = _LLMChatResponse(
        answer="TCS's Q2 FY26 operating margin was 25.2%.",
        cited_chunk_ids=["tcs-transcript-q2fy26-p6", "made-up-chunk-id"],
        insufficient_data=False,
    )
    result = answer(
        "What was TCS's operating margin in Q2FY26?",
        client=_FakeClient(fake_response),
    )
    assert len(result.citations) == 1
    assert result.citations[0].doc_id == "tcs-transcript-q2fy26"


def test_answer_withholds_response_on_failed_numeric_verification():
    fake_response = _LLMChatResponse(
        answer="TCS's Q2 FY26 operating margin was 99.9%, a huge jump.",
        cited_chunk_ids=["tcs-transcript-q2fy26-p6"],
        insufficient_data=False,
    )
    result = answer(
        "What was TCS's operating margin in Q2FY26?",
        client=_FakeClient(fake_response),
    )
    assert result.insufficient_data is True
    assert result.citations == []


def test_answer_returns_insufficient_data_for_off_corpus_question():
    result = answer(
        "What is TCS's stance on cryptocurrency mining?",
        client=_FakeClient(None),  # should never be called
    )
    assert result.insufficient_data is True
    assert result.citations == []
