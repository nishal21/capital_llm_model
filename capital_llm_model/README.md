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

Fine-tuned **GPT-2** (`gpt2`) for geography Q&A. Best used with the [country-llm-app](https://github.com/nishal21/capital_llm_model) hybrid CLI (database first, this model as fallback).

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

- **Base model:** `gpt2` (124M parameters)
- **Data:** ~277k Q&A examples from [countries-states-cities-database](https://github.com/dr5hn/countries-states-cities-database)
- **State capitals:** enriched via Wikidata `wikiDataId`
- **Format:** `Question: …? Answer: …`

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

```bash
ollama pull hf.co/nishal21/geo-capital-llm
ollama run hf.co/nishal21/geo-capital-llm "Question: what is the capital of Kerala? Answer:"
```

## Data credits

Geographic training data: [Countries States Cities Database](https://github.com/dr5hn/countries-states-cities-database) (ODbL) by [dr5hn](https://github.com/dr5hn).

For **accurate capitals**, use the app's verified database + Wikidata lookup — do not rely on the LLM alone.

## Limitations

- Small GPT-2 model; factual errors possible on rare queries
- Capitals and structured facts are more reliable via the companion app's database layer
