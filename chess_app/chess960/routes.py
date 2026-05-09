import random

from flask import Blueprint, jsonify, render_template


chess960_bp = Blueprint(
    "chess960",
    __name__,
    url_prefix="/schach960"
)


def suche_platz(aufstellung: list[str], figur: str, nummer: int) -> list[str]:
    freie_felder = [
        index for index, feld in enumerate(aufstellung)
        if feld == " "
    ]

    ziel_index = freie_felder[nummer - 1]
    aufstellung[ziel_index] = figur

    return aufstellung


def schach960_auslosen() -> str:
    aufstellung = [" "] * 8

    # 1. Läufer auf einem dunklen Feld: b, d, f, h
    zufall = random.randint(1, 4)
    aufstellung[zufall * 2 - 1] = "b"

    # 2. Läufer auf einem hellen Feld: a, c, e, g
    zufall = random.randint(1, 4)
    aufstellung[zufall * 2 - 2] = "b"

    # Dame
    zufall = random.randint(1, 6)
    aufstellung = suche_platz(aufstellung, "q", zufall)

    # 1. Springer
    zufall = random.randint(1, 5)
    aufstellung = suche_platz(aufstellung, "n", zufall)

    # 2. Springer
    zufall = random.randint(1, 4)
    aufstellung = suche_platz(aufstellung, "n", zufall)

    # Rest: Turm, König, Turm
    aufstellung = suche_platz(aufstellung, "r", 1)
    aufstellung = suche_platz(aufstellung, "k", 1)
    aufstellung = suche_platz(aufstellung, "r", 1)

    schwarze_figuren = "".join(aufstellung)
    weisse_figuren = schwarze_figuren.upper()

    return (
        f"{schwarze_figuren}/pppppppp/8/8/8/8/"
        f"PPPPPPPP/{weisse_figuren} w KQkq - 0 1"
    )


@chess960_bp.route("/")
def index():
    fen = schach960_auslosen()

    return render_template(
        "chess960.html",
        fen=fen
    )


@chess960_bp.post("/auslosen")
def auslosen():
    fen = schach960_auslosen()

    return jsonify({
        "fen": fen
    })