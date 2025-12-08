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
            jeu_blanc = jB.rentre_case(self.plateau)
            self.plateau.to_square()    
            jeu_noir = jN.rentre_case(self.plateau)
            


class Joueur():

    def __init__(self, couleur):
        self.couleur = couleur

    def rentre_case(self, plateau: Jeu) -> str:
        os.system('cls' if os.name == 'nt' else 'clear')
        res = input(
            f"{plateau} \nTOUR:{self.couleur}, rentrez une case parmis les cases suivante (lettre + coordonnée) \n"
        )
        return res


if __name__ == "__main__":
    j = Jeu()
    j.affiche_plateau()
    blanc = Joueur("blanc")
    noir = Joueur("noir")
    j.lance_partie(blanc, noir)
