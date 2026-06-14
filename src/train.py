import json
import os
import sys
from pathlib import Path

import torch

from config import DEFAULT_MODEL, MODEL_DIR, PROJECT_ROOT, TRAINING_PATH

os.environ.setdefault("WANDB_PROJECT", "capital_llm")


def gpu_available() -> bool:
    return torch.cuda.is_available()


def default_batch_size() -> int:
    return 32 if gpu_available() else 8


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


def write_model_card(model_name: str, base_model: str, num_examples: int):
    readme = f"""---
license: mit
tags:
- geography
- capitals
- gpt2
- question-answering
base_model: {base_model}
datasets:
- dr5hn/countries-states-cities-database
language:
- en
---

# {model_name}

Fine-tuned {base_model} for geography Q&A (capitals, currency, country/state/city facts).

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
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Base model: gpt2 (default), gpt2-medium, distilgpt2",
    )
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=default_batch_size())
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--no-wandb", action="store_true")
    parser.add_argument("--full-data", action="store_true", help="Use/rebuild full 280k dataset")
    parser.add_argument("--rebuild-data", action="store_true", help="Rebuild training.jsonl")
    parser.add_argument("--fp16", action="store_true", help="Force fp16 (auto on GPU)")
    parser.add_argument("--no-fp16", action="store_true", help="Disable fp16 even on GPU")
    args = parser.parse_args()

    use_fp16 = args.fp16 or (gpu_available() and not args.no_fp16)
    device = "GPU" if gpu_available() else "CPU"
    if gpu_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    mode = "full" if args.full_data else "capitals"
    texts = load_training_texts(force_rebuild=args.rebuild_data, mode=mode)
    print(f"Base model: {args.model}")
    print(f"Training examples: {len(texts)}")
    steps_per_epoch = (len(texts) + args.batch_size - 1) // args.batch_size
    total_steps = steps_per_epoch * args.epochs
    sec_per_step = 0.15 if use_fp16 else (0.4 if gpu_available() else 3.7)
    print(f"Steps: ~{total_steps} ({args.epochs} epoch(s), batch {args.batch_size}, {device}, fp16={use_fp16})")
    print(f"Estimated time: ~{total_steps * sec_per_step / 60:.1f} min")

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
            notes=f"Geo Q&A fine-tune on {args.model}",
            tags=["geo-llm", "capitals", args.model],
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
        dataloader_pin_memory=gpu_available(),
        fp16=use_fp16,
        gradient_accumulation_steps=1,
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized)
    print("Starting training...")
    trainer.train()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    write_model_card("geo-capital-llm", args.model, len(texts))

    print(f"\nModel saved to {MODEL_DIR}")
    print('Test:  python src/ask.py "what is the capital of kerala"')
    print("Export: python src/export_hf.py --repo-id YOUR_USERNAME/geo-capital-llm")


if __name__ == "__main__":
    main()
