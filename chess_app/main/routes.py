from flask import Blueprint, render_template, request, redirect, url_for, session
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
