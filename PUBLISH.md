# Publish guide — Hugging Face, GitHub, Ollama

**Live model:** [nishal21/geo-capital-llm](https://huggingface.co/nishal21/geo-capital-llm)

No `huggingface-cli` required — use the Python scripts below.

## Hugging Face model contents

| File | Purpose |
|------|---------|
| `config.json` | GPT-2 architecture config |
| `generation_config.json` | Generation defaults |
| `model.safetensors` | Fine-tuned weights (~475 MB) |
| `tokenizer.json` | Tokenizer vocabulary |
| `tokenizer_config.json` | Tokenizer config |
| `README.md` | Model card (datasets, usage, credits) |

## 1. Download the model

```bash
pip install huggingface_hub
python src/download_hf_model.py
```

Downloads [nishal21/geo-capital-llm](https://huggingface.co/nishal21/geo-capital-llm) into `capital_llm_model/`.

## 2. Upload / update on Hugging Face

```bash
pip install huggingface_hub
python -c "from huggingface_hub import login; login()"
python src/export_hf.py --repo-id nishal21/geo-capital-llm
```

Create a [write token](https://huggingface.co/settings/tokens) when prompted by `login()` — never commit tokens to git.

## 3. Use from Python

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

> For accurate capitals, run the hybrid app: `python src/main.py` (database always used first).

## 4. Ollama (ollama.com library)

`hf.co/...` pull URLs do **not** create a public Ollama library page. To publish properly:

**See [OLLAMA.md](OLLAMA.md)** for the full guide.

Quick summary:

```bash
pip install -r llama.cpp/requirements.txt   # after cloning llama.cpp
python src/convert_for_ollama.py
ollama create nishal21/geo-capital-llm -f Modelfile.ollama
ollama push nishal21/geo-capital-llm
```

Result: **https://ollama.com/nishal21/geo-capital-llm**

Users run:

```bash
ollama run nishal21/geo-capital-llm
```

## 5. GitHub repo

**Include:** `src/`, `README.md`, `LICENSE`, `PUBLISH.md`, `OLLAMA.md`, `learning-journal.md`, `Modelfile.ollama`, `requirements.txt`

**Exclude (`.gitignore`):** `*.safetensors`, `.cache/`, `wandb/`, `.cursor/`, `.env`

## 6. Retrain and re-upload

```bash
python src/vast_train.py --full --skip-data   # GPU
# or
python src/full_train.py                      # CPU

python -c "from huggingface_hub import login; login()"
python src/export_hf.py --repo-id nishal21/geo-capital-llm
```

## Prompt format

```
Question: <your question>? Answer:
```
