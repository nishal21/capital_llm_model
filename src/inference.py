from pathlib import Path

from config import PROJECT_ROOT
from normalize import extract_capital_question, normalize_question, to_training_prompt

MODEL_DIR = PROJECT_ROOT / "capital_llm_model"


def load_model(model_dir: Path | None = None):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    path = model_dir or MODEL_DIR
    if not (path / "config.json").exists():
        raise FileNotFoundError(
            f"Model not found at {path}. Run: python src/build_training_data.py && python src/train.py"
        )

    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForCausalLM.from_pretrained(path)
    return tokenizer, model


def generate_answer(question: str, model_dir: Path | None = None) -> str:
    tokenizer, model = load_model(model_dir)
    prompt = to_training_prompt(question)
    inputs = tokenizer(prompt, return_tensors="pt")

    outputs = model.generate(
        inputs["input_ids"],
        attention_mask=inputs.get("attention_mask"),
        max_new_tokens=35,
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
