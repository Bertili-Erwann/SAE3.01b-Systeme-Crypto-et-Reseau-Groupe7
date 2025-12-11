from Case import Case

class Plateau():
      
    def __init__(self):
        self.dimensions = 8
        self.cases = {}
        self.lettres = ["A","B","C","D","E","F","G","H"]
        self.nbB = 16
        self.nbN = 16
        for i in range(self.dimensions):
            for j in range(self.dimensions):
                self.cases[(i,self.lettres[j])]
        for i in range(self.dimensions):
            
        
        
        
    def get_piece_case(self, i, j):
        case = ""+i+self.lettres[j]
        return self.cases[case]
    
    def est_occupe(self, i, j):
        case = ""+i+self.lettres[j]
        return self.cases[case]==""
    
    def deplacer_piece(self, i, j, piece):
        case = ""+i+self.lettres[j]
        if self.est_occupe(i, j):
            piece2 = self.get_piece_case(i, j)
            if piece2.couleur == piece.couleur:
                print("Case occupé par un allié -- Déplacement impossible")
                return False
            print(piece2+" éliminé -- Déplacement de "+piece+" en "+case)
            self.cases[case]=piece
            return True
        
                
            
        
