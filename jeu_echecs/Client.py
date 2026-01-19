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

    # Handshake ECDH
    try:
        # Réception de la clé publique du serveur
        server_key_str = f.readline().strip()
        if not server_key_str:
            print("Erreur: Pas de clé reçue du serveur")
            return
        server_pub_key = ecdh.import_key_from_str(server_key_str)

        # Envoi de notre clé publique
        f.write(ecdh.export_key_str(pub_key) + "\n")
        f.flush()
        
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
                # Le serveur envoie PLATEAU:xxxxxx
                plateau = line[8:].strip().replace("|", "\n")
                _clear_screen()
                print(plateau)
            elif line.startswith("TOUR:"):
                current = line[5:].strip()
                if my_color is None:
                    # my_color est déterminé par le premier message start, récupéré plus bas
                    pass
                doit_jouer = my_color is not None and current == my_color
                if not doit_jouer:
                    # On attend que l'autre joue, on continue à écouter
                    continue
                else:
                    break
            elif line.startswith("WAIT:" ):
                # Déjà affiché, on boucle pour réécouter
                doit_jouer = False
                continue
            elif line.startswith("ERR:"):
                print(line)
            else:
                print(line) # Affiche les OK ou autres messages
                if line.startswith("start"):
                    parts = line.strip().split("#")
                    if len(parts) >= 2:
                        my_color = parts[1].strip()
                    continue
        if fini:
            break
        
        if not doit_jouer:
            time.sleep(0.3)
            continue  # Pas notre tour, on reboucle sans demander input

        # Boucle pour redemander le coup jusqu'à ce qu'il soit valide
        while True:
            coup = input("[Position Actuelle] [Nouvelle Position]\n[0] Quitter\n").split(
                " "
            )
            if coup[0] == "0":
                send("leave") # format "leave"
                fini = True
                break
            elif len(coup) != 2:
                print("Veuillez respecter le format")
                # Continue la boucle interne pour redemander
            else:
                # Format: play#case1#case2
                send(f"play#{coup[0]}#{coup[1]}")
                break  # Sortir de la boucle interne pour relire le serveur
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
    # Format: register#login#mdp
    send_func(f"register#{login}#{mdp}")
    
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
    # Format: connect#login#mdp
    send_func(f"connect#{login}#{mdp}")
    
    response = recv_func()
    if response:
        print(response)
        return response.startswith("OK")
    return False


if __name__ == "__main__":
    client("localhost", 2460)
