from threading import Thread 
import socket
from Jeu import Jeu, Joueur
class Server:

    def __init__(self):
        self.counter = 0

    def mainServer(self, port):
        sock = socket.socket()
        sock.bind(("0.0.0.0", port))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.listen(10)
        jeu = Jeu()
        listThreads = []                                   
        while len(listThreads)<2:
            cli, _ = sock.accept()
            sess = Session(self, cli, jeu,Joueur("blanc" if len(listThreads) == 0 else "noir" ))
            listThreads.append(sess)
        listThreads[0].start()
        listThreads[1].start()

class Session(Thread):
    def __init__(self,server, sock,jeu:Jeu,joueur:Joueur):
        Thread.__init__(self)
        self.server = server
        self.socket = sock
        self.jeu = jeu
        self.file = sock.makefile(mode="rw")
        self.joueur = joueur
    def run(self):
        while not self.jeu.plateau.is_checkmate() and not self.jeu.plateau.is_stalemate():
            self.file.write(f"{self.jeu.plateau}\nTOUR:{self.joueur.couleur}, Entrez la coordonnée ACTUELLE de la pièce et la NOUVELLE, (ex : a2 a3) \n")
            line = self.file.readline()
            self.jeu.faire_coup(str(line[:5]).split(" "))
            self.file.flush()
        self.file.close()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
    def getJoueur(self):
        return self.joueur
        
if __name__ == "__main__":
    serv = Server()
    serv.mainServer(2460)
