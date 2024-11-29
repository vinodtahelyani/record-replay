import json

temp_storage = {}

def save_temp_data(session_id: str, data: dict):
    """Save data temporarily in memory."""
    temp_storage[session_id] = data

def get_temp_data(session_id: str):
    """Retrieve temporary data."""
    return temp_storage.get(session_id)

def save_to_jsonl(file_path: str, record):
    """Save data to a JSONL file."""
    with open(file_path, "a") as f:
        f.write(json.dumps(record) + "\n")
