from threading import Thread, Lock, Condition
import socket
import time
from Jeu import Jeu, Joueur, CoupIllegalException, AttendTonTourException, CoupMalFormate
import csv
import os

BD_FILEPATH = os.path.join(os.path.dirname(__file__), "bdtmp.csv")


class Server:

    def __init__(self):
        self.running = False
        self.server_socket = None
        self.matchmaker = None
        self.active_sessions = []
        self.sessions_lock = Lock()

    def mainServer(self, port):
        self.server_socket = socket.socket()
        self.server_socket.bind(("0.0.0.0", port))
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.listen(10)
        self.matchmaker = MatchMaker(self)
        self.matchmaker.start()
        self.running = True
        print(f"Serveur démarré sur le port {port}")
        while self.running:
            try:
                cli, _ = self.server_socket.accept()
                sess = SessionRegister(self, cli)
                sess.start()
            except OSError:
                break
        print("Boucle serveur terminée")

    def add_session(self, session):
        with self.sessions_lock:
            self.active_sessions.append(session)

    def remove_session(self, session):
        with self.sessions_lock:
            if session in self.active_sessions:
                self.active_sessions.remove(session)

    def shutdown(self):
        print("Arrêt du serveur...")
        self.running = False
        
        # Arrêter le matchmaker
        if self.matchmaker:
            self.matchmaker.running = False
        
        # Fermer toutes les sessions actives
        with self.sessions_lock:
            for session in self.active_sessions:
                session.socket.shutdown(socket.SHUT_RDWR)
                session.socket.close()

        # Fermer le socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("Serveur arrêté")

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
        self.autre_session = None
    
    def set_autre_session(self, autre):
        self.autre_session = autre

    def run(self):
        self.server.add_session(self)
        couleur_code = "w" if self.joueur.couleur == "blanc" else "b"
        self.file.write(f"start {couleur_code}\n")
        self.file.flush()
        while (
            not self.jeu.plateau.is_checkmate() and not self.jeu.plateau.is_stalemate()
        ):
            with self.jeu_condition:
                # Toujours envoyer le plateau pour que le client l'affiche puis decide si c'est son tour
                plateau_str = str(self.jeu.plateau).replace("\n", "|")
                current_color = "blanc" if self.jeu.plateau.turn else "noir"
                self.file.write(f"PLATEAU:{plateau_str}\n")
                self.file.flush()
                self.file.write(f"TOUR:{current_color}\n")
                self.file.flush()

                if current_color != self.joueur.couleur:
                    self.file.write(f"WAIT:C'est au tour de {current_color}\n")
                    self.file.flush()
                    self.jeu_condition.wait()
                    continue
                
            line = self.file.readline().strip().split(" ")
            match line[0]:
                case "leave":
                    self.file.write("OK\n")
                    self.file.flush()
                    self.jeu.declarer_abandon(self.joueur.couleur)
                    self.file.write("lose\n")
                    self.file.flush()
                    break
                case "quit":
                    self.file.write("OK\n")
                    self.file.flush()
                    break
                case "play":
                    with self.jeu_condition:
                        try:
                            self.jeu.faire_coup([line[1], line[2]], self.joueur.couleur)
                            # Notifier l'autre joueur du coup joué
                            if self.autre_session:
                                self.autre_session.file.write(f"play_ad {line[1]} {line[2]}\n")
                                self.autre_session.file.flush()
                            self.jeu_condition.notify_all()
                        except CoupMalFormate:
                            self.file.write("ERR: Format de coup invalide. Utilisez le format: e2 e4\n")
                            self.file.flush()
                        except CoupIllegalException:
                            self.file.write("ERR: coup illégal\n")
                            self.file.flush()
                        except AttendTonTourException:
                            self.file.write("ERR: Attendez votre tour\n")
                            self.file.flush()
                        except IndexError:
                            self.file.write("ERR: Format de coup invalide. Utilisez le format: e2 e4\n")
                            self.file.flush()
                case _default:
                    self.file.write(f"ERR : ne peux pas résoudre : '{line}'\n")
                    self.file.flush()
        
        # Fin de la partie - vérifier le résultat
        if self.jeu.plateau.is_checkmate():
            gagnant = "noir" if self.jeu.plateau.turn else "blanc"
            if gagnant == self.joueur.couleur:
                self.file.write("win\n")
            else:
                self.file.write("lose\n")
            self.file.flush()
        elif self.jeu.plateau.is_stalemate():
            self.file.write("draw\n")
            self.file.flush()
        
        # Attendre la décision de rejouer ou non
        demande_rejouer = self.file.readline().strip()
        if demande_rejouer in ["replay", "new"]:
            self.jeu.reset_plateau()
            self.file.write("OK\n")
            self.file.flush()
            # Relancer une nouvelle partie
            self.run()
        
        self.server.remove_session(self)  
        
                
    
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
            file_exists = os.path.isfile(BD_FILEPATH)
            with open(BD_FILEPATH, "a", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["login", "password"])
                if not file_exists or csvfile.tell() == 0:
                    writer.writeheader()
                writer.writerow({"login": login, "password": mdp})

    @staticmethod
    def lireuser(login: str, mdp: str) -> bool:
        with SessionRegister._write_lock:
            try:
                with open(BD_FILEPATH, "r", newline="") as file:
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
            raw = self.file.readline()
            if not raw:
                break
            line = raw.strip().split(" ")
            if not line or not line[0]:
                self.file.write("ERR: Commande vide\n")
                self.file.flush()
                continue
            match line[0]:
                case "register":
                    if len(line) < 3:
                        self.file.write("ERR: Format attendu: register <login> <password>\n")
                        self.file.flush()
                        continue
                    login = line[1].strip()
                    mdp = line[2].strip()
                    bonLog = SessionRegister.verifLogin(login)
                    bonMdp = SessionRegister.verifMdp(mdp)
                    if bonLog and bonMdp:
                        SessionRegister.ecrireUser(login, mdp)
                        self.file.write("OK\n")
                        self.file.flush()
                        # On laisse le thread actif pour permettre un futur 'connect' depuis le menu client
                    elif not bonLog and bonMdp:
                        self.file.write(
                            "ERR: Le nom d'utilisateur ne doit pas contenir d'espaces et la longueur doit être entre 3 et 10\n"
                        )
                        self.file.flush()

                    elif bonLog and not bonMdp:
                        self.file.write(
                            "ERR: Le mot de passe doit être au moins de longueur 6\n"
                        )
                        self.file.flush()

                    else:
                        self.file.write(
                            "ERR: Le nom d'utilisateur ne doit pas contenir d'espaces et la longueur doit être entre 3 et 10 et le mot de passe doit être au moins de longueur 6\n"
                        )
                        self.file.flush()

                case "connect":
                    if len(line) < 3:
                        self.file.write("ERR: Format attendu: connect <login> <password>\n")
                        self.file.flush()
                        continue
                    login = line[1].strip()
                    mdp = line[2].strip()
                    if SessionRegister.lireuser(login, mdp):
                        self.file.write("OK\n")
                        self.file.flush()
                        self.server.get_matchmaker().ajt_thread(self)
                        break
                    else:
                        self.file.write("ERR: Connexion échouée\n")
                        self.file.flush()
                
                case "quit":
                    self.file.write("OK\n")
                    self.file.flush()
                    break

                case _default:
                    self.file.write(
                        f"ERR: Commande {line[0]} de {line} n'a pas pu etre resolue\n"
                    )
                    self.file.flush()


class MatchMaker(Thread):
    def __init__(self, server):
        Thread.__init__(self)
        self.server = server
        self.joueurs_idle = []
        self.lock = Lock()
        self.running = True

    def ajt_thread(self, joueur: Thread) -> None:
        with self.lock:
            self.joueurs_idle.append(joueur)

    def run(self):
        while self.running:
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
                    # Définir les références croisées entre les deux joueurs
                    list_tmp[0].set_autre_session(list_tmp[1])
                    list_tmp[1].set_autre_session(list_tmp[0])
                    [t.start() for t in list_tmp]
            time.sleep(0.1)


if __name__ == "__main__":
    serv = Server()
    serv.mainServer(2460)
