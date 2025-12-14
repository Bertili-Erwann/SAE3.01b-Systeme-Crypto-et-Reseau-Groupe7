from threading import Thread, Lock
import socket
import time
from Jeu import Jeu, Joueur
import csv


class Server:

    def __init__(self):
        self.counter = 0

    def mainServer(self, port):
        sock = socket.socket()
        sock.bind(("0.0.0.0", port))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.listen(10)
        self.matchmaker = MatchMaker()
        self.matchmaker.start()
        while True:
            cli, _ = sock.accept()
            sess = SessionRegister(self, cli)
            sess.start()

    def get_matchmaker(self) -> "MatchMaker":
        return self.matchmaker


class SessionJeu(Thread):
    def __init__(self, server, sock, jeu: Jeu, joueur: Joueur):
        Thread.__init__(self)
        self.server = server
        self.socket = sock
        self.jeu = jeu
        self.file = sock.makefile(mode="rw")
        self.joueur = joueur

    def run(self):
        self.file.write(f"Partie trouvée! Vous jouez les {self.joueur.couleur}\n")
        self.file.flush()
        # while (
        #     not self.jeu.plateau.is_checkmate() and not self.jeu.plateau.is_stalemate()
        # ):
        #     self.file.write(
        #         f"{self.jeu.plateau}\nTOUR:{self.joueur.couleur}, Entrez la coordonnée ACTUELLE de la pièce et la NOUVELLE, (ex : a2 a3) \n"
        #     )
        #     line = self.file.readline()
        #     self.jeu.faire_coup(str(line[:5]).split(" "))
        #     self.file.flush()
        time.sleep(5)
        self.file.write("Partie terminée\n")
        self.file.flush()
        self.file.close()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def getJoueur(self):
        return self.joueur


class SessionRegister(Thread):
    def __init__(self, server, sock):
        Thread.__init__(self)
        self.server = server
        self.socket = sock
        self.file = sock.makefile(mode="rw")

    _write_lock = Lock()

    @staticmethod
    def verifLogin(log: str) -> bool:
        return " " not in log and 3 <= len(log) <= 10

    @staticmethod
    def verifMdp(mdp: str) -> bool:
        return len(mdp) >= 6

    @staticmethod
    def ecrireUser(login: str, mdp: str) -> None:
        with SessionRegister._write_lock:
            with open("bdtmp.csv", "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows([login, mdp])

    def get_socket(self):
        return self.socket

    def get_server(self) -> None:
        return self.server

    def run(self):
        while True:
            line = self.file.readline().split(" ")
            match line[0]:
                case "register":
                    bonLog = SessionRegister.verifLogin(line[1])
                    bonMdp = SessionRegister.verifMdp(line[2])
                    if bonLog and bonMdp:
                        SessionRegister.ecrireUser(line[1], line[2])
                        self.file.write("OK: Compte créé avec succès\n")
                        self.file.flush()
                        self.server.get_matchmaker().ajt_thread(self)
                        break
                    elif not bonLog and bonMdp:
                        self.file.write(
                            f"ERR: Le nom d'utilisateur ne doit pas contenir d'espaces et la longueur doit entre 3 et 10"
                        )
                        self.file.flush()

                    elif bonLog and not bonMdp:
                        self.file.write(
                            f"ERR: Le mot de passe doit être au moins de longueur 6"
                        )
                        self.file.flush()

                    else:
                        self.file.write(
                            f"ERR: Le nom d'utilisateur ne doit pas contenir d'espaces et la longueur doit entre 3 et 10 et le mot de passe doit être au moins de longueur 6"
                        )
                        self.file.flush()

                case "connect":
                    pass
                case _default:
                    self.file.write(
                        f"ERR: Commande {line[0]} de {line} n'a pas pu etre resolue"
                    )


class MatchMaker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.joueurs_idle = []

    def ajt_thread(self, joueur: Thread) -> None:
        self.joueurs_idle.append(joueur)

    def run(self):
        while True:
            if len(self.joueurs_idle) >= 2:
                list_tmp = []
                jeu = Jeu()
                for i in range(2):
                    session_register = self.joueurs_idle.pop()
                    sess = SessionJeu(
                        session_register.get_server(),
                        session_register.get_socket(),
                        jeu,
                        Joueur("blanc" if i == 0 else "noir"),
                    )
                    list_tmp.append(sess)
                [t.start() for t in list_tmp]
            time.sleep(0.1)


if __name__ == "__main__":
    serv = Server()
    serv.mainServer(2460)
