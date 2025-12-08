from abc import abstractmethod
from typing import List, Tuple

import Plateau


class Piece(object):
    def __init__(self, plateau: Plateau.Plateau, couleur: str, symbole: str, coordonnee: Tuple[int, int]):
        self.couleur = couleur
        self.symbole = symbole
        self.coordonnee = coordonnee
        self.plateau = plateau

    def getCaseActu(self) -> Tuple[int, int]:
        return self.coordonnee
        
    @abstractmethod
    def avancer(self, target: Tuple[int, int]) -> None:
        pass
        
    @abstractmethod
    def getTargets(self) -> List[Tuple[int, int]]:
        pass
