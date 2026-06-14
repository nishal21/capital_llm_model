# Learning Journal

## App

Hybrid geo Q&A: database + Wikidata first, GPT-2 fallback. Model fine-tuned for <$2 on Vast.ai; no budget for bigger models or scratch training (no money to test). Still not good alone — use `python src/main.py`.

```bash
pip install -r requirements.txt
python src/main.py
```

## Model on Hugging Face

**[nishal21/geo-capital-llm](https://huggingface.co/nishal21/geo-capital-llm)**

Download (no `huggingface-cli`):

```bash
pip install huggingface_hub
python src/download_hf_model.py
```

Upload/update:

```bash
python -c "from huggingface_hub import login; login()"
python src/export_hf.py --repo-id nishal21/geo-capital-llm
```

## Ollama (ollama.com library)

See **OLLAMA.md** — convert to GGUF, then push:

```bash
python src/convert_for_ollama.py
ollama create nishal21/geo-capital-llm -f Modelfile.ollama
ollama push nishal21/geo-capital-llm
```

**Live:** https://ollama.com/nishal21/geo-capital-llm

```bash
ollama pull nishal21/geo-capital-llm
ollama run nishal21/geo-capital-llm "Question: what is the capital of Kerala? Answer:"
```

## Credits

- Dataset: [dr5hn/countries-states-cities-database](https://github.com/dr5hn/countries-states-cities-database) (ODbL)
- App: MIT — see `LICENSE`
