from flask import Blueprint, render_template, request, redirect, url_for

from ..services.play_service import (
    load_play_configuration
)

from ..services.visualization_service import (
    load_visualization_tasks
)


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def menu():
    return render_template("menu.html")


@main_bp.route("/visualisierung")
def visualization():
    return redirect(url_for("visualization.index"))

