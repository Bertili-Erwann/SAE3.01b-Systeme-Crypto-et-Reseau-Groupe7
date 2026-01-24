#!/usr/bin/env python3
import socket
import time
import os
import sys

# Ajout du dossier crypto au path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crypto import ecdh


def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def client(host, port):
    sock = socket.socket()
    sock.connect((host, port))
    f = sock.makefile(mode="rw")

    # Génération des clés ECDH
    print("Génération des clés ECDH...")
    priv_key, pub_key = ecdh.generer_cles()

    try:
        sync_line = f.readline().strip()
        if not sync_line or not sync_line.startswith("sync "):
            print("Erreur: Commande sync non reçue du serveur")
            return
        
        server_key_str = sync_line[5:]
        server_pub_key = ecdh.import_key_from_str(server_key_str)

        f.write(f"sync {ecdh.export_key_str(pub_key)}\n")
        f.flush()
        
        ok_response = f.readline().strip()
        if ok_response != "OK":
            print(f"Erreur: Réponse attendue 'OK', reçu '{ok_response}'")
            return
        
        secret_key = ecdh.deriver_secret(priv_key, server_pub_key)
        
    except Exception as e:
        print(f"Erreur lors du handshake: {e}")
        return

    def send(msg):
        encrypted = ecdh.chiffrer(msg, secret_key)
        f.write(encrypted + "\n")
        f.flush()

    def recv():
        raw = f.readline()
        if not raw:
            return None
        return ecdh.dechiffrer(raw.strip(), secret_key)

    my_color = None
    connecte = False
    while not connecte:
        log = input(
            "Bienvenue à Term Chess Online\n[1] Se connecter\n[2] Créer un compte\n[0] Quitter\n"
        )
        match log:
            case "1":
                connecte = connexion(send, recv)

            case "2":
                crea_compte(send, recv)

            case "0":
                f.write("quit\n")
                f.flush()
                print("Aurevoir")
                f.close()
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
                return

            case _default:
                print(f"on ne peut pas résoudre {log}")
    fini = False
    while not fini:
        doit_jouer = False
        while True:
            line = recv()
            if line is None:
                print("Connexion fermée par le serveur")
                fini = True
                break
            
            if line.startswith("PLATEAU:"):
                plateau = line[8:].strip().replace("|", "\n")
                _clear_screen()
                print(plateau)
            elif line.startswith("TOUR:"):
                current = line[5:].strip()
                if my_color is None:
                    pass
                doit_jouer = my_color is not None and current == my_color
                if not doit_jouer:
                    continue
                else:
                    break
            elif line.startswith("WAIT:" ):
                doit_jouer = False
                continue
            elif line.startswith("play_ad"):
                parts = line.strip().split(" ")
                if len(parts) >= 3:
                    print(f"Adversaire a joué: {parts[1]} -> {parts[2]}")
                continue
            elif line.startswith("win"):
                print("Vous avez gagné !")
                rejouer = input("Voulez-vous rejouer? [replay/new] ou [0] pour quitter\n").strip()
                if rejouer in ["replay", "new"]:
                    f.write(f"{rejouer}\n")
                    f.flush()
                    resp = f.readline().strip()
                    if resp == "OK":
                        my_color = None
                        continue
                else:
                    f.write("quit\n")
                    f.flush()
                    fini = True
                    break
            elif line.startswith("lose"):
                print("Vous avez perdu...")
                rejouer = input("Voulez-vous rejouer? [replay/new] ou [0] pour quitter\n").strip()
                if rejouer in ["replay", "new"]:
                    f.write(f"{rejouer}\n")
                    f.flush()
                    resp = f.readline().strip()
                    if resp == "OK":
                        my_color = None
                        continue
                else:
                    f.write("quit\n")
                    f.flush()
                    fini = True
                    break
            elif line.startswith("draw"):
                print("Match nul !")
                rejouer = input("Voulez-vous rejouer? [replay/new] ou [0] pour quitter\n").strip()
                if rejouer in ["replay", "new"]:
                    f.write(f"{rejouer}\n")
                    f.flush()
                    resp = f.readline().strip()
                    if resp == "OK":
                        my_color = None
                        continue
                else:
                    f.write("quit\n")
                    f.flush()
                    fini = True
                    break
            elif line.startswith("ERR:"):
                print(line)
            else:
                print(line)
                if line.startswith("start"):
                    parts = line.strip().split(" ")
                    if len(parts) >= 2:
                        couleur_recue = parts[1].strip()
                        if couleur_recue == "w":
                            my_color = "blanc"
                        elif couleur_recue == "b":
                            my_color = "noir"
                        else:
                            my_color = couleur_recue
                    continue
        if fini:
            break
        
        if not doit_jouer:
            time.sleep(0.3)
            continue
        while True:
            coup = input("[Position Actuelle] [Nouvelle Position] ou [promote case piece]\n[0] Quitter\n").split(
                " "
            )
            if coup[0] == "0":
                send("leave")
                fini = True
                break
            elif coup[0] == "promote" and len(coup) == 3:
                send(f"promote {coup[1]} {coup[2]}")
                break
            elif len(coup) != 2:
                print("Veuillez respecter le format")
            else:
                send(f"play {coup[0]} {coup[1]}")
                break
    f.close()
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()


def crea_compte(send_func, recv_func) -> bool:
    rep = input("Mettre le login suivis du mot de passe\n").split(" ")
    if len(rep) < 2:
        print("Bien mettre le login et le password")
        return False

    login = rep[0].strip()
    mdp = rep[1].strip()
    send_func(f"register {login} {mdp}")
    
    response = recv_func()
    if response:
        print(response)
        return response.startswith("OK")
    return False


def connexion(send_func, recv_func):
    rep = input("Mettre le login suivis du mot de passe\n").split(" ")
    if len(rep) < 2:
        print("Bien mettre le login et le password")
        return False

    login = rep[0].strip()
    mdp = rep[1].strip()
    send_func(f"connect {login} {mdp}")
    
    response = recv_func()
    if response:
        print(response)
        return response.startswith("OK")
    return False


if __name__ == "__main__":
    client("localhost", 2460)
