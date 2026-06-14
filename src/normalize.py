import re


def normalize_question(text: str) -> str:
    """Clean user input: trim, fix stray brackets, collapse whitespace."""
    text = text.strip()
    text = text.strip("[](){}\"'")
    text = re.sub(r"[\[\](){}]", "", text)
    text = re.sub(r"\s+", " ", text)
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
