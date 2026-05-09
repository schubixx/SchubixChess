import requests
import requests

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    session,
    url_for,
    request,
    flash,
)

from ..extensions import db
from ..config import DEFAULT_AI_SETTINGS
from ..models import LichessToken, Position, Collection
from ..utils import (
    get_current_collection,
    get_positions_for_current_collection,
    fen_to_board,
    is_admin,
    generate_collection_id,
)

from ..config import DEFAULT_AI_SETTINGS
from ..models import LichessToken, Position, Collection
from ..utils import get_current_collection, get_positions_for_current_collection, fen_to_board

play_bp = Blueprint(
    "play",
    __name__,
    url_prefix="/ausspielen"
)


@play_bp.route("/")
def select_fen():
    user_id = session.get("lichess_user_id")
    if not user_id:
        return redirect(url_for("auth.login", next=request.full_path))

    token_record = LichessToken.query.filter_by(lichess_user_id=user_id).first()
    if token_record is None:
        session.clear()
        return redirect(url_for("auth.login", next=request.full_path))

    collection_id = get_current_collection()
    positions = get_positions_for_current_collection()

    collection_record = None
    if collection_id:
        collection_record = Collection.query.filter_by(collection_id=collection_id).first()

    for position in positions:
        position.board = fen_to_board(position.fen)

    return render_template(
        "play/fen_select.html",
        positions=positions,
        username=token_record.lichess_username,
        collection=collection_id,
        collection_record=collection_record,
    )

@play_bp.route("/start/<int:position_id>", methods=["POST"])
def start_game(position_id):
    user_id = session.get("lichess_user_id")
    if not user_id:
        return jsonify({"error": "Nicht eingeloggt."}), 401

    token_record = LichessToken.query.filter_by(lichess_user_id=user_id).first()
    if token_record is None:
        return jsonify({"error": "Kein gespeichertes Token gefunden."}), 401

    collection = get_current_collection()
    if not collection:
        return jsonify({"error": "Keine COLLECTION gesetzt."}), 400

    position = Position.query.filter_by(
        id=position_id,
        collection_id=collection
    ).first()

    if position is None:
        return jsonify({"error": "Stellung nicht gefunden."}), 404

    payload = {
        "level": position.ai_level if position.ai_level is not None else DEFAULT_AI_SETTINGS["level"],
        "clock.limit": position.clock_limit if position.clock_limit is not None else DEFAULT_AI_SETTINGS["clock_limit"],
        "clock.increment": position.clock_increment if position.clock_increment is not None else DEFAULT_AI_SETTINGS["clock_increment"],
        "color": position.color if position.color else DEFAULT_AI_SETTINGS["color"],
        "variant": DEFAULT_AI_SETTINGS["variant"],
        "fen": position.fen,
    }

    response = requests.post(
        current_app.config["LICHESS_CHALLENGE_AI_URL"],
        headers={"Authorization": f"Bearer {token_record.access_token}"},
        data=payload,
        timeout=20,
    )

    if not response.ok:
        return jsonify(
            {
                "error": "Lichess konnte die Partie nicht erstellen.",
                "details": f"{response.status_code}: {response.text}",
            }
        ), 400

    game_data = response.json()
    game_id = game_data.get("id")

    if not game_id:
        return jsonify({"error": "Keine Spiel-ID in der Lichess-Antwort gefunden."}), 500

    return jsonify(
        {
            "game_id": game_id,
            "game_url": f"https://lichess.org/{game_id}",
            "position_id": position.id,
            "title": position.title,
            "collection": collection,
        }
    )


@play_bp.route("/new-collection", methods=["GET", "POST"])
def new_collection():
    if not is_admin():
        return "Nicht erlaubt", 403

    if request.method == "POST":
        collection_id = generate_collection_id()
        valid_rows = 0

        # Stellungen der Collection speichern   
        for i in range(8):
            title = (request.form.get(f"title_{i}") or "").strip()
            position_description = (request.form.get(f"position_description_{i}") or "").strip()
            fen = (request.form.get(f"fen_{i}") or "").strip()
            ai_level_raw = (request.form.get(f"ai_level_{i}") or "").strip()
            color = (request.form.get(f"color_{i}") or "random").strip().lower()
            clock_limit_raw = (request.form.get(f"clock_limit_{i}") or "").strip()
            clock_increment_raw = (request.form.get(f"clock_increment_{i}") or "").strip()

            if not fen:
                continue

            try:
                ai_level = int(ai_level_raw)
            except ValueError:
                flash(f"Stellung {i + 1}: Level muss eine ganze Zahl sein.", "error")
                return render_template("play/new_collection.html"), 400

            try:
                clock_limit = int(clock_limit_raw)
            except ValueError:
                flash(f"Stellung {i + 1}: Clock Limit muss eine ganze Zahl sein.", "error")
                return render_template("play/new_collection.html"), 400

            try:
                clock_increment = int(clock_increment_raw)
            except ValueError:
                flash(f"Stellung {i + 1}: Clock Increment muss eine ganze Zahl sein.", "error")
                return render_template("play/new_collection.html"), 400

            if ai_level < 1 or ai_level > 8:
                flash(f"Stellung {i + 1}: Level ist nur von 1 bis 8 erlaubt.", "error")
                return render_template("play/new_collection.html"), 400

            if clock_limit < 0 or clock_limit > 10800:
                flash(f"Stellung {i + 1}: Clock Limit ist nur von 0 bis 10800 erlaubt.", "error")
                return render_template("play/new_collection.html"), 400

            if clock_increment < 0 or clock_increment > 60:
                flash(f"Stellung {i + 1}: Clock Increment ist nur von 0 bis 60 erlaubt.", "error")
                return render_template("play/new_collection.html"), 400

            if color not in {"white", "black", "random"}:
                flash(f"Stellung {i + 1}: Color muss white, black oder random sein.", "error")
                return render_template("play/new_collection.html"), 400

            pos = Position(
                collection_id=collection_id,
                title=title or f"Stellung {i + 1}",
                description=position_description,
                fen=fen,
                ai_level=ai_level,
                color=color,
                clock_limit=clock_limit,
                clock_increment=clock_increment,
            )
            db.session.add(pos)
            valid_rows += 1

        if valid_rows == 0:
            flash("Bitte mindestens eine Stellung mit FEN eingeben.", "error")
            return render_template("play/new_collection.html"), 400

        # Collection speichern
        description = (request.form.get("description") or "").strip()
        explanation = (request.form.get("explanation") or "").strip()
        user_id = session.get("lichess_user_id")
        token_record = LichessToken.query.filter_by(lichess_user_id=user_id).first()
        creator_name = token_record.lichess_username if token_record else "unbekannt"
        collection_record = Collection(
            collection_id=collection_id,
            creator_name=creator_name,
            description=description,
            explanation=explanation,
        )
        db.session.add(collection_record)


        db.session.commit()
        return render_template("play/collection_created.html", collection_id=collection_id)

    return render_template("play/new_collection.html")

@play_bp.route("/collections")
def my_collections():
    if not is_admin():
        return "Nicht erlaubt", 403

    user_id = session.get("lichess_user_id")
    token_record = LichessToken.query.filter_by(lichess_user_id=user_id).first()

    if not token_record:
        return redirect(url_for("main.menu"))

    collections = (
        Collection.query
        .filter_by(creator_name=token_record.lichess_username)
        .order_by(Collection.id.desc())
        .all()
    )

    return render_template("play/collections.html", collections=collections)


@play_bp.route("/collections/<collection_id>/edit", methods=["GET", "POST"])
def edit_collection(collection_id):
    if not is_admin():
        return "Nicht erlaubt", 403

    user_id = session.get("lichess_user_id")
    token_record = LichessToken.query.filter_by(lichess_user_id=user_id).first()
    if not token_record:
        return redirect(url_for("main.menu"))

    collection = Collection.query.filter_by(
        collection_id=collection_id,
        creator_name=token_record.lichess_username
    ).first_or_404()

    positions = (
        Position.query
        .filter_by(collection_id=collection_id)
        .order_by(Position.id.asc())
        .all()
    )

    if request.method == "POST":
        collection.description = (request.form.get("description") or "").strip()
        collection.explanation = (request.form.get("explanation") or "").strip()


        for position in positions:
            fen = (request.form.get(f"fen_{position.id}") or "").strip()

            # Leere FEN = Stellung löschen
            if not fen:
                db.session.delete(position)
                continue

            try:
                ai_level = int(request.form.get(f"ai_level_{position.id}") or 1)
                clock_limit = int(request.form.get(f"clock_limit_{position.id}") or 300)
                clock_increment = int(request.form.get(f"clock_increment_{position.id}") or 0)
            except ValueError:
                return "Level, Clock Limit und Clock Increment müssen ganze Zahlen sein.", 400

            color = (request.form.get(f"color_{position.id}") or "random").lower()

            if not 1 <= ai_level <= 8:
                return "Level muss zwischen 1 und 8 liegen.", 400
            if not 0 <= clock_limit <= 10800:
                return "Clock Limit muss zwischen 0 und 10800 liegen.", 400
            if not 0 <= clock_increment <= 60:
                return "Clock Increment muss zwischen 0 und 60 liegen.", 400
            if color not in {"white", "black", "random"}:
                return "Color muss white, black oder random sein.", 400

            position.title = (request.form.get(f"title_{position.id}") or "").strip() or f"Stellung {id}"
            position.description = (request.form.get(f"position_description_{position.id}") or "").strip()
            position.fen = fen
            position.ai_level = ai_level
            position.color = color
            position.clock_limit = clock_limit
            position.clock_increment = clock_increment

        db.session.commit()
        return redirect(url_for("play.edit_collection", collection_id=collection_id))

    return render_template(
        "play/edit_collection.html",
        collection=collection,
        positions=positions,
    )

@play_bp.route("/collections/<collection_id>/delete", methods=["POST"])
def delete_collection(collection_id):
    if not is_admin():
        return "Nicht erlaubt", 403

    user_id = session.get("lichess_user_id")
    token_record = LichessToken.query.filter_by(lichess_user_id=user_id).first()

    collection = Collection.query.filter_by(
        collection_id=collection_id,
        creator_name=token_record.lichess_username
    ).first_or_404()

    Position.query.filter_by(collection_id=collection_id).delete()
    db.session.delete(collection)
    db.session.commit()

    return redirect(url_for("play.my_collections"))