class Piece:

    position_depart : int
    position_actu : int
    role : str
    couleur : str

    def __init__(self, position_depart : int, position_actu: int, role: str, couleur: str):
        self.position_depart = position_depart
        self.position_actu = position_actu
        self.role = role
        self.couleur = couleur