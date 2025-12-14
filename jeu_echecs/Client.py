#!/usr/bin/env python3
import socket
import time


def client(host, port):
    sock = socket.socket()
    sock.connect((host, port))
    f = sock.makefile(mode="rw")
    est_enregistrer = False
    while not est_enregistrer:
        log = input(
            "Bienvenue à Term Chess Online\n[1] Se connecter\n[2] Créer un compte\n[0] Quitter\n"
        )
        match log:
            case "1":
                while not est_enregistrer:
                    est_enregistrer = connexion(f)

            case "2":
                while not est_enregistrer:
                    est_enregistrer = crea_compte(f)
            case "0":
                print("Aurevoir")
                f.close()
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
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
                print(plateau)
            elif line.startswith("TOUR:"):
                print(line, end="")
                doit_jouer = True
                break
            elif line.startswith("WAIT:"):
                print(line, end="")
                doit_jouer = False
                break
            elif line.startswith("ERR:"):
                print(line, end="")
            else:
                print(line, end="")
                if line.startswith("start"):
                    break
        if fini:
            break
        
        if not doit_jouer:
            time.sleep(0.3)
            continue  # Pas notre tour, on reboucle sans demander input

        coup = input("[Position Actuelle] [Nouvelle Position]\n[0] Quitter\n").split(
            " "
        )
        if coup[0] == "0":
            f.write("leave\n")
            f.flush()
            fini = True
        elif len(coup) != 2:
            print("Veuillez respecter le format")
        else:
            f.write(f"play {coup[0]} {coup[1]}\n")
            f.flush()
    f.close()
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()


def crea_compte(file) -> bool:
    rep = input("Mettre le login suivis du mot de passe\n").split(" ")
    if len(rep) < 2:
        print("Bien mettre le login et le password")
        return False

    file.write(f"register {rep[0]} {rep[1]}\n")
    file.flush()
    response = file.readline().strip()
    return not response.startswith("ERR")


def connexion(file):
    rep = input("Mettre le login suivis du mot de passe\n").split(" ")
    if len(rep) < 2:
        print("Bien mettre le login et le password")
        return False

    file.write(f"connect {rep[0]} {rep[1]}\n")
    file.flush()
    response = file.readline().strip()
    return not response.startswith("ERR")


if __name__ == "__main__":
    client("localhost", 2460)
