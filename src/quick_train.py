"""
One-command fast training (~1-3 hours on CPU, not 9 days).

  python src/quick_train.py

Does:
  1. Build capitals-only training data (~10k examples)
  2. Train DistilGPT-2 for 1 epoch
  3. Save to capital_llm_model/
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
    print("  Geo Capital LLM — fast training (capitals only, 1 epoch)")
    print("  Expected time: ~1-3 hours on CPU")
    print("=" * 60)

    run([sys.executable, "src/build_training_data.py"])
    run([
        sys.executable,
        "src/train.py",
        "--no-wandb",
        "--model",
        "distilgpt2",
        "--epochs",
        "1",
        "--batch-size",
        "8",
    ])

    print("\n" + "=" * 60)
    print("  Done! Test with:")
    print('  python src/ask.py "what is the capital of kerala"')
    print("=" * 60)


if __name__ == "__main__":
    main()
