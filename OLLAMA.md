# Publish geo-capital-llm to ollama.com (proper library page)

Your model will appear at **https://ollama.com/nishal21/geo-capital-llm** and users run:

```bash
ollama run nishal21/geo-capital-llm
```

This is different from `ollama pull hf.co/...` (Hugging Face import URL only).

## Why GGUF?

Ollama's public registry needs a **GGUF** model. Your Hugging Face repo has **safetensors** — convert once with `llama.cpp`.

## Step 1 — Install Ollama

Download from [ollama.com](https://ollama.com/download) and install.

## Step 2 — Ollama account + SSH key

1. Sign up at [ollama.com/signup](https://ollama.com/signup)
2. Copy your Ollama public key:

   **Windows (PowerShell):**
   ```powershell
   type $env:USERPROFILE\.ollama\id_ed25519.pub
   ```

3. Paste it at [ollama.com/settings/keys](https://ollama.com/settings/keys)

## Step 3 — Get model weights

If `capital_llm_model/` is empty:

```bash
pip install huggingface_hub
python src/download_hf_model.py
```

Or use your existing local folder.

## Step 4 — Convert to GGUF

```bash
git clone https://github.com/ggerganov/llama.cpp
pip install -r llama.cpp/requirements.txt
python src/convert_for_ollama.py
```

Creates `capital_llm_model.gguf` (~475 MB f16).

## Step 5 — Create Ollama model

From the project root:

```bash
ollama create nishal21/geo-capital-llm -f Modelfile.ollama
```

Test locally:

```bash
ollama run nishal21/geo-capital-llm "Question: what is the capital of Kerala? Answer:"
```

## Step 6 — Push to ollama.com

```bash
ollama push nishal21/geo-capital-llm
```

After success, your model page is live:

**https://ollama.com/nishal21/geo-capital-llm**

Anyone can run:

```bash
ollama pull nishal21/geo-capital-llm
ollama run nishal21/geo-capital-llm "Question: what country is Paris in? Answer:"
```

## Update after retraining

```bash
python src/convert_for_ollama.py
ollama create nishal21/geo-capital-llm -f Modelfile.ollama
ollama push nishal21/geo-capital-llm
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `not authorized to push` | Add the correct `.ollama/id_ed25519.pub` key at ollama.com/settings/keys |
| `namespace does not exist` | Use your exact Ollama username: `yourname/geo-capital-llm` |
| GPT-2 convert fails | Update llama.cpp: `git pull` in llama.cpp folder |
| Wrong capital answers | Use the hybrid app (`python src/main.py`) — DB is accurate; LLM is fallback |

## Recommended

For **accurate capitals**, use this repo's Python app (database + Wikidata first):

```bash
python src/main.py
```

The Ollama model is best for open-ended geo questions where the LLM helps.
