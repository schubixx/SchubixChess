# chess_app/wendepunkt/state.py

import io
from dataclasses import dataclass

from typing import Optional

import chess
import chess.pgn


@dataclass
class WendepunktTask:
    fen: str
    history: str
    history_items: list[str]
    navigation_fens: list[str]
    navigation_sans: list[str]

def build_solution_items(pgn_text: str):
    game = load_game(pgn_text)
    board = game.board()
    node = game

    items = []
    first_move = True

    while node.variations:
        main_node = node.variation(0)
        main_move = main_node.move

        san = san_to_german(board.san(main_move))

        if board.turn == chess.WHITE:
            text = f"{board.fullmove_number}. {san}"
        else:
            text = f"{board.fullmove_number}... {san}" if first_move else san

        items.append(text)

        # Nebenvarianten direkt an dieser Stellung
        if len(node.variations) > 1:
            for variation in node.variations[1:]:
                comment = variation.comment or ""

                if "TYPE:alternative" in comment:
                    continue

                # TYPE:solution oder erste unmarkierte Variante anzeigen
                variation_board = board.copy()
                variation_items = []
                variation_node = variation

                while variation_node:
                    move = variation_node.move
                    san_var = san_to_german(variation_board.san(move))

                    if variation_board.turn == chess.WHITE:
                        var_text = f"{variation_board.fullmove_number}. {san_var}"
                    else:
                        var_text = f"{variation_board.fullmove_number}... {san_var}"

                    variation_items.append(var_text)
                    variation_board.push(move)

                    variation_node = (
                        variation_node.variation(0)
                        if variation_node.variations
                        else None
                    )

                items.append({
                    "type": "marker",
                    "text": "(" + " ".join(variation_items) + ")"
                })

        board.push(main_move)
        node = main_node
        first_move = False

    return items

def load_game(pgn_text: str) -> chess.pgn.Game:
    game = chess.pgn.read_game(io.StringIO(pgn_text))

    if game is None:
        raise ValueError("PGN konnte nicht gelesen werden.")

    return game


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

def get_variation_moves_at_index(pgn_text: str, index: int):
    game = load_game(pgn_text)
    node = get_node_at_index(game, index)

    solution = None
    alternatives = []

    if len(node.variations) < 2:
        return solution, alternatives

    for variation in node.variations[1:]:
        comment = variation.comment or ""
        move_uci = variation.move.uci()

        if "TYPE:alternative" in comment:
            alternatives.append(move_uci)
        elif "TYPE:solution" in comment:
            solution = move_uci
        elif solution is None:
            solution = move_uci

    return solution, alternatives

def build_mainline_task(pgn_text: str) -> WendepunktTask:
    game = load_game(pgn_text)

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
            text = f"{board.fullmove_number}... {san}" if first_move else san

        history_items.append(text)
        sans.append(san)

        board.push(move)
        fens.append(board.fen())

        node = next_node
        first_move = False

    return WendepunktTask(
        fen=fens[0],
        history=" ".join(history_items),
        history_items=history_items,
        navigation_fens=fens,
        navigation_sans=sans,
    )


def get_node_at_index(game: chess.pgn.Game, index: int) -> chess.pgn.GameNode:
    """
    index = 0 bedeutet Startstellung.
    index = 1 bedeutet nach dem ersten Hauptvariantenzug.
    """
    node = game

    for _ in range(index):
        if not node.variations:
            break

        node = node.variation(0)

    return node


def expected_variation_move_uci(
    pgn_text: str,
    index: int,
) -> Optional[str]:
    """
    Liefert den ersten Zug der Nebenvariante an der aktuellen Stellung.

    None bedeutet:
    An dieser Stelle gibt es keine Nebenvariante.
    """
    game = load_game(pgn_text)
    node = get_node_at_index(game, index)

    if len(node.variations) < 2:
        return None

    return node.variation(1).move.uci()


def is_correct_wendepunkt_move(
    pgn_text: str,
    index: int,
    move_uci: str,
) -> tuple[bool, Optional[str]]:
    expected = expected_variation_move_uci(
        pgn_text=pgn_text,
        index=index,
    )

    if expected is None:
        return False, None

    # move_uci[:4] ignoriert Promotion, z. B. e7e8q.
    return move_uci[:4] == expected[:4], expected

def find_first_variation_move(game):
    """
    Sucht die erste Stellung der Hauptvariante,
    an der eine Nebenvariante vorhanden ist.

    Rückgabe:
    (
        zugnummer_der_stellung,
        erster_zug_der_nebenvariante_als_uci
    )

    Beispiel:
    (5, "e2e4")
    """

    node = game
    index = 0

    while node.variations:

        # Hauptvariante + mindestens eine Nebenvariante
        if len(node.variations) >= 2:
            return (
                index,
                node.variation(1).move.uci()
            )

        node = node.variation(0)
        index += 1

    return None, None
