"""
Build training.jsonl from countries-states-cities-database + Wikidata state capitals.

Modes:
  capitals (default) ~10k examples, trains in ~1-3 hours on CPU
  full             ~280k examples, takes days on CPU

Usage:
  python src/build_training_data.py              # capitals only (recommended)
  python src/build_training_data.py --full       # everything (slow)
"""

import argparse
import json
from pathlib import Path

from config import PROJECT_ROOT
from database import GeoDatabase
from wikidata import fetch_state_capital

OUTPUT_PATH = PROJECT_ROOT / "data" / "training.jsonl"

CAPITAL_TEMPLATES_FULL = [
    "Question: What is the capital of {name}? Answer: The capital of {name} is {capital}.",
    "Question: what is the capital of {name}? Answer: The capital of {name} is {capital}.",
    "Question: What's the capital of {name}? Answer: The capital of {name} is {capital}.",
    "Question: capital of {name}? Answer: The capital of {name} is {capital}.",
]

CAPITAL_TEMPLATES_FAST = [
    "Question: What is the capital of {name}? Answer: The capital of {name} is {capital}.",
    "Question: what is the capital of {name}? Answer: The capital of {name} is {capital}.",
]


def add_capital_examples(examples: list[str], name: str, capital: str, templates: list[str]):
    for template in templates:
        examples.append(template.format(name=name, capital=capital))


def build_examples(db: GeoDatabase, mode: str = "capitals") -> list[str]:
    examples: list[str] = []
    templates = CAPITAL_TEMPLATES_FAST if mode == "capitals" else CAPITAL_TEMPLATES_FULL
    db.load()

    all_states = []
    for states in db.states_by_name.values():
        all_states.extend(states)

    print("Building state capital examples (Wikidata, cached)...")
    seen_states = set()
    total = len(all_states)
    for index, state in enumerate(all_states, start=1):
        key = (state["name"], state["country_name"])
        if key in seen_states:
            continue
        seen_states.add(key)

        name = state["name"]
        capital = db.infer_state_capital(state)
        if not capital:
            capital = fetch_state_capital(state.get("wikiDataId"))
        if capital:
            add_capital_examples(examples, name, capital, templates)

        if mode == "full":
            country = state["country_name"]
            examples.append(
                f"Question: What country is {name} in? Answer: {name} is in {country}."
            )
            examples.append(
                f"Question: what country is {name} in? Answer: {name} is in {country}."
            )

        if index % 200 == 0:
            print(f"  States processed: {index}/{total}")

    print("Building country capital examples...")
    for country in db.countries_by_name.values():
        name = country["name"]
        if country.get("capital"):
            add_capital_examples(examples, name, country["capital"], templates)

        if mode == "full":
            for field in (
                "currency",
                "phonecode",
                "iso2",
                "iso3",
                "region",
                "subregion",
                "nationality",
                "population",
            ):
                value = country.get(field)
                if value not in (None, ""):
                    label = field.replace("_", " ")
                    examples.append(
                        f"Question: What is the {label} of {name}? "
                        f"Answer: The {label} of {name} is {value}."
                    )
                    examples.append(
                        f"Question: what is the {label} of {name}? "
                        f"Answer: The {label} of {name} is {value}."
                    )

    if mode == "full":
        print("Building city examples (unique names only)...")
        for cities in db.cities_by_name.values():
            if len(cities) != 1:
                continue
            city = cities[0]
            name = city["name"]
            examples.append(
                f"Question: What country is {name} in? Answer: {name} is in {city['country']}."
            )
            examples.append(
                f"Question: What state is {name} in? "
                f"Answer: {name} is in {city['state']}, {city['country']}."
            )

    return examples


def main(mode: str = "capitals"):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = GeoDatabase()
    examples = build_examples(db, mode=mode)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        for text in examples:
            handle.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(examples)} training examples ({mode} mode) to {OUTPUT_PATH}")
    if mode == "capitals":
        steps_est = len(examples) // 8
        print(f"Estimated training: ~{steps_est} steps/epoch → ~1-3 hours on CPU with quick_train.py")
    else:
        print("Warning: full mode takes days on CPU. Use capitals mode instead.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include all city/country facts (~280k examples, very slow training)",
    )
    args = parser.parse_args()
    main(mode="full" if args.full else "capitals")
