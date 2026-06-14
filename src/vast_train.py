"""
One command for Vast.ai GPU training (GPT-2, fp16, batch 32).

  python src/vast_train.py              # capitals-only (~20k), ~2 min on RTX 5090
  python src/vast_train.py --full       # full 287k dataset, ~10 min
  python src/vast_train.py --epochs 3   # capitals, 3 epochs for better recall
"""

import subprocess
import sys
from pathlib import Path

from config import DEFAULT_MODEL, PROJECT_ROOT

MODELS_DIR = PROJECT_ROOT / "models"
LOCAL_GPT2 = MODELS_DIR / "gpt2"


def run(cmd: list[str]):
    print(f"\n>>> {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)


def resolve_base_model() -> str:
    if LOCAL_GPT2.joinpath("config.json").exists():
        return str(LOCAL_GPT2)
    return DEFAULT_MODEL


def main():
    full = "--full" in sys.argv
    skip_data = "--skip-data" in sys.argv
    extra = [a for a in sys.argv[1:] if a not in {"--full", "--skip-data"}]

    print("=" * 60)
    print("  Vast.ai GPU training — GPT-2 + fp16 + batch 32")
    print("=" * 60)

    run([sys.executable, "src/download_base_model.py", "--model", "gpt2"])

    if not skip_data:
        if full:
            run([sys.executable, "src/build_training_data.py", "--full"])
        else:
            run([sys.executable, "src/build_training_data.py"])

    cmd = [
        sys.executable,
        "src/train.py",
        "--no-wandb",
        "--model",
        resolve_base_model(),
        "--batch-size",
        "32",
        "--epochs",
        "1",
    ]
    if full:
        cmd.append("--full-data")
    cmd.extend(extra)

    run(cmd)

    print("\n" + "=" * 60)
    print("  Done! Download model then test:")
    print('  python src/ask.py "what is the capital of kerala"')
    print("  scp -r root@HOST:/workspace/capital_llm_model ./capital_llm_model")
    print("=" * 60)


if __name__ == "__main__":
    main()
