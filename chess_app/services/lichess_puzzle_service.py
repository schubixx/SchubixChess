
from http.client import ImproperConnectionState
import random
from pathlib import Path
import sqlite3
import chess.pgn
import requests
import io
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Tuple, List, Union
from ..LichessEnums import Thema, Laenge, THEMA_NAMEN, LAENGE_NAMEN   


BASE_DIR = Path(__file__).resolve().parents[1]

PUZZLE_DB = (
    BASE_DIR / "data" / "puzzles_small.db"
)

@dataclass
class LichessAufgabe:
    game_id: str
    puzzle_id: str
    fen: str # FEN-String der Lichess-Aufgabe (Zug vor Ausgangsstellung)
    fen_start: str # FEN-String der Ausgangsstellung (erster Zug ausgeführt)
    pgn_komplett: str # PGN-String der kompletten Partie (nur bei Visualisierungsaufgaben)
    solution: str
    halfmove: int
    schwarz_am_zug: bool
    rating: int


class LichessPuzzleService:
    def __init__(self, themen_nummer: Optional[Union[Thema, int]] = None, laenge: Optional[Union[Laenge, int]] = None,
                 min_rating: Optional[int] = None, max_rating: Optional[int] = None):
        self.themen_nummer = int(themen_nummer) if themen_nummer is not None else 0
        self.laenge = int(laenge) if laenge is not None else 0
        self.min_rating = min_rating if min_rating is not None else 0
        self.max_rating = max_rating if max_rating is not None else 3000

    def zufallszahl(self, anzahl: int) -> int:
        """Zufallszahl zwischen 0 und anzahl - 1."""
        if anzahl <= 0:
            raise ValueError("anzahl muss größer als 0 sein")
        return random.randrange(anzahl)

    def sql_filter_lichess(
        self,
        min_rating: int,
        max_rating: int,
        themen_nummer: Optional[Union[Thema, int]] = None,
        laenge: Optional[int] = None,
    ) -> Tuple[str, List[int]]:
        """
        Baut den SQL-Filter für Lichess-Puzzles.
        Gibt (sql_filter, params) zurück.
        """
        if themen_nummer is None:
            themen_nummer = self.themen_nummer
        else:
            themen_nummer = int(themen_nummer)

        if laenge is None:
            laenge = self.laenge

        sql_filter = " FROM puzzles p WHERE rating >= ? AND rating < ?"
        params: List[int] = [min_rating, max_rating]

        if themen_nummer > 0:
            sql_filter += " AND theme = ?"
            params.append(themen_nummer)

        if laenge > 0:
            sql_filter += " AND length = ?"
            params.append(laenge)

        # sql_filter += " AND p.id IN (SELECT puzzleId FROM length WHERE length <= 2)"

        return sql_filter, params

    def partien_von_lichess_holen(self,list_of_game_ids: str) -> str:
        url = "https://lichess.org/api/games/export/_ids"

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            url,
            data=list_of_game_ids.encode("utf-8"),
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        return(response.content.decode("utf-8"))

    def get_anzahl_aufgaben(
        self,
        conn: sqlite3.Connection,
        sql_filter: str,
        params: List[int],
    ) -> int:
        """Entspricht GetAnzahlAufgaben aus dem VB-Code."""
        sql = "SELECT count(*) AS Anzahl" + sql_filter

        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return row[0] if row else 0
        finally:
            cursor.close()

    def hole_aufgabe_aus_lichess(
        self,
        conn: sqlite3.Connection,
        anzahlZuegeVisualisierung: Optional[int] = 0,
    ) -> Optional[LichessAufgabe]:
        """
        Lädt eine zufällige passende Aufgabe aus der Datenbank.
        Gibt None zurück, wenn keine Aufgabe gefunden wurde.
        """
        sql_filter, params = self.sql_filter_lichess(self.min_rating, self.max_rating)
        anzahl_aufgaben = self.get_anzahl_aufgaben(conn, sql_filter, params)

        if anzahl_aufgaben == 0:
            return None

        offset = self.zufallszahl(anzahl_aufgaben)

        sql = (
            "SELECT gameId, id, FEN, solution, halfmove, rating"
            + sql_filter
            + " LIMIT ?, 1;"
        )

        cursor = conn.cursor()
        try:
            cursor.execute(sql, params + [offset])
            row = cursor.fetchone()

            if not row:
                return None

            game_id, puzzle_id, fen, solution, halfmove, rating = row

            zuege = solution.split()
            erster_zug = zuege[0]

            if anzahlZuegeVisualisierung>0 :
                partie=self.partien_von_lichess_holen(list_of_game_ids=game_id)
                pgn_io = io.StringIO(partie)
                # print(partie)
                game = chess.pgn.read_game(pgn_io)
                board=game.board()
                halbzug=0
                for zug in game.mainline_moves():
                    halbzug+=1
                    board.push(zug)
                    differenz = (halbzug - halfmove+anzahlZuegeVisualisierung-1)
                    if differenz==0:
                        # print(board.fen())
                        boardVisualisierung=chess.Board(board.fen())
                        gameVisualisierung=chess.pgn.Game()
                        gameVisualisierung.setup(boardVisualisierung)
                        gameVisualisierung.headers["Event"]="Visualisierungsaufgabe"
                        gameVisualisierung.headers["Site"]="https://lichess.org/training/"+puzzle_id
                        gameVisualisierung.headers["WhiteELo"]=str(rating)
                        gameVisualisierung.headers["BlackELo"]=str(rating)
                        gameVisualisierung.headers["PuzzleId"] = puzzle_id
                        gameVisualisierung.headers["Source"] = "Lichess"
                    elif differenz==1:
                        boardVisualisierung.push(zug)
                        node=gameVisualisierung.add_variation(zug)
                        #print(boardVisualisierung)
                    elif differenz>0 and differenz<=anzahlZuegeVisualisierung:
                        boardVisualisierung.push(zug)
                        node=node.add_variation(zug)
                        # print(boardVisualisierung)
                    #if halbzug == halfmove-anzahlZuegeVisualisierung+1:
                        #for i in range(1, anzahlZuegeVisualisierung):
                        #print(fen)
                node.add_variation(chess.Move.null())
                for zug in zuege:
                    if zug != erster_zug:
                        node=node.add_variation(chess.Move.from_uci(zug))
                # print(str(gameVisualisierung))
                return LichessAufgabe(
                    game_id=game_id,
                    puzzle_id=puzzle_id,
                    fen=fen,
                    fen_start=board.fen(),
                    solution=solution,
                    pgn_komplett=str(gameVisualisierung),
                    halfmove=halfmove,
                    schwarz_am_zug=(halfmove % 2 == 0),
                    rating=rating,)
            else:
                board=chess.Board(fen)
                board.push_uci(erster_zug)
                return LichessAufgabe(
                    game_id=game_id,
                    puzzle_id=puzzle_id,
                    fen=fen,
                    fen_start=board.fen(),
                    solution=solution,
                    halfmove=halfmove,
                    schwarz_am_zug=(halfmove % 2 == 0),
                    rating=rating,
            )
        finally:
            cursor.close()


    def thema_name(self) -> Optional[str]:
        """Liefert den Anzeigenamen des aktuell gesetzten Themas."""
        if self.themen_nummer <= 0:
            return None
        try:
            return THEMA_NAMEN[Thema(self.themen_nummer)]
        except ValueError:
            return f"Unbekanntes Thema ({self.themen_nummer})"

    @staticmethod
    def create_connection():    
        return sqlite3.connect(str(PUZZLE_DB))


if __name__ == "__main__":
    # Beispielverwendung:
    conn = LichessPuzzleService.create_connection("puzzles_small.db")

    service = LichessPuzzleService(
        themen_nummer=Thema.GABEL,
        laenge=2,
    )

    aufgabe = service.hole_aufgabe_aus_lichess(
        conn=conn,
        min_rating=1200,
        max_rating=1600,
    )

    if aufgabe is None:
        print("Keine passende Aufgabe gefunden.")
    else:
        print("Thema:", service.thema_name())
        print("Puzzle-ID:", aufgabe.puzzle_id)
        print("Game-ID:", aufgabe.game_id)
        print("FEN:", aufgabe.fen)
        print("Loesung:", aufgabe.solution)
        print("Halfmove:", aufgabe.halfmove)
        print("Schwarz am Zug:", aufgabe.schwarz_am_zug)
        print("Rating:", aufgabe.rating)

    conn.close()
