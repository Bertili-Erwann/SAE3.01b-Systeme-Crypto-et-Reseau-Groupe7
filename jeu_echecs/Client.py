#!/usr/bin/env python3
import socket


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
                pass
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

    while True:
        line = f.readline()
        if not line:  # Connexion fermée par le serveur
            print("Connexion fermée par le serveur")
            break
        print(line, end="")

    # while (comm.split(" ")[0] != "quit"):
    #     f.write(f"{comm}\n")
    #     f.flush()
    #     print(f.readline(), end="")
    #     comm = input("Mettre une commande\n")
    f.close()
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()


def crea_compte(file) -> bool:
    rep = input("Mettre le login suivis du mot de passe").split(" ")
    file.write(f"register {rep[0]} {rep[1]}\n")
    file.flush()
    response = file.readline().strip()
    return not response.startswith("ERR")


if __name__ == "__main__":
    client("localhost", 2460)
