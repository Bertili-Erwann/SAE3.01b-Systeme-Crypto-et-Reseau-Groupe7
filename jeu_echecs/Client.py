#!/usr/bin/env python3
import socket

def client(host, port):
    sock = socket.socket()
    sock.connect((host, port))
    f = sock.makefile(mode="rw")
    comm = input("Mettre une commande\n")
    while (comm.split(" ")[0] != "quit"):
        f.write(f"{comm}\n")
        f.flush()
        print(f.readline(), end="")
        comm = input("Mettre une commande\n")
    f.close()
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()


client("localhost", 4444)