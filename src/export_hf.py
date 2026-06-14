"""
Upload fine-tuned model to Hugging Face Hub.

Setup:
  pip install huggingface_hub
  huggingface-cli login

Usage:
  python src/export_hf.py --repo-id YOUR_USERNAME/geo-capital-llm
"""

import argparse
from pathlib import Path

from config import PROJECT_ROOT

MODEL_DIR = PROJECT_ROOT / "capital_llm_model"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", required=True, help="HF repo id, e.g. nishal21/geo-capital-llm")
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    if not (MODEL_DIR / "config.json").exists():
        raise SystemExit(f"Model not found at {MODEL_DIR}. Run python src/train.py first.")

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(repo_id=args.repo_id, exist_ok=True, private=args.private)
    api.upload_folder(
        folder_path=str(MODEL_DIR),
        repo_id=args.repo_id,
        commit_message="Upload geo-capital-llm fine-tuned model",
    )

    print(f"Uploaded to https://huggingface.co/{args.repo_id}")
    print(f"Ollama: ollama pull hf.co/{args.repo_id}")


if __name__ == "__main__":
    main()
