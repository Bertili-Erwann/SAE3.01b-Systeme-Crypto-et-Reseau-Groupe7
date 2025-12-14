import chess
import os


class Jeu:
    """Gère une partie d'échecs avec son plateau et les règles du jeu."""

    def __init__(self) -> None:
        """Initialise une nouvelle partie avec un plateau d'échecs vierge."""
        self.plateau = chess.Board()

    def reset_plateau(self) -> None:
        """Réinitialise le plateau à son état initial."""
        self.plateau = chess.Board()

    def faire_coup(self, input, tour):
        if (
            self.plateau.turn
            and tour == "blanc"
            or not self.plateau.turn
            and tour == "noir"
        ):
            move = chess.Move(
                chess.parse_square(input[0]), chess.parse_square(input[1])
            )
            if move not in self.plateau.legal_moves:
                raise CoupIllegalException()
            else:
                self.plateau.push(move)
        else:
            raise AttendTonTourException()


class CoupIllegalException(Exception):
    pass


class AttendTonTourException(Exception):
    pass

# f2 f3
# e7 e6
# g2 g4
# d8 h4
# la combinaison la plus rapide pour mat
