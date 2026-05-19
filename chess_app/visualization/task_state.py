import io
import chess
import chess.pgn


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

        self.puzzle_id = game.headers.get("PuzzleId", "")

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
            "puzzle_id": self.puzzle_id,
        }

    def solution_dict(self):
        return {
            "history": self.solution_text,
            "history_items": self.solution_items,
            "navigation_fens": self.navigation_fens,
            "navigation_sans": self.navigation_sans,
        }

