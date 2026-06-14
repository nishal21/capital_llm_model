"""
Train on ALL dataset examples (countries, states, cities, capitals) — 1 epoch only.

  python src/full_train.py

~280k examples, 1 epoch, batch 8 → ~30-40 hours on CPU (vs 9 days for 3 epochs).
Stop any running training first (Ctrl+C).
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
    print("  Geo LLM — FULL dataset, 1 epoch")
    print("  ~287k examples | ~36k steps | ~30-40 hrs on CPU")
    print("  (3x faster than your previous 3-epoch run)")
    print("=" * 60)

    run([sys.executable, "src/build_training_data.py", "--full"])
    run([
        sys.executable,
        "src/train.py",
        "--full-data",
        "--no-wandb",
        "--epochs",
        "1",
        "--batch-size",
        "8",
        "--model",
        "distilgpt2",
    ])

    print("\n" + "=" * 60)
    print("  Done! Test with:")
    print('  python src/ask.py "what is the capital of kerala"')
    print('  python src/ask.py "what country is Paris in"')
    print("=" * 60)


if __name__ == "__main__":
    main()
