import json
import os
import sys
from pathlib import Path

from config import PROJECT_ROOT

TRAINING_PATH = PROJECT_ROOT / "data" / "training.jsonl"
MODEL_DIR = PROJECT_ROOT / "capital_llm_model"

os.environ.setdefault("WANDB_PROJECT", "capital_llm")


def load_training_texts(force_rebuild: bool = False, mode: str = "capitals") -> list[str]:
    if force_rebuild or not TRAINING_PATH.exists():
        print(f"Building {mode} training data (may take a few minutes)...")
        from build_training_data import build_examples
        from database import GeoDatabase

        TRAINING_PATH.parent.mkdir(parents=True, exist_ok=True)
        db = GeoDatabase()
        examples = build_examples(db, mode=mode)
        with open(TRAINING_PATH, "w", encoding="utf-8") as handle:
            for text in examples:
                handle.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
        print(f"Saved {len(examples)} examples to {TRAINING_PATH}")

    texts = []
    with open(TRAINING_PATH, "r", encoding="utf-8") as handle:
        for line in handle:
            texts.append(json.loads(line)["text"])
    return texts


def write_model_card(model_name: str, num_examples: int):
    readme = f"""---
license: mit
tags:
- geography
- capitals
- gpt2
- question-answering
datasets:
- dr5hn/countries-states-cities-database
language:
- en
---

# {model_name}

Fine-tuned GPT-2 for geography Q&A (capitals, currency, country/state/city facts).

## Training data

- Source: [countries-states-cities-database](https://github.com/dr5hn/countries-states-cities-database)
- State capitals enriched via Wikidata `wikiDataId`
- Examples: {num_examples}

## Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("./capital_llm_model")
model = AutoModelForCausalLM.from_pretrained("./capital_llm_model")

prompt = "Question: what is the capital of Kerala? Answer:"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=30, do_sample=False)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Prompt format

```
Question: <your question>? Answer:
```
"""
    (MODEL_DIR / "README.md").write_text(readme, encoding="utf-8")


def main():
    import argparse

    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="distilgpt2", help="Base model (distilgpt2 or gpt2)")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--no-wandb", action="store_true")
    parser.add_argument("--full-data", action="store_true", help="Use/rebuild full 280k dataset (slow)")
    parser.add_argument("--rebuild-data", action="store_true", help="Rebuild training.jsonl before training")
    args = parser.parse_args()

    mode = "full" if args.full_data else "capitals"
    texts = load_training_texts(force_rebuild=args.rebuild_data, mode=mode)
    print(f"Training examples: {len(texts)}")
    steps_per_epoch = (len(texts) + args.batch_size - 1) // args.batch_size
    total_steps = steps_per_epoch * args.epochs
    hours_est = total_steps * 3.7 / 3600
    print(f"Steps: ~{total_steps} ({args.epochs} epoch(s), batch {args.batch_size})")
    print(f"Estimated time on CPU: ~{hours_est:.0f} hours")

    dataset = Dataset.from_dict({"text": texts})
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.pad_token = tokenizer.eos_token

    def tokenize(batch):
        tokens = tokenizer(
            batch["text"],
            padding="max_length",
            truncation=True,
            max_length=args.max_length,
        )
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])
    model = AutoModelForCausalLM.from_pretrained(args.model)

    report_to = "none" if args.no_wandb else "wandb"
    if not args.no_wandb:
        import wandb

        wandb.init(
            project="capital_llm",
            notes="Geo Q&A model for HF / Ollama publish",
            tags=["geo-llm", "capitals"],
        )

    training_args = TrainingArguments(
        output_dir=str(PROJECT_ROOT / "results"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
        weight_decay=0.01,
        logging_steps=50,
        save_strategy="epoch",
        save_total_limit=2,
        report_to=report_to,
        dataloader_pin_memory=False,
        fp16=False,
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized)
    print("Starting training...")
    trainer.train()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    write_model_card("geo-capital-llm", len(texts))

    if not args.no_wandb:
        import wandb

        wandb.finish()

    print(f"\nModel saved to {MODEL_DIR}")
    print("Test:  python src/ask.py \"what is the capital of kerala\"")
    print("Export: python src/export_hf.py --repo-id YOUR_USERNAME/geo-capital-llm")


if __name__ == "__main__":
    main()
