from threading import Thread 
import socket
from .Jeu import Jeu, Joueur
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
        while True:
            if len(listThreads)<2: #Limite a 2 joueur 
                cli, _ = sock.accept()
                sess = Session(self, cli, jeu,Joueur("blanc" if len(listThreads) == 0 else "noir" ))
                listThreads.append(sess)
            else:
                listThreads[0].start()
                listThreads[1].start()
                jeu.lance_partie(listThreads[0], listThreads[1])

class Session(Thread):
    def __init__(self,server, sock,jeu:Jeu,joueur:Joueur):
        Thread.__init__(self)
        self.server = server
        self.socket = sock
        self.jeu = jeu
        self.file = sock.makefile(mode="rw")
        self.joueur = joueur
    def run(self):
        while True:
            line = self.file.readline().strip() 
            self.file.write(self.jeu.plateau_to_str())
            self.writea
            self.file.flush()
        self.file.close()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

        
if __name__ == "__main__":
    
    serv = Server()
    serv.mainServer(4444)