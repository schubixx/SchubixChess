import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

TASK_DIR = (
    BASE_DIR / "data" / "visualization_tasks"
)


def load_visualization_tasks():
    tasks = []

    for path in TASK_DIR.glob("*.json"):
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            tasks.append(json.load(f))

    return tasks
