"""
Fast capitals-only training on CPU or GPU.

  python src/quick_train.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]):
    print(f"\n>>> {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    print("=" * 60)
    print("  Geo Capital LLM — capitals only, GPT-2, 1 epoch")
    print("=" * 60)

    run([sys.executable, "src/build_training_data.py"])
    run([
        sys.executable,
        "src/train.py",
        "--no-wandb",
        "--model",
        "gpt2",
        "--epochs",
        "1",
    ])

    print("\n" + "=" * 60)
    print('  Done! Test: python src/ask.py "what is the capital of kerala"')
    print("=" * 60)


if __name__ == "__main__":
    main()
