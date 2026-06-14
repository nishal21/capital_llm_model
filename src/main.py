import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from assistant import answer as smart_answer


def main():
    print("Geo Q&A — verified database + optional LLM fallback")
    print("Capitals use Wikidata-backed lookup (accurate).")
    print("Examples:")
    print("  what is the capital of kerala")
    print("  what is the capital of england")
    print("  what country is Paris in")
    print("  where is Malappuram in")
    print("  currency of Japan | list states in India | exit")
    print("Flags: --llm (LLM only) | --db (database only)")
    print()

    while True:
        question = input("Ask> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            break

        force_llm = question.endswith(" --llm") or "--llm" in question
        force_db = question.endswith(" --db") or "--db" in question
        question = question.replace("--llm", "").replace("--db", "").strip()

        if force_db and not force_llm:
            from query_engine import QueryEngine

            print(QueryEngine().answer(question))
        else:
            result, source = smart_answer(question, force_llm=force_llm)
            print(result)
            print(f"[{source}]")


if __name__ == "__main__":
    main()
