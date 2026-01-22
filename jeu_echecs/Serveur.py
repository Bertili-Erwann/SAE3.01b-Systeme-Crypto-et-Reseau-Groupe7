from threading import Thread, Lock, Condition
import socket
import time
import chess
from Jeu import Jeu, Joueur, CoupIllegalException, AttendTonTourException, CoupMalFormate
import csv
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crypto import ecdh

BD_FILEPATH = os.path.join(os.path.dirname(__file__), "bdtmp.csv")


class Server:

    def __init__(self):
        self.running = False
        self.server_socket = None
        self.matchmaker = None
        self.active_sessions = []
        self.sessions_lock = Lock()
        self.private_key, self.public_key = ecdh.generer_cles()
        self.public_key_str = ecdh.export_key_str(self.public_key)

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
        
        if self.matchmaker:
            self.matchmaker.running = False
        
        with self.sessions_lock:
            for session in self.active_sessions:
                session.socket.shutdown(socket.SHUT_RDWR)
                session.socket.close()

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("Serveur arrêté")

    def get_matchmaker(self) -> "MatchMaker":
        return self.matchmaker


class SessionJeu(Thread):
    def __init__(self, server, sock, jeu: Jeu, joueur: Joueur, jeu_condition: Condition, secret_key):
        Thread.__init__(self)
        self.server = server
        self.socket = sock
        self.jeu = jeu
        self.jeu_condition = jeu_condition
        self.file = sock.makefile(mode="rw")
        self.joueur = joueur
        self.autre_session = None
        self.secret_key = secret_key
    
    def set_autre_session(self, autre):
        self.autre_session = autre

    def _send(self, msg):
        try:
            encrypted = ecdh.chiffrer(msg, self.secret_key)
            self.file.write(encrypted + "\n")
            self.file.flush()
        except Exception:
            pass

    def run(self):
        self.server.add_session(self)
        couleur_code = "w" if self.joueur.couleur == "blanc" else "b"
        self._send(f"start {couleur_code}")
        
        while (
            not self.jeu.plateau.is_checkmate() and not self.jeu.plateau.is_stalemate()
        ):
            with self.jeu_condition:
                plateau_str = str(self.jeu.plateau).replace("\n", "|")
                current_color = "blanc" if self.jeu.plateau.turn else "noir"
                self._send(f"PLATEAU:{plateau_str}")
                self._send(f"TOUR:{current_color}")

                if current_color != self.joueur.couleur:
                    self._send(f"WAIT:C'est au tour de {current_color}")
                    self.jeu_condition.wait()
                    continue
                
            raw = self.file.readline()
            if not raw:
                break

            try:
                decrypted_line = ecdh.dechiffrer(raw.strip(), self.secret_key)
            except Exception:
                continue

            if not decrypted_line:
                continue

            line = decrypted_line.strip().split(" ")
            
            match line[0]:
                case "leave":
                    self._send("OK")
                    self.jeu.declarer_abandon(self.joueur.couleur)
                    self._send("lose")
                    break
                case "quit":
                    self._send("OK")
                    break
                case "promote":
                    if len(line) < 3:
                        self._send("ERR: Format de promotion invalide. Utilisez: promote case piece")
                        continue
                    with self.jeu_condition:
                        try:
                            case_src = line[1]
                            piece_char = line[2].lower()
                            
                            piece_map = {
                                'q': chess.QUEEN,
                                'r': chess.ROOK,
                                'b': chess.BISHOP,
                                'n': chess.KNIGHT
                            }
                            
                            if piece_char not in piece_map:
                                self._send("ERR: Pièce invalide. Utilisez q (Queen), r (Rook), b (Bishop), ou n (Knight)")
                                continue
                            
                            from_square = chess.parse_square(case_src)
                            promotion_piece = piece_map[piece_char]
                            
                            move_found = None
                            for legal_move in self.jeu.plateau.legal_moves:
                                if legal_move.from_square == from_square and legal_move.promotion == promotion_piece:
                                    move_found = legal_move
                                    break
                            
                            if move_found:
                                self.jeu.plateau.push(move_found)
                                if self.autre_session:
                                    self.autre_session._send(f"play_ad {chess.square_name(move_found.from_square)} {chess.square_name(move_found.to_square)}")
                                self.jeu_condition.notify_all()
                            else:
                                self._send("ERR: Aucun coup de promotion valide depuis cette case")
                        except Exception as e:
                            self._send(f"ERR: Erreur lors de la promotion: {str(e)}")
                case "play":
                    if len(line) < 3:
                        self._send("ERR: Format de coup invalide")
                        continue
                    with self.jeu_condition:
                        try:
                            self.jeu.faire_coup([line[1], line[2]], self.joueur.couleur)
                            if self.autre_session:
                                self.autre_session._send(f"play_ad {line[1]} {line[2]}")
                            self.jeu_condition.notify_all()
                        except CoupMalFormate:
                            self._send("ERR: Format de coup invalide. Utilisez le format: e2 e4")
                        except CoupIllegalException:
                            self._send("ERR: coup illégal")
                        except AttendTonTourException:
                            self._send("ERR: Attendez votre tour")
                        except IndexError:
                            self._send("ERR: Format de coup invalide. Utilisez le format: e2 e4")
                case _default:
                    self._send(f"ERR : ne peux pas résoudre : '{line}'")
        
        if self.jeu.plateau.is_checkmate():
            gagnant = "noir" if self.jeu.plateau.turn else "blanc"
            if gagnant == self.joueur.couleur:
                self._send("win")
            else:
                self._send("lose")
        elif self.jeu.plateau.is_stalemate():
            self._send("draw")
        
        raw_rejouer = self.file.readline()
        if raw_rejouer:
            try:
                demande_rejouer = ecdh.dechiffrer(raw_rejouer.strip(), self.secret_key).strip()
                if demande_rejouer in ["replay", "new"]:
                    self.jeu.reset_plateau()
                    self._send("OK")
                    self.run()
            except:
                pass
        
        self.server.remove_session(self)  
        
                
    def getJoueur(self):
        return self.joueur


class SessionRegister(Thread):
    def __init__(self, server, sock):
        Thread.__init__(self)
        self.server = server
        self.socket = sock
        self.file = sock.makefile(mode="rw")
        self.secret_key = None

    _write_lock = Lock()

    def _send(self, msg):
        try:
            encrypted = ecdh.chiffrer(msg, self.secret_key)
            self.file.write(encrypted + "\n")
            self.file.flush()
        except Exception:
            pass

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
        try:
            self.file.write(f"sync {self.server.public_key_str}\n")
            self.file.flush()
            
            sync_line = self.file.readline().strip()
            if not sync_line or not sync_line.startswith("sync "):
                return
            
            client_pub_key_str = sync_line[5:]
            self.client_pub_key = ecdh.import_key_from_str(client_pub_key_str)
            self.secret_key = ecdh.deriver_secret(self.server.private_key, self.client_pub_key)
            
            self.file.write("OK\n")
            self.file.flush()
            
        except Exception as e:
            print(f"Erreur handshake session register: {e}")
            return

        while True:
            raw = self.file.readline()
            if not raw:
                break
            
            try:
                decrypted_line = ecdh.dechiffrer(raw.strip(), self.secret_key)
            except Exception:
                continue

            if not decrypted_line:
                continue

            line = decrypted_line.strip().split(" ")
            if not line or not line[0]:
                self._send("ERR: Commande vide")
                continue

            match line[0]:
                case "register":
                    if len(line) < 3:
                        self._send("ERR: Format attendu: register <login> <password>")
                        continue
                    login = line[1].strip()
                    mdp = line[2].strip()
                    bonLog = SessionRegister.verifLogin(login)
                    bonMdp = SessionRegister.verifMdp(mdp)
                    if bonLog and bonMdp:
                        SessionRegister.ecrireUser(login, mdp)
                        self._send("OK")
                    elif not bonLog and bonMdp:
                        self._send(
                            "ERR: Le nom d'utilisateur ne doit pas contenir d'espaces et la longueur doit être entre 3 et 10"
                        )
                    elif bonLog and not bonMdp:
                        self._send(
                            "ERR: Le mot de passe doit être au moins de longueur 6"
                        )
                    else:
                        self._send(
                            "ERR: Le nom d'utilisateur ne doit pas contenir d'espaces et la longueur doit être entre 3 et 10 et le mot de passe doit être au moins de longueur 6"
                        )

                case "connect":
                    if len(line) < 3:
                        self._send("ERR: Format attendu: connect <login> <password>")
                        continue
                    login = line[1].strip()
                    mdp = line[2].strip()
                    if SessionRegister.lireuser(login, mdp):
                        self._send("OK")
                        self.server.get_matchmaker().ajt_thread(self)
                        break
                    else:
                        self._send("ERR: Connexion échouée")
                
                case "quit":
                    self._send("OK")
                    break

                case _default:
                    self._send(
                        f"ERR: Commande {line[0]} de {line} n'a pas pu etre resolue"
                    )


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
                            session_register.secret_key
                        )
                        list_tmp.append(sess)
                    
                    list_tmp[0].set_autre_session(list_tmp[1])
                    list_tmp[1].set_autre_session(list_tmp[0])
                    [t.start() for t in list_tmp]
            time.sleep(0.1)


if __name__ == "__main__":
    serv = Server()
    serv.mainServer(2460)