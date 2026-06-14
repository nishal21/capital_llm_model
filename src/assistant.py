"""Smart geo Q&A: verified database for facts, LLM fallback when needed."""

from normalize import extract_capital_question, normalize_question
from query_engine import QueryEngine

_LLM = None
_ENGINE = None


def _get_engine() -> QueryEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = QueryEngine()
    return _ENGINE


def _llm_available() -> bool:
    from inference import resolve_model_dir

    return resolve_model_dir() is not None


def _try_llm(question: str) -> str | None:
    global _LLM
    try:
        from inference import answer_question as llm_answer

        return llm_answer(question)
    except FileNotFoundError:
        return None


def _is_failure(text: str) -> bool:
    lower = text.lower()
    return (
        "could not find" in lower
        or "not found" in lower
        or "no capital is stored" in lower
        or "not stored in the dataset" in lower
        or "was not found in the dataset" in lower
        or "was not found in the city index" in lower
    )


def _clean_capital_answer(place: str, capital: str) -> str:
    return f"The capital of {place} is {capital}."


def answer(question: str, force_llm: bool = False) -> tuple[str, str]:
    """
    Return (answer_text, source_label).
    Default: database for capitals and structured facts; LLM only as fallback.
    """
    question = normalize_question(question)
    if not question:
        return "Please ask a question.", "none"

    engine = _get_engine()

    if force_llm:
        llm_result = _try_llm(question)
        if llm_result:
            return llm_result, "LLM only"
        db_result = engine.answer(question)
        return db_result, "database (LLM unavailable)"

    # Capitals always use verified lookup (Wikidata + dataset)
    place = extract_capital_question(question)
    if place:
        capital, note = engine.db.place_capital(place)
        if capital:
            return _clean_capital_answer(place, capital), "verified database"
        db_result = engine.answer(question)
        if not _is_failure(db_result):
            return db_result, "database"
        llm_result = _try_llm(question)
        if llm_result:
            return llm_result, "LLM fallback"
        return db_result, "database"

    # Structured geo questions → database first
    db_result = engine.answer(question)
    if not _is_failure(db_result):
        return db_result, "database"

    # Unknown → try LLM
    llm_result = _try_llm(question)
    if llm_result:
        return llm_result, "LLM fallback"

    return db_result, "database"
