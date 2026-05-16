from flask import Blueprint, jsonify, render_template, request, session, Response
import chess
import chess.pgn
import io
from datetime import datetime
from ..services.user_move_log_service import log_wendepunkt_move

from .service import WendepunktService
from .state import (
    build_mainline_task,
    is_correct_wendepunkt_move,
    build_solution_items,
    find_first_variation_move,
)


wendepunkt_bp = Blueprint(
    "wendepunkt",
    __name__,
    url_prefix="/wendepunkt"
)


def load_game(pgn_text: str):
    game = chess.pgn.read_game(io.StringIO(pgn_text))

    if game is None:
        raise ValueError("PGN konnte nicht gelesen werden.")

    return game

def build_pgn_from_row(row):
    (
        task_id,
        moves,
        event,
        site,
        white,
        black,
        white_elo,
        black_elo,
    ) = row

    pgn_text = (
        f'[Event "{event or "?"}"]\n'
        f'[Site "{site or "?"}"]\n'
        f'[White "{white or "Weiß"}"]\n'
        f'[Black "{black or "Schwarz"}"]\n'
        f'[WhiteElo "{white_elo or "?"}"]\n'
        f'[BlackElo "{black_elo or "?"}"]\n'
        "\n"
        f"{moves.strip()}\n"
    )

    return pgn_text, task_id

def san_to_german(san: str) -> str:
    replacements = {
        "Q": "D",
        "R": "T",
        "B": "L",
        "N": "S",
    }

    for english, german in replacements.items():
        san = san.replace(english, german)

    return san


def build_mainline_navigation(game):
    board = game.board()
    node = game

    fens = [board.fen()]
    sans = []
    history_items = []

    first_move = True

    while node.variations:
        next_node = node.variation(0)
        move = next_node.move

        san = san_to_german(board.san(move))

        if board.turn == chess.WHITE:
            text = f"{board.fullmove_number}. {san}"
        else:
            if first_move:
                text = f"{board.fullmove_number}... {san}"
            else:
                text = san

        history_items.append(text)
        sans.append(san)

        board.push(move)
        fens.append(board.fen())

        node = next_node
        first_move = False

    return {
        "fen": fens[0],
        "history": " ".join(history_items),
        "history_items": history_items,
        "navigation_fens": fens,
        "navigation_sans": sans,
    }


def get_node_at_index(game, index: int):
    node = game

    for _ in range(index):
        if not node.variations:
            return node
        node = node.variation(0)

    return node


@wendepunkt_bp.route("/")
def index():
    selected_rating = session.get("wendepunkt_rating", 2000)
    task_id = request.args.get("TASK")

    initial_task = None
    fen = chess.STARTING_FEN
    loaded_task_id = None

    if task_id:
        service = WendepunktService()
        row = service.hole_aufgabe_by_task_id(task_id)

        if row:
            pgn_text, loaded_task_id = build_pgn_from_row(row)
            task = build_mainline_task(pgn_text)

            session["wendepunkt_pgn"] = pgn_text
            session["wendepunkt_task_id"] = loaded_task_id
            session["wendepunkt_user_has_answered"] = False
            session.modified = True

            initial_task = {
                "fen": task.fen,
                "history": task.history,
                "history_items": task.history_items,
                "navigation_fens": task.navigation_fens,
                "navigation_sans": task.navigation_sans,
                "task_id": loaded_task_id,
            }

            fen = task.fen

    return render_template(
        "wendepunkt.html",
        fen=fen,
        selected_rating=selected_rating,
        initial_task=initial_task,
        loaded_task_id=loaded_task_id,
    )

@wendepunkt_bp.post("/generate_task")
def generate_task():
    data = request.get_json() or {}
    rating = int(data.get("rating", 2000))
    rating = max(600, min(3000, rating))

    # optional auf 100er runden
    rating = round(rating / 100) * 100

    service = WendepunktService()
    row = service.hole_aufgabe(rating)

    if row is None:
        return jsonify({
            "ok": False,
            "message": "Keine passende Wendepunkt-Aufgabe gefunden.",
        }), 404

    (
    task_id,
    moves,
    puzzle_rating,
    event,
    site,
    white,
    black,
    white_elo,
    black_elo,
    ) = row
    pgn_text = (
        f'[Event "{event or "?"}"]\n'
        f'[Site "{site or "?"}"]\n'
        f'[White "{white or "Weiß"}"]\n'
        f'[Black "{black or "Schwarz"}"]\n'
        f'[WhiteElo "{white_elo or puzzle_rating or "?"}"]\n'
        f'[BlackElo "{black_elo or puzzle_rating or "?"}"]\n'
        '\n'
        f'{moves.strip()}\n'
    )

    game = load_game(pgn_text)
    task_data = build_mainline_navigation(game)

    session["wendepunkt_pgn"] = pgn_text
    session["wendepunkt_rating"] = rating
    session.modified = True
    session["wendepunkt_user_has_answered"] = False
    session["wendepunkt_task_id"] = task_id

    task = build_mainline_task(pgn_text)

    if not task.history_items or len(task.navigation_fens) <= 1:
        return jsonify({
            "ok": False,
            "message": "Keine passende Aufgabe gefunden: PGN enthält keine Hauptvariante.",
        }), 404
    #print("PGN:", pgn_text[:500])
    #print("History:", task.history_items)
    #print("FEN-Anzahl:", len(task.navigation_fens))

    return jsonify({
        "ok": True,
        "fen": task.fen,
        "history": task.history,
        "history_items": task.history_items,
        "navigation_fens": task.navigation_fens,
        "navigation_sans": task.navigation_sans,
        "task_id": task_id,
        "message": "Wendepunkt-Aufgabe geladen.",
    })

@wendepunkt_bp.post("/check_move")
def check_move():
    pgn_text = session.get("wendepunkt_pgn")

    if not pgn_text:
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst eine Aufgabe laden.",
        }), 400

    data = request.get_json() or {}
    move_text = str(data.get("move", "")).strip()
    index = int(data.get("index", 0))

    if not move_text:
        return jsonify({
            "ok": False,
            "message": "Bitte einen Zug eingeben.",
        }), 400

    game = load_game(pgn_text)
    node = get_node_at_index(game, index)

    username = session.get("lichess_username")

    session["wendepunkt_user_has_answered"] = True
    session.modified = True

    expected = None
    correct_move_number = None
    is_correct = False

    if len(node.variations) >= 2:
        # Es gibt an der aktuellen Stellung eine Nebenvariante.
        expected = node.variation(1).move.uci()
        correct_move_number = index
        is_correct = move_text[:4] == expected[:4]

        message = "Richtig!" if is_correct else "Leider falsch."

    else:
        # An der aktuellen Stellung gibt es keine Nebenvariante.
        # Für das Logging soll trotzdem die erste vorhandene Wendepunkt-
        # Nebenvariante der Partie gefunden werden.
        correct_move_number, expected = find_first_variation_move(game)

        message = "Leider falsch."

    if username:
        log_wendepunkt_move(
            lichess_username=username,
            task_id=session.get("wendepunkt_task_id", ""),
            current_move_number=index,
            entered_move=move_text,
            correct_move_number=correct_move_number,
            correct_move=expected or "",
            is_correct=is_correct,
        )

    return jsonify({
        "ok": True,
        "correct": is_correct,
        "expected": expected,
        "correct_move_number": correct_move_number,
        "user_has_answered": True,
        "message": message,
    })

@wendepunkt_bp.route("/solution")
def solution():
    pgn_text = session.get("wendepunkt_pgn")

    if not pgn_text:
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst eine Aufgabe laden.",
        }), 400

    if not session.get("wendepunkt_user_has_answered", False):
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst einen Zug eingeben.",
        }), 403

    solution_items = build_solution_items(pgn_text)

    return jsonify({
        "ok": True,
        "history_items": solution_items,
        "message": "Lösung angezeigt.",
    })

@wendepunkt_bp.route("/download_pgn")
def download_pgn():
    pgn_text = session.get("wendepunkt_pgn")

    if not pgn_text:
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst eine Aufgabe laden.",
        }), 400

    if not session.get("wendepunkt_user_has_answered", False):
        return jsonify({
            "ok": False,
            "message": "Bitte zuerst einen Zug eingeben.",
        }), 403

    filename = f"wendepunkt_{datetime.now().strftime('%Y%m%d_%H%M')}.pgn"

    return Response(
        pgn_text,
        mimetype="application/x-chess-pgn",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )