"""
Download the fine-tuned model from Hugging Face (no huggingface-cli required).

  pip install huggingface_hub
  python src/download_hf_model.py
  python src/download_hf_model.py --repo-id nishal21/geo-capital-llm
"""

import argparse

from config import MODEL_DIR

DEFAULT_REPO = "nishal21/geo-capital-llm"


def main():
    parser = argparse.ArgumentParser(description="Download model from Hugging Face Hub")
    parser.add_argument("--repo-id", default=DEFAULT_REPO, help="HF repo id")
    parser.add_argument(
        "--output",
        default=str(MODEL_DIR),
        help="Local folder (default: capital_llm_model/)",
    )
    args = parser.parse_args()

    from huggingface_hub import snapshot_download

    print(f"Downloading {args.repo_id} -> {args.output}")
    path = snapshot_download(
        repo_id=args.repo_id,
        local_dir=args.output,
        local_dir_use_symlinks=False,
    )
    print(f"Done: {path}")
    print('Test: python src/ask.py "what country is Paris in"')


if __name__ == "__main__":
    main()
