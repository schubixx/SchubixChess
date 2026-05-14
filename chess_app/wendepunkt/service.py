from pathlib import Path
import random
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[1]
WENDEPUNKT_DB = BASE_DIR / "data" / "wendepunkt.db"


class WendepunktService:
    @staticmethod
    def create_connection():
        return sqlite3.connect(str(WENDEPUNKT_DB))

    def hole_aufgabe(self, rating: int):
        min_rating = rating - 100
        max_rating = rating + 100

        conn = self.create_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    task_id,
                    game,
                    WhiteElo,
                    Event,
                    Site,
                    White,
                    Black,
                    WhiteElo,
                    BlackElo
                FROM games
                WHERE WhiteElo >= ? AND WhiteElo < ?
                """,
                (min_rating, max_rating),
            )

            rows = cursor.fetchall()

            if not rows:
                return None

            return random.choice(rows)

        finally:
            conn.close()

    def hole_aufgabe_by_task_id(self, task_id: str):
        conn = self.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    TASK_ID,
                    GAME,
                    Event,
                    Site,
                    White,
                    Black,
                    WhiteElo,
                    BlackElo
                FROM games
                WHERE TASK_ID = ?
                """,
                (task_id,),
            )
            return cursor.fetchone()
        finally:
            conn.close()

