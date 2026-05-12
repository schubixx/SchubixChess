import base64
import hashlib
import os
import time
import random
import string
from datetime import datetime, timezone
from typing import Optional

from flask import request, session

from .models import Position, LichessToken
import secrets

DEFAULT_COLLECTION = "A13d45xZ"

MERIDA_MAP = {
    "K": "k",  # weißer König
    "Q": "q",
    "R": "r",
    "B": "b",
    "N": "n",
    "P": "p",
    "k": "l",  # schwarzer König
    "q": "w",
    "r": "t",
    "b": "v",
    "n": "m",
    "p": "o",
}

SVG_PIECE_MAP = {
    "K": "wK.svg",
    "Q": "wQ.svg",
    "R": "wR.svg",
    "B": "wB.svg",
    "N": "wN.svg",
    "P": "wP.svg",
    "k": "bK.svg",
    "q": "bQ.svg",
    "r": "bR.svg",
    "b": "bB.svg",
    "n": "bN.svg",
    "p": "bP.svg",
}

def generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")


def generate_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")

def is_admin():
    user_id = session.get("lichess_user_id")
    if not user_id:
        return False

    user = LichessToken.query.filter_by(lichess_user_id=user_id).first()
    return user and user.admin

def generate_collection_id():
    # timestamp = int(time.time() * 1000)
    # random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    # return f"{timestamp}{random_part}"
    return snowflake44()

def store_collection_from_request() -> Optional[str]:
    """Speichert den optionalen GET-Parameter COLLECTION in der Session.

    Wird bei jedem Request aufgerufen. Sobald ?COLLECTION=<wert> vorhanden ist,
    wird der Wert in der Session aktualisiert. Ohne Parameter bleibt der
    vorhandene Session-Wert unveraendert."""

    collection = request.args.get("COLLECTION", type=str)
    if collection:
        session["collection"] = collection.strip()
    if "COLLECTION" not in session:
        session["COLLECTION"] = DEFAULT_COLLECTION
    return session.get("collection")


def get_current_collection() -> Optional[str]:
    """Liefert die aktuelle Collection."""

    collection = session.get("collection")

    if not collection:
        collection = DEFAULT_COLLECTION
        session["collection"] = collection

    return collection

def get_positions_for_current_collection():
    collection = get_current_collection()
    if not collection:
        return []

    return (
        Position.query
        .filter_by(collection_id=collection)
        .order_by(Position.id)
        .all()
    )

def _ticks(dt: datetime) -> int:
    dt = dt.astimezone(timezone.utc)
    YEAR1 = datetime(1, 1, 1, tzinfo=timezone.utc)
    delta = dt - YEAR1
    return delta.days * 864_000_000_000 + delta.seconds * 10_000_000 + delta.microseconds * 10


def to_44bit_salted(dt: datetime) -> int:
    global _previous_time_frame

    _randoms_of_previous_time_frame = set()
    _random_generator = random.Random()
    CENTURY_BEGIN = datetime(1900, 1, 1, tzinfo=timezone.utc)
    dt_ticks = _ticks(dt)

    elapsed_milliseconds = dt_ticks // 10_000 - _ticks(CENTURY_BEGIN) // 10_000

    elapsed_milliseconds <<= 19

    while True:
        rv = _random_generator.randrange(524_287)
        if rv not in _randoms_of_previous_time_frame:
            _randoms_of_previous_time_frame.add(rv)
            break

    _previous_time_frame = dt_ticks
    return elapsed_milliseconds | rv

def uid_to_base64_urlsafe(uid: int) -> str:
    b = uid.to_bytes(8, byteorder="big", signed=False)
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def base64_urlsafe_to_uid(b64: str) -> int:
    padding = "=" * (-len(b64) % 4)
    b = base64.urlsafe_b64decode(b64 + padding)
    return int.from_bytes(b, byteorder="big", signed=False)


def snowflake44() -> str:
    return uid_to_base64_urlsafe(to_44bit_salted(datetime.now(timezone.utc)))

def fen_to_board_merida(fen):
    if not fen:
        return []

    board_part = fen.split()[0]
    rows = []

    for row_index, fen_row in enumerate(board_part.split("/")):
        row = []
        col_index = 0

        for char in fen_row:
            if char.isdigit():
                for _ in range(int(char)):
                    row.append({
                        "piece": "",
                        "color": "light" if (row_index + col_index) % 2 == 0 else "dark"
                    })
                    col_index += 1
            else:
                row.append({
                    "piece": MERIDA_MAP.get(char, ""),
                    "color": "light" if (row_index + col_index) % 2 == 0 else "dark"
                })
                col_index += 1

        rows.append(row)

    return rows

def fen_to_board(fen):
    if not fen:
        return []

    board_part = fen.split()[0]
    rows = []

    for row_index, fen_row in enumerate(board_part.split("/")):
        row = []
        col_index = 0

        for char in fen_row:
            if char.isdigit():
                for _ in range(int(char)):
                    row.append({
                        "piece": None,
                        "color": "light" if (row_index + col_index) % 2 == 0 else "dark"
                    })
                    col_index += 1
            else:
                row.append({
                    "piece": SVG_PIECE_MAP.get(char),
                    "color": "light" if (row_index + col_index) % 2 == 0 else "dark"
                })
                col_index += 1

        rows.append(row)

    return rows