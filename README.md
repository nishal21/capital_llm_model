# Country Language Model Application

Geo Q&A app powered by the [countries-states-cities-database](countries-states-cities-database-master/countries-states-cities-database-master/) (250 countries, 5,299 states, 153k+ cities).

## Project Structure

```
country-llm-app/
├── src/
│   ├── main.py          # Interactive Q&A (recommended)
│   ├── ask.py           # Single question from CLI
│   ├── database.py      # Loads and indexes full JSON dataset
│   ├── query_engine.py  # Parses questions and returns answers
│   ├── wikidata.py      # State capitals via wikiDataId (cached)
│   ├── train.py         # Optional GPT-2 fine-tune on dataset Q&A
│   └── model.py         # Legacy wrapper
├── countries-states-cities-database-master/  # Full geo dataset
├── capital_llm_model/   # Optional fine-tuned model
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

First load parses ~47MB nested JSON (~10–20 seconds).

## Usage

**Train your LLM:**

```bash
# All data, 1 epoch (~30-40 hrs on CPU)
python src/full_train.py

# Capitals only, faster (~1-3 hrs)
python src/quick_train.py
```

**Ask questions (LLM):**

```bash
python src/ask.py "what is the capital of kerala"
python src/ask.py "what is the capital of england"
python src/ask.py "what is the capital of india"
```

**Exact database lookup (no LLM):**

```bash
python src/ask.py --db "what is the capital of kerala"
```

**Interactive database CLI:**

```bash
python src/main.py
```

See [PUBLISH.md](PUBLISH.md) for Hugging Face, GitHub, and Ollama steps.

## License

Dataset: ODbL (see dataset LICENSE). App code: MIT.