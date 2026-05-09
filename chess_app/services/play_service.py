import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

PLAY_CONFIG_DIR = (
    BASE_DIR / "data" / "play_configs"
)


def load_play_configuration(
    config_id=None
):
    if config_id:
        path = (
            PLAY_CONFIG_DIR /
            f"{config_id}.json"
        )
    else:
        path = (
            PLAY_CONFIG_DIR /
            "default.json"
        )

    if not path.exists():
        raise FileNotFoundError(
            f"Konfiguration nicht gefunden: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)
