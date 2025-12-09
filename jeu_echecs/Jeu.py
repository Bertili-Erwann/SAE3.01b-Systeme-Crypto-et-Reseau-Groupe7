import chess
import os


class Jeu():

    def __init__(self):
        self.plateau = chess.Board()

    def affiche_plateau(self):
        print(self.plateau)

    def lance_partie(self, jB, jN):
        while not self.plateau.is_checkmate(
        ) and not self.plateau.is_stalemate():
            # Tour du blanc
            move_blanc = chess.Move(
                chess.parse_square("a2"), chess.parse_square("a8")
            )  # je fais volontairement un move impossible pour entrer dans la boucle
            while move_blanc not in self.plateau.legal_moves:
                try:
                    
                    input_blanc = jB.rentre_case(self.plateau)
                    move_blanc = chess.Move(chess.parse_square(input_blanc[0]),
                                        chess.parse_square(input_blanc[1]))
                except ValueError:
                    print("Mauvais format")
                
            self.plateau.push(move_blanc)

            # Tour du noir
            move_noir = chess.Move(chess.parse_square("a2"),
                                   chess.parse_square("a8"))
            while move_noir not in self.plateau.legal_moves:
                input_noir = jN.rentre_case(self.plateau)
                move_noir = chess.Move(chess.parse_square(input_noir[0]),
                                       chess.parse_square(input_noir[1]))
            self.plateau.push(move_noir)


class Joueur():

    def __init__(self, couleur):
        self.couleur = couleur

    def rentre_case(self, plateau: Jeu) -> str:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(plateau)
        res = input(
            f"\nTOUR:{self.couleur}, Entrez la coordonnée ACTUELLE de la pièce et la NOUVELLE, (ex : a2 a3) \n"
        )
        return res.lower().split(" ")


if __name__ == "__main__":
    j = Jeu()
    blanc = Joueur("blanc")
    noir = Joueur("noir")
    j.lance_partie(blanc, noir)
