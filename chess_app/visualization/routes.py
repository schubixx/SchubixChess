from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

import chess
import chess.pgn
import sqlite3
import random
from ..services.lichess_puzzle_service import LichessPuzzleService
from ..LichessEnums import Thema, Laenge, THEMA_NAMEN, LAENGE_NAMEN
from .parameter_codec import (encode_visualization_parameter,decode_visualization_parameter,)
from flask import Blueprint, jsonify, render_template, request, Response, session
from datetime import datetime


'''
aber ich würde board und current_task künftig klar trennen:
board = aktuelle interaktive Stellung
current_task = geladene Aufgabe
6. Doppelte/alte Hilfsfunktionen in app.py

Du hast sowohl in TaskState:

_load_game
_get_start_fen
_format_mainline
_format_with_variations
_build_navigation

als auch darunter nochmal:

load_game_from_pgn
get_start_fen
get_mainline_data
format_with_variations

Diese freien Funktionen werden aktuell gar nicht mehr genutzt.

Folge: unnötige Verwirrung, höheres Fehlerrisiko.

Fix: löschen, wenn du sie nicht mehr brauchst.
'''

visualization_bp = Blueprint("visualization", __name__, url_prefix="/visualisierung")

class TaskState:

    def _items_to_text(self, items):
        return " ".join(
            item["text"] if isinstance(item, dict) else item
            for item in items
        )

    def __init__(self, pgn_text: str):
        self.pgn = pgn_text

        # PGN parsen
        game = self._load_game(pgn_text)

        # Startstellung
        self.start_fen = self._get_start_fen(game)
        self.first_move_uci = self._get_first_move_uci(game)

        # Notationen
        self.mainline_text = self._format_mainline(game)
        self.solution_text = self._format_with_variations(game)

        # Navigation
        self.navigation_fens, self.navigation_sans = self._build_navigation(game)

        # Steuerung, ob die Lösung schon angezeigt wird oder nicht
        self.user_has_answered = False

        self.history_items = self._build_history_items(game)
        self.mainline_text = " ".join(self.history_items)

        self.solution_items = self._build_solution_items(game)
        self.solution_text = self._items_to_text(self.solution_items)

    # -------------------------
    # PGN laden
    # -------------------------
    def _load_game(self, pgn_text):
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        if game is None:
            raise ValueError("PGN konnte nicht gelesen werden.")
        return game

    # -------------------------
    # ersten Zug der Lösung ermitteln
    # -------------------------
    def _get_first_move_uci(self, game):
        node = game
        while node.variations:
            # Gibt es an dieser Stelle eine Nebenvariante?
            if len(node.variations) > 1:
                side_move = node.variations[1].move
                return side_move.uci()

            # Sonst weiter entlang der Hauptvariante suchen
            node = node.variation(0)
        return None

    # -------------------------
    # Startstellung bestimmen
    # -------------------------
    def _get_start_fen(self, game):
        fen = game.headers.get("FEN")
        return fen if fen else chess.STARTING_FEN

    # -------------------------
    # Hauptvariante (ohne Varianten)
    # -------------------------
    def _format_mainline(self, game):
        board = game.board()
        node = game

        parts = []
        first_move = True

        while node.variations:
            next_node = node.variation(0)
            move = next_node.move

            san = self._san_to_german(board.san(move))

            if board.turn == chess.WHITE:
                parts.append(f"{board.fullmove_number}. {san}")
            else:
                if first_move:
                    parts.append(f"{board.fullmove_number}... {san}")
                else:
                    parts.append(san)

            board.push(move)
            node = next_node
            first_move = False

        return " ".join(parts)

    def _san_to_german(self, san: str) -> str:
        replacements = {
            "Q": "D",
            "R": "T",
            "B": "L",
            "N": "S",
        }

        result = san
        for english, german in replacements.items():
            result = result.replace(english, german)

        return result

    def _build_history_items(self, game):
        board = game.board()
        node = game
        items = []
        first_move = True
        while node.variations:
            next_node = node.variation(0)
            move = next_node.move
            # Nullzug nicht anzeigen
            if move == chess.Move.null():
                break

            san = self._san_to_german(board.san(move))

            if board.turn == chess.WHITE:
                text = f"{board.fullmove_number}. {san}"
            else:
                if first_move:
                    text = f"{board.fullmove_number}... {san}"
                else:
                    text = san

            items.append(text)

            board.push(move)
            node = next_node
            first_move = False

        return items

    def _build_solution_items(self, game):
        board = game.board()
        node = game
        items = []
        first_move = True

        while node.variations:
            main_node = node.variation(0)
            move = main_node.move

            # Wenn Hauptvariante am Ende einen Nullzug enthält,
            # stattdessen die Nebenvariante als Lösung übernehmen
            if move == chess.Move.null() and len(node.variations) > 1:
                variation_node = node.variation(1)
                items.append({"type": "marker", "text": "Lösung:"})

                while variation_node:
                    move = variation_node.move
                    san = self._san_to_german(board.san(move))

                    if board.turn == chess.WHITE:
                        text = f"{board.fullmove_number}. {san}"
                    else:
                        if first_move:
                            text = f"{board.fullmove_number}... {san}"
                        else:
                            text = san

                    items.append(text)

                    board.push(move)

                    if variation_node.variations:
                        variation_node = variation_node.variation(0)
                    else:
                        variation_node = None

                    first_move = False

                break

            # Normale Hauptvariante bis zum Nullzug
            if move != chess.Move.null():
                san = self._san_to_german(board.san(move))

                if board.turn == chess.WHITE:
                    text = f"{board.fullmove_number}. {san}"
                else:
                    if first_move:
                        text = f"{board.fullmove_number}... {san}"
                    else:
                        text = san

                items.append(text)
                board.push(move)

            node = main_node
            first_move = False

        return items

    # -------------------------
    # Variante mit Klammern
    # -------------------------
    def _format_with_variations(self, game):
        board = game.board()

        def recurse(node, board):
            result = []

            for index, variation in enumerate(node.variations):
                move = variation.move

                prefix = f"{board.fullmove_number}. " if board.turn == chess.WHITE else f"{board.fullmove_number}... "
                san = board.san(move)

                if index == 0:
                    result.append(prefix + san)
                    board.push(move)
                    result.extend(recurse(variation, board))
                    board.pop()
                else:
                    board.push(move)
                    inner = recurse(variation, board)
                    board.pop()

                    variation_text = prefix + san
                    if inner:
                        variation_text += " " + " ".join(inner)

                    result.append(f"({variation_text})")

            return result

        return " ".join(recurse(game, board))

    # -------------------------
    # -------------------------
    # Navigation aufbauen
    # -------------------------
    def _build_navigation(self, game):
        board = game.board()
        node = game
        fens = [board.fen()]
        sans = []
        while node.variations:
            main_node = node.variation(0)
            move = main_node.move

            # Wenn der Hauptzug ein Nullzug ist und es eine Nebenvariante gibt:
            # nicht den Nullzug übernehmen, sondern die Nebenvariante nachspielen.
            if move == chess.Move.null() and len(node.variations) > 1:
                variation_node = node.variation(1)

                while variation_node is not None:
                    move = variation_node.move
                    san = board.san(move)
                    sans.append(self._san_to_german(san))
                    board.push(move)
                    fens.append(board.fen())
                    if variation_node.variations:
                        variation_node = variation_node.variation(0)
                    else:
                        variation_node = None

                break

            # normaler Hauptvarianten-Zug
            san = board.san(move)
            sans.append(self._san_to_german(san))
            board.push(move)
            fens.append(board.fen())
            node = main_node

        return fens, sans

    # -------------------------
    # Für JSON-Ausgabe (optional)
    # -------------------------
    def to_dict(self):
        return {
            "fen": self.start_fen,
            "history": self.mainline_text,
            "history_items": self.history_items,
            "navigation_fens": self.navigation_fens,
            "navigation_sans": self.navigation_sans,
            "first_move_uci": self.first_move_uci,
        }

    def solution_dict(self):
        return {
            "history": self.solution_text,
            "history_items": self.solution_items,
            "navigation_fens": self.navigation_fens,
            "navigation_sans": self.navigation_sans,
        }

board = chess.Board()
current_task = None

def get_session_state():
    return {
        "task_loaded": session.get("task_loaded", False),
        "user_has_answered": session.get("user_has_answered", False),
        "solution_shown": session.get("solution_shown", False),
    }


def generate_task_pgn(number1, number2, select1, select2) -> str:
    """
    Beispielimplementierung.
    Hier kannst du später deine echte Logik verwenden.
    Die 4 Parameter kommen direkt aus der Oberfläche.
    """

    print("generate_task_pgn aufgerufen mit:")
    print("number1 =", number1)
    print("number2 =", number2)
    print("select1 =", select1)
    print("select2 =", select2)
    conn = LichessPuzzleService.create_connection()
    try:
        service = LichessPuzzleService(
            themen_nummer=select1,
            laenge=select2,
            min_rating=number2-100,
            max_rating=number2+100
        )
        aufgabe = service.hole_aufgabe_aus_lichess(
            conn=conn,anzahlZuegeVisualisierung=number1
        )
        if aufgabe is None:
            return """[Event \"Taktikaufgabe\"]
                [Site \"?\"]
                [Date \"2026.04.15\"]
                [Round \"?\"]
                [White \"Weiß\"]
                [Black \"Schwarz\"]
                [Result \"*\"]
                [SetUp \"1\"]
                [FEN \"r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 2 3\"]

                3... Nf6 4. d3 (4. Ng5 d5 5. exd5 Na5) 4... Be7 5. O-O O-O *
                """
        else:
            return aufgabe.pgn_komplett
    finally:
        conn.close()

def create_task_from_values(number1, number2, select1, select2):
    global current_task, board

    pgn_text = generate_task_pgn(
        number1,
        number2,
        select1,
        select2,
    )

    current_task = TaskState(pgn_text)

    session["pgn"] = pgn_text
    session["task_loaded"] = True
    session["user_has_answered"] = False
    session["solution_shown"] = False

    session["selected_number1"] = number1
    session["selected_number2"] = number2
    session["selected_thema"] = select1
    session["selected_laenge"] = select2

    session.modified = True

    board = chess.Board(current_task.start_fen)

    return current_task

def load_game_from_pgn(pgn_text: str) -> chess.pgn.Game:
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        raise ValueError("PGN konnte nicht gelesen werden.")
    return game


def get_start_fen(game: chess.pgn.Game) -> str:
    return game.headers.get("FEN") or chess.STARTING_FEN


def get_mainline_data(game: chess.pgn.Game) -> tuple[str, list[str], list[str]]:
    temp_board = game.board()
    node: chess.pgn.GameNode = game
    parts: list[str] = []
    fens: list[str] = [temp_board.fen()]
    sans: list[str] = []

    while node.variations:
        next_node = node.variation(0)
        move = next_node.move
        san = temp_board.san(move)
        sans.append(san)

        if temp_board.turn == chess.WHITE:
            parts.append(f"{temp_board.fullmove_number}. {san}")
        else:
            parts.append(f"{temp_board.fullmove_number}... {san}")

        temp_board.push(move)
        fens.append(temp_board.fen())
        node = next_node

    return " ".join(parts), fens, sans


def format_with_variations(game: chess.pgn.Game) -> str:
    def recurse(node: chess.pgn.GameNode, temp_board: chess.Board) -> list[str]:
        result: list[str] = []
        for idx, variation in enumerate(node.variations):
            move = variation.move
            san = temp_board.san(move)
            if temp_board.turn == chess.WHITE:
                prefix = f"{temp_board.fullmove_number}. "
            else:
                prefix = f"{temp_board.fullmove_number}... "

            temp_board.push(move)
            child = recurse(variation, temp_board)
            temp_board.pop()

            text = prefix + san
            if child:
                text += " " + " ".join(child)

            if idx == 0:
                result.append(text)
            else:
                result.append(f"({text})")
        return result

    return " ".join(recurse(game, game.board()))


@visualization_bp.route("/")
def index():
    global board, current_task

    board = chess.Board()
    current_task = None

    session.pop("pgn", None)
    session["task_loaded"] = False
    session["user_has_answered"] = False
    session["solution_shown"] = False
    session.modified = True

    thema_options = [{"value": t.value, "label": THEMA_NAMEN[t]} for t in Thema]
    laenge_options = [{"value": l.value, "label": LAENGE_NAMEN[l]} for l in Laenge]

    selected_thema = session.get("selected_thema", Thema.ZUFALL.value)
    selected_laenge = session.get("selected_laenge", Laenge.BELIEBIG.value)
    selected_number1 = session.get("selected_number1", 3)
    selected_number2 = session.get("selected_number2", 1500)

    encoded_parameter = request.args.get("parameter")
    parameter_error = None
    task_data = None

    if encoded_parameter:
        try:
            decoded = decode_visualization_parameter(encoded_parameter)

            selected_number1 = decoded.halbzuege
            selected_number2 = decoded.rating
            selected_thema = decoded.thema
            selected_laenge = decoded.laenge

            task = create_task_from_values(
                selected_number1,
                selected_number2,
                selected_thema,
                selected_laenge,
            )

            task_data = task.to_dict()

        except Exception as exc:
            parameter_error = str(exc)

    current_parameter = encode_visualization_parameter(
        halbzuege=int(selected_number1),
        rating=int(selected_number2),
        thema=int(selected_thema),
        laenge=int(selected_laenge),
    )

    return render_template(
        "visualization.html",
        fen=task_data["fen"] if task_data else board.fen(),
        thema_options=thema_options,
        selected_thema=selected_thema,
        laenge_options=laenge_options,
        selected_laenge=selected_laenge,
        selected_number1=selected_number1,
        selected_number2=selected_number2,
        initial_task=task_data,
        parameter_error=parameter_error,
        current_parameter=current_parameter,
    )

@visualization_bp.post("/move")
def make_move():
    global board
    data = request.get_json(silent=True) or {}
    move_text = str(data.get("move", "")).strip()

    if not move_text:
        return jsonify({"ok": False, "message": "Bitte einen Zug eingeben."})

    try:
        move = None
        try:
            move = chess.Move.from_uci(move_text)
            if move not in board.legal_moves:
                move = None
        except ValueError:
            move = None

        if move is None:
            move = board.parse_san(move_text)

        if move not in board.legal_moves:
            return jsonify({"ok": False, "message": "Illegaler Zug."})

        board.push(move)
        status = "Zug ausgeführt"
        if board.is_checkmate():
            status = "Schachmatt"
        elif board.is_stalemate():
            status = "Patt"
        elif board.is_check():
            status = "Schach"

        return jsonify(
            {
                "ok": True,
                "fen": board.fen(),
                "message": status,
                "san": board.peek().uci() if False else None,
            }
        )
    except Exception:
        return jsonify({"ok": False, "message": "Ungültiges Zugformat. Beispiel: e2e4, Nf3 oder O-O"})


@visualization_bp.post("/reset")
def reset():
    global board, current_task
    board = chess.Board()
    current_task = None
    session.pop("pgn", None)
    session["task_loaded"] = False
    session["user_has_answered"] = False
    session.modified = True
    return jsonify({
        "ok": True,
        **get_session_state(),
        "fen": board.fen(),
        "message": "Brett zurückgesetzt",
        "history": "",
        "navigation_fens": [board.fen()],
        "navigation_sans": [],
    })


@visualization_bp.post("/set_fen")
def set_fen():
    global board
    data = request.get_json(silent=True) or {}
    fen = str(data.get("fen", "")).strip()
    try:
        board = chess.Board(fen)
        return jsonify({"ok": True, "fen": board.fen(), "message": "FEN geladen"})
    except ValueError:
        return jsonify({"ok": False, "message": "Ungültige FEN"})


@visualization_bp.route("/generate_task", methods=["POST"])
def generate_task():
    data = request.get_json() or {}

    number1 = int(data.get("number1", 0))
    number2 = int(data.get("number2", 0))
    select1 = int(data.get("select1", 0))
    select2 = int(data.get("select2", 0))

    task = create_task_from_values(
        number1,
        number2,
        select1,
        select2,
    )

    encoded_parameter = encode_visualization_parameter(
        halbzuege=number1,
        rating=number2,
        thema=select1,
        laenge=select2,
    )

    return jsonify({
        "ok": True,
        **task.to_dict(),
        **get_session_state(),
        "parameter": encoded_parameter,
        "message": "Neue Aufgabe : "+ task.start_fen,
    })

@visualization_bp.route("/solution", methods=["GET"])
def solution():
    if not session.get("task_loaded", False):
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst eine Aufgabe generieren."
        }), 400

    pgn_text = session.get("pgn")

    if not pgn_text:
        return jsonify({
            "ok": False,
            "message": "Keine PGN zur Aufgabe gefunden."
        }), 400

    if not session.get("user_has_answered", False):
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst einen Lösungszug eingeben."
        }), 403

    task = TaskState(pgn_text)
    session["solution_shown"] = True
    session.modified = True

    return jsonify({
        "ok": True,
        **task.solution_dict(),
        **get_session_state(),
        "message": "Lösung angezeigt"
    })

@visualization_bp.route("/check_solution_move", methods=["POST"])
def check_solution_move():
    pgn_text = session.get("pgn")

    if not session.get("task_loaded", False) or not pgn_text:
        return jsonify({
            "ok": False,
            **get_session_state(),
            "message": "Bitte zuerst eine Aufgabe generieren."
        }), 400

    data = request.get_json() or {}
    move = data.get("move", "").strip()

    task = TaskState(pgn_text)
    expected = task.first_move_uci
    is_correct = move[:4] == expected[:4]

    session["user_has_answered"] = True
    session.modified = True

    return jsonify({
        "ok": True,
        **get_session_state(),
        "correct": is_correct,
        "answered": session.get("user_has_answered", False),
        "expected": expected,
        "message": "Richtig!" if is_correct else "Leider falsch." # + move[:4] + " - "  + expected[:4]
    })
   
@visualization_bp.route("/download_pgn")
def download_pgn():
    if not session.get("task_loaded", False):
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst eine Aufgabe generieren."
        }), 400

    if not session.get("user_has_answered", False):
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst einen Lösungszug eingeben."
        }), 403

    pgn_text = session["pgn"]
    filename = f"aufgabe_{datetime.now().strftime('%Y%m%d_%H%M')}.pgn"
    return Response(
        pgn_text,
        mimetype="application/x-chess-pgn",
        headers={
            "Content-Disposition": "attachment; filename="+filename
        }
    )

