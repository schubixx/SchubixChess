from flask import Flask, session, g

from .extensions import db
from .main.routes import main_bp
from .play.routes import play_bp
from .auth.lichess import auth_bp
from .visualization.routes import (visualization_bp)
from .chess960.routes import chess960_bp
from .utils import get_current_collection, store_collection_from_request, is_admin


def create_app():
    app = Flask(__name__)

    app.config.from_object("chess_app.config.Config")

    db.init_app(app)

    @app.before_request
    def persist_collection_parameter():
        g.collection = store_collection_from_request()

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(play_bp)
    app.register_blueprint(visualization_bp)
    app.register_blueprint(chess960_bp)

    @app.context_processor
    def inject_collection():
        return {
            "current_collection": get_current_collection(),
            "is_admin": is_admin(),
        }

    @app.context_processor
    def inject_user():
        username = session.get("lichess_username")

        return {
            "user": {
                "username": username
            } if username else None
        }

    with app.app_context():
        db.create_all()

    return app

    @app.context_processor
    def inject_globals():
        username = session.get("lichess_username")

        return {
            "user": {
                "username": username
            } if username else None,
            "is_admin": is_admin(),
        }
