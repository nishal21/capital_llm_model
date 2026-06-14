import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from assistant import answer as smart_answer
from normalize import normalize_question


def main():
    force_llm = "--llm" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg not in {"--llm", "--db"}]

    question = normalize_question(
        " ".join(args) if args else "what is the capital of India?"
    )

    print(f"Question: {question}")

    if "--db" in sys.argv and not force_llm:
        from query_engine import QueryEngine

        result = QueryEngine().answer(question)
        source = "database only"
    else:
        result, source = smart_answer(question, force_llm=force_llm)

    print("\n--- Result ---")
    print(result)
    print(f"Source: {source}")
    print("--------------")


if __name__ == "__main__":
    main()
