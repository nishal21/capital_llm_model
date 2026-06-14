from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_ROOT = (
    PROJECT_ROOT
    / "countries-states-cities-database-master"
    / "countries-states-cities-database-master"
    / "json"
)

# Base model: gpt2 (124M) — better than distilgpt2; use gpt2-medium for quality (slower)
DEFAULT_MODEL = "gpt2"
MODEL_DIR = PROJECT_ROOT / "capital_llm_model"
TRAINING_PATH = PROJECT_ROOT / "data" / "training.jsonl"
