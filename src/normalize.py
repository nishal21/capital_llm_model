import re
import unicodedata


def normalize_question(text: str) -> str:
    """Clean user input: trim, fix stray brackets, collapse whitespace."""
    text = text.strip()
    text = text.strip("[](){}\"'")
    text = re.sub(r"[\[\](){}]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\btime zone\b", "timezone", text, flags=re.I)
    # "what country is Kerala is in" → "what country is Kerala in"
    text = re.sub(
        r"^(what country is .+?) is in(\??)$",
        r"\1 in\2",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"^(what state is .+?) is in(\??)$",
        r"\1 in\2",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"^(where is .+?) is in(\??)$",
        r"\1\2",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"^(where is .+?) in(\??)$",
        r"\1\2",
        text,
        flags=re.I,
    )
    if text and not text.endswith("?"):
        text = text.rstrip(".!")
    return text


def extract_capital_question(text: str) -> str | None:
    """Return place name if question asks for a capital."""
    text = normalize_question(text)
    patterns = [
        r"^what(?:'s| is) the capital of (.+?)\??$",
        r"^capital of (.+?)\??$",
        r"^(.+?) capital\??$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text, re.I)
        if match:
            return match.group(1).strip(" ?.")
    return None


def to_training_prompt(question: str) -> str:
    question = normalize_question(question)
    if not question.lower().startswith("question:"):
        question = f"Question: {question}"
    if not question.endswith("?"):
        question = f"{question}?"
    return f"{question} Answer:"


def wrap_bidi(text: str) -> str:
    """Wrap RTL script so mixed LTR/RTL strings render correctly in terminals."""
    if not text:
        return text
    for char in text:
        if unicodedata.bidirectional(char) in ("R", "AL"):
            return f"\u2067{text}\u2069"
    return text


def parse_place_hint(text: str) -> tuple[str, str | None]:
    """Split 'Paris in France' or 'Usa in Japan' into place + country hint."""
    text = text.strip().rstrip("?.!")
    match = re.match(r"^(.+?) in (.+)$", text, re.I)
    if match:
        place = match.group(1).strip()
        hint = match.group(2).strip()
        if place and hint and len(hint) >= 2:
            return place, hint
    return text, None


def title_place(name: str) -> str:
    """Title-case place names for display."""
    if not name:
        return name
    return " ".join(part.capitalize() for part in name.split())
