# Geo Q&A

Plain-English geography questions: capitals, cities, countries, timezones, currencies. Most answers come from a verified database, not from a language model.

The included LLM is a fine-tuned **GPT-2** trained for under **$2** on a rented [Vast.ai](https://vast.ai) GPU. We could not afford a larger base model, and training from scratch was not an option either (no budget to run tests or failed experiments). It is fine-tuned on geography Q&A and it is still not good: you will get answers, but they may or may not be correct. That is why this app checks the database first.

**Run it:**

```bash
pip install -r requirements.txt
python src/main.py
```

```
Ask> what is the capital of kerala
The capital of kerala is Thiruvananthapuram.
[verified database]

Ask> where is Alappuzha
City: Alappuzha
State/Region: Kerala
Country: India
...

Ask> currency of Japan
The currency of Japan is JPY.
```

## How to get good answers

Use the **Python app** (`python src/main.py`). That is the intended way to run this project.

| Goal | What to do |
|------|------------|
| Capitals, currencies, timezones, populations | Ask normally. These route to the database or Wikidata first. |
| City lookups (`where is …`) | Use the full place name. If ambiguous, add the country: `where is Usa in Japan`. |
| Skip the LLM entirely | Append `--db` or run `python src/ask.py --db "your question"`. |
| Force the LLM only (not recommended) | Append `--llm`. |

Capitals **always** go through the database path in the default app. You should not see wrong capital guesses from the model when using `main.py` normally.

The fine-tuned GPT-2 model is a **fallback** for questions the database cannot answer. On its own (Ollama, Hugging Face, `--llm`), it will return text, but accuracy is not guaranteed. Expect wrong or incomplete answers.

## What it does

Answers are layered:

1. **[Countries States Cities Database](https://github.com/dr5hn/countries-states-cities-database)** — countries, states, 150k+ cities.
2. **Wikidata** — state capitals and official languages when the dataset is incomplete.
3. **GPT-2 fallback** — only when steps 1–2 cannot answer.

```
Question → database / Wikidata → (if no match) → geo-capital-llm
```

For structured facts, trust the app with `[verified database]` or `[wikidata]` in the output. Treat anything from `[llm fallback]` as a guess.

## Setup

**Requirements:** Python 3.10+. About 500 MB extra disk if you download the LLM weights (optional for database-only use).

1. Clone this repo (include the `countries-states-cities-database-master` folder).
2. For city lookups (`where is ...`), you need `countries+states+cities.json` in the dataset's `json/` folder. It is not in the upstream repo; download it from the [dataset releases](https://github.com/dr5hn/countries-states-cities-database) if missing.
3. Install and run:

```bash
pip install -r requirements.txt
python src/main.py
```

Single question from the command line:

```bash
python src/ask.py "what is the capital of India"
python src/ask.py --db "list states in India"    # database only, no model load
```

## Questions you can ask

- `what is the capital of kerala` / `vatican city` / `england`
- `where is Malappuram` / `where is Alappuzha`
- `what country is Kerala in`
- `list states in India`
- `currency of Japan` / `timezone of India` / `population of India`
- `native language of India`
- `tell me about Kerala`
- `what is USA` (also understands `UK`, `vatican`, etc.)

## Pre-trained model

Weights: **[nishal21/geo-capital-llm](https://huggingface.co/nishal21/geo-capital-llm)**  
Ollama: **[nishal21/geo-capital-llm](https://ollama.com/nishal21/geo-capital-llm)**

| Detail | Value |
|--------|-------|
| Base model | GPT-2 (124M parameters) |
| Training data | ~277k Q&A pairs from the countries-states-cities dataset |
| Training cost | Under $2 (rented GPU on [Vast.ai](https://vast.ai)) |
| Prompt format | `Question: what is the capital of Kerala? Answer:` |

### About the model (read this)

This model is **GPT-2 fine-tuned on geography Q&A**. That is the whole story.

We did not have the budget to train a bigger model (Llama, Mistral, etc.) or to train one from scratch. Scratch training needs many GPU hours just to test whether an approach works; we did not have money for those trial runs. What we could afford was one cheap fine-tune of GPT-2: **less than $2** on a rented Vast.ai GPU. Fine-tuning helped a little, but the model is still weak by modern standards.

**What to expect:**

- It will answer geography questions in the trained format.
- Answers **may or may not be correct**. Do not trust it for facts without checking.
- It is useful as a fallback inside this app, or as a small experiment you can run locally or via Ollama.
- For anything that matters, use `python src/main.py` so the database and Wikidata handle the lookup first.

If you pull it from Ollama or Hugging Face and ask questions directly, you are using the LLM alone. That is the worst way to use this project.

Download weights into the project:

```bash
pip install huggingface_hub
python src/download_hf_model.py
```

Or load in Python:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("nishal21/geo-capital-llm")
tokenizer = AutoTokenizer.from_pretrained("nishal21/geo-capital-llm")
```

## Ollama

The model is published on [ollama.com](https://ollama.com/nishal21/geo-capital-llm):

```bash
ollama pull nishal21/geo-capital-llm
ollama run nishal21/geo-capital-llm "Question: what is the capital of Kerala? Answer:"
```

To rebuild and push after retraining, see [OLLAMA.md](OLLAMA.md).

## Train your own (optional)

```bash
python src/quick_train.py      # capitals only, faster
python src/full_train.py       # full dataset (~280k examples)
python src/vast_train.py       # GPU training helper for Vast.ai
```

More details: [PUBLISH.md](PUBLISH.md)

## License

**Application code:** [MIT](LICENSE). MIT is kept here because it is simple, widely used for ML tooling, and matches the model card on Hugging Face. No patent clause is needed for this scope.

**Geographic data:** [Countries States Cities Database](https://github.com/dr5hn/countries-states-cities-database) by [dr5hn](https://github.com/dr5hn) ([ODbL 1.0](countries-states-cities-database-master/countries-states-cities-database-master/LICENSE)). Redistributing derived data requires ODbL compliance.

**Wikidata enrichment:** CC0 where applicable ([wikidata.org](https://www.wikidata.org/)).

**Model weights:** [nishal21/geo-capital-llm](https://huggingface.co/nishal21/geo-capital-llm) (MIT).
