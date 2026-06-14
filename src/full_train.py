"""
Train on ALL dataset examples — 1 epoch.

  python src/full_train.py          # CPU ~30-40 hrs
  python src/vast_train.py --full   # GPU ~10 min on RTX 5090
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
    print("  Geo LLM — FULL dataset, GPT-2, 1 epoch")
    print("  On GPU use: python src/vast_train.py --full")
    print("=" * 60)

    run([sys.executable, "src/build_training_data.py", "--full"])
    run([
        sys.executable,
        "src/train.py",
        "--full-data",
        "--no-wandb",
        "--epochs",
        "1",
        "--model",
        "gpt2",
    ])

    print("\n" + "=" * 60)
    print('  Done! Test: python src/ask.py "what country is Paris in"')
    print("=" * 60)


if __name__ == "__main__":
    main()
