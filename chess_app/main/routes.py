from flask import Blueprint, render_template, request, redirect, url_for, session
from flask import abort
from ..utils import is_admin
from ..services.user_move_log_service import create_connection
from ..config import AVAILABLE_PIECE_SETS, DEFAULT_PIECE_SET

from ..services.play_service import (load_play_configuration)

from ..services.visualization_service import (load_visualization_tasks)


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def menu():
    return render_template("menu.html")


@main_bp.route("/visualisierung")
def visualization():
    return redirect(url_for("visualization.index"))

@main_bp.route("/set-piece-set", methods=["POST"])
def set_piece_set():
    piece_set = request.form.get("piece_set", DEFAULT_PIECE_SET)

    if piece_set in AVAILABLE_PIECE_SETS:
        session["piece_set"] = piece_set

    return redirect(request.referrer or "/")

@main_bp.route("/admin/logs")
def user_move_logs():
    if not is_admin():
        abort(403)

    conn = create_connection()

    try:
        visualization_logs = conn.execute("""
            SELECT
                lichess_username,
                created_at,
                puzzle_id,
                halfmoves,
                entered_move,
                correct_move,
                is_correct
            FROM visualization_moves
            ORDER BY created_at DESC
            LIMIT 200
        """).fetchall()

        wendepunkt_logs = conn.execute("""
            SELECT
                lichess_username,
                created_at,
                task_id,
                current_move_number,
                entered_move,
                correct_move_number,
                correct_move,
                is_correct
            FROM wendepunkt_moves
            ORDER BY created_at DESC
            LIMIT 200
        """).fetchall()

    finally:
        conn.close()

    return render_template(
        "admin_logs.html",
        visualization_logs=visualization_logs,
        wendepunkt_logs=wendepunkt_logs,
    )