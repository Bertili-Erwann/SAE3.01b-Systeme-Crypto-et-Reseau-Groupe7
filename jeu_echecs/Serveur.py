from threading import Thread, Lock, Condition
import socket
import time
from Jeu import Jeu, Joueur, CoupIllegalException, AttendTonTourException
import csv
import os


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
    def __init__(self, server, sock, jeu: Jeu, joueur: Joueur, jeu_condition: Condition):
        Thread.__init__(self)
        self.server = server
        self.socket = sock
        self.jeu = jeu
        self.jeu_condition = jeu_condition
        self.file = sock.makefile(mode="rw")
        self.joueur = joueur

    def run(self):
        self.file.write(f"start {self.joueur.couleur}\n")
        self.file.flush()
        while (
            not self.jeu.plateau.is_checkmate() and not self.jeu.plateau.is_stalemate()
        ):
            with self.jeu_condition:
                # Attendre que ce soit notre tour
                while ("blanc" if self.jeu.plateau.turn else "noir") != self.joueur.couleur:
                    self.file.write(f"WAIT: C'est au tour de {('blanc' if self.jeu.plateau.turn else 'noir')}\n")
                    self.file.flush()
                    self.jeu_condition.wait()
                
                # C'est notre tour
                print(self.jeu.plateau)
                plateau_str = str(self.jeu.plateau).replace("\n", "|")
                self.file.write(f"PLATEAU:{plateau_str}\n")
                self.file.flush()
                self.file.write(f"TOUR:{self.joueur.couleur}\n")
                self.file.flush()
                
            line = self.file.readline().strip().split(" ")
            match line[0]:
                case "leave":
                    self.file.write("OK\n")
                    self.file.flush()
                    self.file.close()
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                    return
                case "play":
                    with self.jeu_condition:
                        try:
                            self.jeu.faire_coup([line[1], line[2]], self.joueur.couleur)
                            self.jeu_condition.notify_all()
                        except CoupIllegalException:
                            self.file.write("ERR: coup illégal\n")
                            self.file.flush()
                        except AttendTonTourException:
                            self.file.write("ERR: Attendez votre tour\n")
                            self.file.flush()
                case _default:
                    self.file.write(f"ERR : ne peux pas résoudre : '{line}'\n")
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
            file_exists = os.path.isfile("bdtmp.csv")
            with open("bdtmp.csv", "a", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["login", "password"])
                if not file_exists or csvfile.tell() == 0:
                    writer.writeheader()
                writer.writerow({"login": login, "password": mdp})

    @staticmethod
    def lireuser(login: str, mdp: str) -> bool:
        with SessionRegister._write_lock:
            try:
                with open("bdtmp.csv", "r", newline="") as file:
                    reader = csv.DictReader(file)
                    if reader.fieldnames is None or set(reader.fieldnames) < {
                        "login",
                        "password",
                    }:
                        return False
                    for row in reader:
                        if (
                            row.get("login", "").strip() == login.strip()
                            and row.get("password", "").strip() == mdp.strip()
                        ):
                            return True
                    return False
            except FileNotFoundError:
                return False

    def get_socket(self):
        return self.socket

    def get_server(self) -> None:
        return self.server

    def run(self):
        while True:
            line = self.file.readline().strip().split(" ")
            match line[0]:
                case "register":
                    print("1")
                    bonLog = SessionRegister.verifLogin(line[1])
                    bonMdp = SessionRegister.verifMdp(line[2])
                    print("2")
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
                    if SessionRegister.lireuser(line[1], line[2]):
                        self.file.write("OK: Connexion réussie\n")
                        self.file.flush()
                        self.server.get_matchmaker().ajt_thread(self)
                        break
                    else:
                        self.file.write("ERR: Connexion échouée \n")
                        self.file.flush()

                case _default:
                    self.file.write(
                        f"ERR: Commande {line[0]} de {line} n'a pas pu etre resolue"
                    )


class MatchMaker(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.joueurs_idle = []
        self.lock = Lock()

    def ajt_thread(self, joueur: Thread) -> None:
        with self.lock:
            self.joueurs_idle.append(joueur)

    def run(self):
        while True:
            with self.lock:
                if len(self.joueurs_idle) >= 2:
                    list_tmp = []
                    jeu = Jeu()
                    jeu_condition = Condition()
                    for i in range(2):
                        session_register = self.joueurs_idle.pop()
                        sess = SessionJeu(
                            session_register.get_server(),
                            session_register.get_socket(),
                            jeu,
                            Joueur("blanc" if i == 0 else "noir"),
                            jeu_condition,
                        )
                        list_tmp.append(sess)
                    [t.start() for t in list_tmp]
            time.sleep(0.1)


if __name__ == "__main__":
    serv = Server()
    serv.mainServer(2460)
