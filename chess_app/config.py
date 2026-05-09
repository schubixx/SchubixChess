import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_PIECE_SET = "merida"
AVAILABLE_PIECE_SETS = ["merida", "cburnett"]

class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-change-me"
    )

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" + str(BASE_DIR / "data" / "lichess_tokens.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LICHESS_CLIENT_ID = os.getenv(
        "LICHESS_CLIENT_ID",
        ""
    )

    LICHESS_REDIRECT_URI = os.getenv(
        "LICHESS_REDIRECT_URI",
        "http://localhost:5000/auth/callback"
    )

    LICHESS_OAUTH_AUTHORIZE_URL = (
        "https://lichess.org/oauth"
    )

    LICHESS_OAUTH_TOKEN_URL = (
        "https://lichess.org/api/token"
    )

    LICHESS_ACCOUNT_URL = (
        "https://lichess.org/api/account"
    )

    LICHESS_CHALLENGE_AI_URL = "https://lichess.org/api/challenge/ai"

DEFAULT_AI_SETTINGS = {
    "level": 8,
    "clock_limit": 300,
    "clock_increment": 0,
    "color": "white",
    "variant": "standard",
}

