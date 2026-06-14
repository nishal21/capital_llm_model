"""
Convert capital_llm_model/ (GPT-2 safetensors) to GGUF for Ollama.

Prerequisites:
  git clone https://github.com/ggerganov/llama.cpp
  pip install -r llama.cpp/requirements.txt

Usage:
  python src/convert_for_ollama.py
  python src/convert_for_ollama.py --llama-cpp ../llama.cpp
"""

import argparse
import subprocess
import sys
from pathlib import Path

from config import MODEL_DIR, PROJECT_ROOT

GGUF_OUT = PROJECT_ROOT / "capital_llm_model.gguf"
DEFAULT_LLAMA_CPP = PROJECT_ROOT / "llama.cpp"


def main():
    parser = argparse.ArgumentParser(description="Convert fine-tuned GPT-2 to GGUF for Ollama")
    parser.add_argument("--llama-cpp", type=Path, default=DEFAULT_LLAMA_CPP)
    parser.add_argument("--outfile", type=Path, default=GGUF_OUT)
    parser.add_argument("--outtype", default="f16", choices=["f16", "f32", "q8_0"])
    args = parser.parse_args()

    convert_script = args.llama_cpp / "convert_hf_to_gguf.py"
    if not convert_script.exists():
        print("llama.cpp not found. Clone it next to this project:")
        print(f"  cd {PROJECT_ROOT.parent}")
        print("  git clone https://github.com/ggerganov/llama.cpp")
        print("  pip install -r llama.cpp/requirements.txt")
        sys.exit(1)

    if not (MODEL_DIR / "config.json").exists():
        print(f"Model not found at {MODEL_DIR}")
        print("  python src/download_hf_model.py")
        sys.exit(1)

    cmd = [
        sys.executable,
        str(convert_script),
        str(MODEL_DIR),
        "--outfile",
        str(args.outfile),
        "--outtype",
        args.outtype,
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    print(f"\nGGUF saved: {args.outfile}")
    print("\nNext (Ollama must be installed):")
    print("  ollama create nishal21/geo-capital-llm -f Modelfile.ollama")
    print("  ollama push nishal21/geo-capital-llm")
    print("\nSee OLLAMA.md for SSH key setup on ollama.com")


if __name__ == "__main__":
    main()
