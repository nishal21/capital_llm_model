---
license: mit
tags:
- geography
- capitals
- gpt2
- question-answering
base_model: gpt2
datasets:
- dr5hn/countries-states-cities-database
language:
- en
---

# geo-capital-llm

Fine-tuned **GPT-2** (`gpt2`, 124M parameters) for geography Q&A.

**Be honest about what this is:** GPT-2 fine-tuned on geography data. It is still not good. You will get answers, but they **may or may not be correct**. Training cost **under $2** on a rented [Vast.ai](https://vast.ai) GPU. We could not afford a larger base model (Llama, Mistral, etc.) or training from scratch (no budget for trial runs or failed experiments).

**Best use:** the [country-llm-app](https://github.com/nishal21/country-llm-app) hybrid CLI — verified database and Wikidata first, this model only as fallback. Using this repo or Ollama alone is the worst way to get reliable geography facts.

## How to get good answers

| Goal | What to do |
|------|------------|
| Reliable capitals, currencies, facts | Run the app: `python src/main.py` ([repo](https://github.com/nishal21/country-llm-app)) |
| Skip the LLM | Use `--db` in the app |
| Experiment with the model only | Use Transformers or Ollama below (expect wrong answers) |

## Files in this repository

| File | Description |
|------|-------------|
| `config.json` | Model architecture (GPT-2) |
| `generation_config.json` | Default generation settings |
| `model.safetensors` | Fine-tuned weights (~475 MB) |
| `tokenizer.json` | GPT-2 tokenizer vocabulary |
| `tokenizer_config.json` | Tokenizer settings |
| `README.md` | This model card |

## Training

| Detail | Value |
|--------|-------|
| Base model | `gpt2` (124M parameters) |
| Data | ~277k Q&A examples from [countries-states-cities-database](https://github.com/dr5hn/countries-states-cities-database) |
| State capitals | Enriched via Wikidata `wikiDataId` |
| Format | `Question: …? Answer: …` |
| Hardware | Rented GPU on [Vast.ai](https://vast.ai) |
| Total cost | Under **$2** |

We did not have the budget to train a bigger model or to train one from scratch. Scratch training needs many GPU hours just to test whether an approach works; we did not have money for those trial runs. Fine-tuning GPT-2 helped a little, but the result is still weak by modern standards.

## Usage (Transformers)

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

repo = "nishal21/geo-capital-llm"
tokenizer = AutoTokenizer.from_pretrained(repo)
model = AutoModelForCausalLM.from_pretrained(repo)

prompt = "Question: what country is Paris in? Answer:"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=40, do_sample=False)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Prompt format

```
Question: <your question>? Answer:
```

## Ollama

Published on [ollama.com/nishal21/geo-capital-llm](https://ollama.com/nishal21/geo-capital-llm):

```bash
ollama pull nishal21/geo-capital-llm
ollama run nishal21/geo-capital-llm "Question: what is the capital of Kerala? Answer:"
```

## Limitations

- **GPT-2 fine-tune only** — not an instruction-tuned or modern LLM.
- **Answers may or may not be correct.** Do not use for facts without checking another source.
- **Budget constraints** — trained for under $2; no room for bigger models or scratch training experiments.
- **Standalone use is unreliable** — capitals and structured facts are much better via the companion app's database + Wikidata layer.

For accurate geography Q&A, clone [country-llm-app](https://github.com/nishal21/country-llm-app) and run `python src/main.py`.

## Data credits

Geographic training data: [Countries States Cities Database](https://github.com/dr5hn/countries-states-cities-database) (ODbL) by [dr5hn](https://github.com/dr5hn).

## License

MIT — same as the [country-llm-app](https://github.com/nishal21/country-llm-app) application code.
