import json
from pathlib import Path
from config import ARTIFACTS_DIR

def get_task_dir(seq_no: str) -> Path:
    """Returns the path to the task directory."""
    return ARTIFACTS_DIR / seq_no

def create_task_state(seq_no: str, platform: str, instructions: str) -> dict:
    """Creates the initial status.json file for a new task."""
    task_dir = get_task_dir(seq_no)
    task_dir.mkdir(exist_ok=True)

    initial_state = {
        "seq_no": seq_no,
        "status": "created",
        "platform": platform,
        "instructions": instructions,
        "artifacts": {}
    }

    status_file = task_dir / "status.json"
    with status_file.open("w", encoding="utf-8") as f:
        json.dump(initial_state, f, indent=2)

    return initial_state

def get_task_state(seq_no: str) -> dict:
    """Reads and returns the content of status.json for a given task."""
    task_dir = get_task_dir(seq_no)
    status_file = task_dir / "status.json"

    if not status_file.exists():
        return None

    with status_file.open("r", encoding="utf-8") as f:
        return json.load(f)

def update_task_state(seq_no: str, new_data: dict) -> dict:
    """Updates the status.json file with new data."""
    task_dir = get_task_dir(seq_no)
    status_file = task_dir / "status.json"

    if not status_file.exists():
        raise FileNotFoundError(f"Status file for task {seq_no} not found.")

    with status_file.open("r+", encoding="utf-8") as f:
        current_state = json.load(f)
        current_state.update(new_data)
        f.seek(0)
        json.dump(current_state, f, indent=2)
        f.truncate()

    return current_state
