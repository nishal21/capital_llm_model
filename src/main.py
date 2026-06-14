import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from query_engine import QueryEngine


def main():
    print("Geo Q&A — powered by countries-states-cities-database")
    print("Examples: capital of India | currency of Japan | what country is Paris in")
    print("           list states in India | tell me about Kerala | exit")
    print("Loading dataset (first question may take ~10-20 seconds)...")

    engine = QueryEngine()

    while True:
        question = input("\nAsk> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            break
        print(engine.answer(question))


if __name__ == "__main__":
    main()
