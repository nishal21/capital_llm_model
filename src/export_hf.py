"""
Upload fine-tuned model to Hugging Face Hub.

Uploads everything in capital_llm_model/:
  - config.json, generation_config.json
  - model.safetensors (or pytorch_model.bin)
  - tokenizer.json, tokenizer_config.json
  - README.md (model card)

Setup:
  pip install huggingface_hub
  python -c "from huggingface_hub import login; login()"

Usage:
  python src/export_hf.py --repo-id nishal21/geo-capital-llm
"""

import argparse
from pathlib import Path

from config import MODEL_DIR


def list_model_files() -> list[Path]:
    if not MODEL_DIR.is_dir():
        return []
    allowed = {
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "README.md",
    }
    files = [p for p in MODEL_DIR.iterdir() if p.is_file() and p.name in allowed]
    files.extend(MODEL_DIR.glob("*.safetensors"))
    files.extend(MODEL_DIR.glob("*.bin"))
    return sorted(files, key=lambda p: p.name)


def main():
    parser = argparse.ArgumentParser(description="Upload capital_llm_model/ to Hugging Face Hub")
    parser.add_argument(
        "--repo-id",
        required=True,
        help="HF repo id, e.g. YOUR_USERNAME/geo-capital-llm",
    )
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    if not (MODEL_DIR / "config.json").exists():
        raise SystemExit(f"Model not found at {MODEL_DIR}. Run training first.")

    weights = list(MODEL_DIR.glob("*.safetensors")) + list(MODEL_DIR.glob("pytorch_model.bin"))
    if not weights:
        raise SystemExit(f"No weights in {MODEL_DIR}. Expected model.safetensors or pytorch_model.bin.")

    files = list_model_files()
    print("Uploading to Hugging Face:")
    for path in files:
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  - {path.name} ({size_mb:.1f} MB)")

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(repo_id=args.repo_id, exist_ok=True, private=args.private)
    api.upload_folder(
        folder_path=str(MODEL_DIR),
        repo_id=args.repo_id,
        commit_message="Upload geo-capital-llm (GPT-2 fine-tuned on geography Q&A)",
    )

    print(f"\nDone: https://huggingface.co/{args.repo_id}")
    print(f"Ollama:  ollama pull hf.co/{args.repo_id}")


if __name__ == "__main__":
    main()
