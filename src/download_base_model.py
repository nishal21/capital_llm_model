"""
Download base model to local disk (fixes Vast.ai DNS / HF timeout issues).

  python src/download_base_model.py
  python src/download_base_model.py --model gpt2-medium
"""

import argparse
import socket
import time
from pathlib import Path

from config import DEFAULT_MODEL, PROJECT_ROOT

MODELS_DIR = PROJECT_ROOT / "models"


def check_dns(host: str = "huggingface.co") -> bool:
    try:
        socket.getaddrinfo(host, 443)
        return True
    except socket.gaierror:
        return False


def download(model_id: str, retries: int = 5) -> Path:
    local_dir = MODELS_DIR / model_id.replace("/", "_")
    if (local_dir / "config.json").exists():
        print(f"Already cached at {local_dir}")
        return local_dir

    if not check_dns():
        print(
            "DNS cannot resolve huggingface.co. Fix on Vast.ai:\n"
            '  echo "nameserver 8.8.8.8" > /etc/resolv.conf\n'
            '  echo "nameserver 1.1.1.1" >> /etc/resolv.conf\n'
            "  ping -c 2 huggingface.co\n"
        )

    from huggingface_hub import snapshot_download

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            print(f"Downloading {model_id} → {local_dir} (attempt {attempt}/{retries})")
            snapshot_download(
                repo_id=model_id,
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
            )
            print(f"Saved to {local_dir}")
            return local_dir
        except Exception as exc:
            last_err = exc
            wait = min(2**attempt, 30)
            print(f"Failed: {exc}\nRetrying in {wait}s...")
            time.sleep(wait)

    raise SystemExit(f"Could not download {model_id}: {last_err}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--retries", type=int, default=5)
    args = parser.parse_args()
    path = download(args.model, retries=args.retries)
    print(f"\nUse in training:\n  python src/train.py --model {path} ...")


if __name__ == "__main__":
    main()
