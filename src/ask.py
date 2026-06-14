import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from inference import answer_question as llm_answer
from normalize import normalize_question

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def answer_with_database(question: str) -> str:
    from query_engine import QueryEngine

    return QueryEngine().answer(question)


def main():
    use_db = "--db" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--db"]

    question = normalize_question(" ".join(args) if args else "what is the capital of India?")

    print(f"Question: {question}")

    if use_db:
        result = answer_with_database(question)
        source = "database lookup"
    else:
        try:
            print("Loading LLM...")
            result = llm_answer(question)
            source = "geo-capital-llm"
        except FileNotFoundError as exc:
            print(str(exc))
            print("Falling back to database lookup...")
            result = answer_with_database(question)
            source = "database fallback (train model first)"

    print("\n--- Result ---")
    print(result)
    print(f"Source: {source}")
    print("--------------")
    if not use_db:
        print("Tip: use --db for exact database answers without the LLM")


if __name__ == "__main__":
    main()
