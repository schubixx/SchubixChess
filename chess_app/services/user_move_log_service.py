from pathlib import Path
import sqlite3
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DB = BASE_DIR / "data" / "user_moves.db"


def create_connection():
    LOG_DB.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(LOG_DB))


def init_user_move_log_db():
    conn = create_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS visualization_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lichess_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                puzzle_id TEXT,
                halfmoves INTEGER,
                entered_move TEXT,
                correct_move TEXT,
                is_correct INTEGER NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS wendepunkt_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lichess_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                task_id TEXT,
                current_move_number INTEGER,
                entered_move TEXT,
                correct_move_number INTEGER,
                correct_move TEXT,
                is_correct INTEGER NOT NULL
            )
        """)

        conn.commit()
    finally:
        conn.close()


def log_visualization_move(
    lichess_username: str,
    puzzle_id: str,
    halfmoves: int,
    entered_move: str,
    correct_move: str,
    is_correct: bool,
):
    conn = create_connection()
    try:
        conn.execute(
            """
            INSERT INTO visualization_moves (
                lichess_username,
                created_at,
                puzzle_id,
                halfmoves,
                entered_move,
                correct_move,
                is_correct
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lichess_username,
                datetime.now().isoformat(timespec="seconds"),
                puzzle_id,
                halfmoves,
                entered_move,
                correct_move,
                1 if is_correct else 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def log_wendepunkt_move(
    lichess_username: str,
    task_id: str,
    current_move_number: int,
    entered_move: str,
    correct_move_number: int,
    correct_move: str,
    is_correct: bool,
):
    conn = create_connection()
    try:
        conn.execute(
            """
            INSERT INTO wendepunkt_moves (
                lichess_username,
                created_at,
                task_id,
                current_move_number,
                entered_move,
                correct_move_number,
                correct_move,
                is_correct
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lichess_username,
                datetime.now().isoformat(timespec="seconds"),
                task_id,
                current_move_number,
                entered_move,
                correct_move_number,
                correct_move,
                1 if is_correct else 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()