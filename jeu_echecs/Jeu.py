import chess
import os


class Jeu():

    def __init__(self):
        self.plateau = chess.Board()

    def reset_plateau(self):
        self.plateau = chess.Board()

    def affiche_plateau(self):
        print(self.plateau)
        
    def revanche(self,jB,jN) -> None:
        if(jB.revanche() and jN.revanche()):
            self.reset_plateau()
            self.lance_partie(jB,jN) # je fais expres de les inverser
        else:
            print(f"La partie s'achève avec un score de {jN.get_score()} - {jB.get_score()}")
            
    def lance_partie(self, jB, jN) -> None:
        while not self.plateau.is_checkmate() and not self.plateau.is_stalemate():
            for j in [jB,jN]:
                move = chess.Move(chess.parse_square("a2"), chess.parse_square("a8"))  # je fais volontairement un move impossible pour entrer dans la boucle
                while move not in self.plateau.legal_moves:
                    try:
                        input = j.rentre_case(self.plateau)
                        move = chess.Move(chess.parse_square(input[0]),chess.parse_square(input[1]))
                    except ValueError:
                        print("Mauvais format")
                self.plateau.push(move)
                if j == jB and (self.plateau.is_checkmate() or self.plateau.is_stalemate()):
                    break
                
        #Le resultat du match 
        resultat = self.plateau.outcome()
        match resultat.termination  :
            case chess.Termination.CHECKMATE: 
                if resultat.winner:
                    print("Vainqueur : Blanc par mat !")
                    jB.inc_score()
                    print(f"{jB.get_score()} - {jN.get_score()}")
                else:
                    print(f"Vainqueur : Noir par mat !")
                    jN.inc_score()
                    print(f"{jN.get_score()} - {jB.get_score()}")
            case chess.Termination.STALEMATE: 
                print("Match nulle !")
                print(f"{jB.get_score()} - {jN.get_score()}")
        
        self.revanche(jB,jN)            

class Joueur():

    def __init__(self, couleur):
        self.couleur = couleur
        self.score = 0
        
    def inc_score(self) -> None :
        """
        Incrémente le score de 1         
        """
        self.score+=1
    
    def get_score(self) -> int:
        return self.score

    def revanche(self) -> bool:
        """
        Demande au joueur si il veux prendre sa revanche 
        returns : True si il prend sa revanche, False sinon
        """
        while True:
            demande = input("Voulez vous prendre votre revanche ? (O)ui/(N)on ")
            match demande.lower():
                case "o"|"oui": 
                    return True
                case "n"|"non": 
                    return False
                case _default:
                    print(f"{demande.lower()} n'est pas une reponse attendu")

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
    
# f2 f3 
# e7 e6       
# g2 g4 
# d8 h4 
# la combinaison la plus rapide pour mat
