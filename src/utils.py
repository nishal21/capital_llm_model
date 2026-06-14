from pathlib import Path


def load_data(file_path):
    import json

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def format_response(data):
    if isinstance(data, dict):
        return "\n".join(f"{key}: {value}" for key, value in data.items())
    return str(data)
