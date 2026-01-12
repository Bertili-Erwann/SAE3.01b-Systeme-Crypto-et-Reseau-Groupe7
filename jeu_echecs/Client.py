#!/usr/bin/env python3
import socket
import time
import os


def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def client(host, port):
    sock = socket.socket()
    sock.connect((host, port))
    f = sock.makefile(mode="rw")
    my_color = None
    connecte = False
    while not connecte:
        log = input(
            "Bienvenue à Term Chess Online\n[1] Se connecter\n[2] Créer un compte\n[0] Quitter\n"
        )
        match log:
            case "1":
                connecte = connexion(f)

            case "2":
                crea_compte(f)

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
            line = f.readline()
            if not line:
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
                print(line, end="")
            else:
                print(line, end="")
                if line.startswith("start"):
                    parts = line.strip().split(" ")
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
                f.write("leave\n")
                f.flush()
                fini = True
                break
            elif len(coup) != 2:
                print("Veuillez respecter le format")
                # Continue la boucle interne pour redemander
            else:
                f.write(f"play {coup[0]} {coup[1]}\n")
                f.flush()
                break  # Sortir de la boucle interne pour relire le serveur
    f.close()
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()


def crea_compte(file) -> bool:
    rep = input("Mettre le login suivis du mot de passe\n").split(" ")
    if len(rep) < 2:
        print("Bien mettre le login et le password")
        return False

    login = rep[0].strip()
    mdp = rep[1].strip()
    file.write(f"register {login} {mdp}\n")
    file.flush()
    response = file.readline().strip()
    print(response)
    return response.startswith("OK")


def connexion(file):
    rep = input("Mettre le login suivis du mot de passe\n").split(" ")
    if len(rep) < 2:
        print("Bien mettre le login et le password")
        return False

    login = rep[0].strip()
    mdp = rep[1].strip()
    file.write(f"connect {login} {mdp}\n")
    file.flush()
    response = file.readline().strip()
    print(response)
    return response.startswith("OK")


if __name__ == "__main__":
    client("localhost", 2460)
