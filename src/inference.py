from pathlib import Path

from config import MODEL_DIR, PROJECT_ROOT
from normalize import extract_capital_question, normalize_question, to_training_prompt

_MODEL = None
_TOKENIZER = None


def resolve_model_dir() -> Path | None:
    """Find fine-tuned model directory (supports nested save paths)."""
    candidates = [
        MODEL_DIR,
        MODEL_DIR / "capital_llm_model",
        PROJECT_ROOT / "capital_llm_model",
    ]
    for path in candidates:
        if (path / "config.json").exists() and (
            (path / "model.safetensors").exists()
            or (path / "pytorch_model.bin").exists()
            or any(path.glob("*.safetensors"))
        ):
            return path
    return None


def load_model(model_dir: Path | None = None):
    global _MODEL, _TOKENIZER
    from transformers import AutoModelForCausalLM, AutoTokenizer

    path = model_dir or resolve_model_dir()
    if path is None:
        raise FileNotFoundError(
            f"No trained model found under {PROJECT_ROOT / 'capital_llm_model'}. "
            "Run: python src/quick_train.py or python src/train.py"
        )

    if _MODEL is None or _TOKENIZER is None:
        _TOKENIZER = AutoTokenizer.from_pretrained(path)
        _MODEL = AutoModelForCausalLM.from_pretrained(path)
    return _TOKENIZER, _MODEL


def generate_answer(question: str, model_dir: Path | None = None) -> str:
    tokenizer, model = load_model(model_dir)
    prompt = to_training_prompt(question)
    inputs = tokenizer(prompt, return_tensors="pt")

    outputs = model.generate(
        inputs["input_ids"],
        attention_mask=inputs.get("attention_mask"),
        max_new_tokens=40,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    full_text = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    if "Answer:" in full_text:
        answer = full_text.split("Answer:", 1)[1].strip()
        if answer:
            return answer.rstrip(".")
    return full_text


def answer_capital(place: str, model_dir: Path | None = None) -> str:
    place = normalize_question(place)
    question = f"What is the capital of {place}?"
    answer = generate_answer(question, model_dir)
    if answer.lower().startswith("the capital of"):
        return answer
    return f"The capital of {place} is {answer.rstrip('.')}."


def answer_question(question: str, model_dir: Path | None = None) -> str:
    question = normalize_question(question)
    place = extract_capital_question(question)
    if place:
        return answer_capital(place, model_dir)
    return generate_answer(question, model_dir)
