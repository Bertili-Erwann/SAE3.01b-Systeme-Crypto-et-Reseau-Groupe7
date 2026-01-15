
import os
import sys

# Add crypto to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crypto import ecdh

def test_protocol_simple():
    print("--- 1. Initialisation ---")
    
    # 1. Le Serveur démarre et génère ses clés
    print("SERVEUR: Génération des clés...")
    srv_priv, srv_pub = ecdh.generer_cles()
    srv_pub_str = ecdh.export_key_str(srv_pub)
    print(f"SERVEUR: PubKey exportée: {srv_pub_str[:20]}...")

    # 2. Le Client démarre et génère ses clés
    print("\nCLIENT: Génération des clés...")
    cli_priv, cli_pub = ecdh.generer_cles()
    cli_pub_str = ecdh.export_key_str(cli_pub)
    print(f"CLIENT: PubKey exportée: {cli_pub_str[:20]}...")

    print("\n--- 2. Handshake (Simulé) ---")
    
    # Echange simulé via Socket
    # Le serveur envoie sa clé publique au client
    received_srv_pub = ecdh.import_key_from_str(srv_pub_str)
    
    # Le client envoie sa clé publique au serveur
    received_cli_pub = ecdh.import_key_from_str(cli_pub_str)
    
    # 3. Dérivation du secret partagé (Simple ECDH)
    print("CLIENT: Calcul du secret partagé...")
    cli_secret_key = ecdh.deriver_secret(cli_priv, received_srv_pub)
    print(f"CLIENT: Secret Key: {cli_secret_key.hex()[:20]}...")

    print("SERVEUR: Calcul du secret partagé...")
    srv_secret_key = ecdh.deriver_secret(srv_priv, received_cli_pub)
    print(f"SERVEUR: Secret Key: {srv_secret_key.hex()[:20]}...")
    
    print("\n--- 3. Vérification ---")
    if cli_secret_key == srv_secret_key:
        print("SUCCÈS: Les clés secrètes sont identiques!")
    else:
        print("ÉCHEC: Les clés secrètes sont différentes!")
        return

    print("\n--- 4. Test Communication Chiffrée ---")
    msg_clair = "Ceci est un test simple."
    print(f"CLIENT: Envoi message: '{msg_clair}'")
    
    encrypted_msg = ecdh.chiffrer(msg_clair, cli_secret_key)
    print(f"Transit (Chiffré): {encrypted_msg}")
    
    decrypted_msg = ecdh.dechiffrer(encrypted_msg, srv_secret_key)
    print(f"SERVEUR: Message déchiffré: '{decrypted_msg}'")
    
    if msg_clair == decrypted_msg:
        print("SUCCÈS: Chiffrement/Déchiffrement OK")
    else:
        print("ÉCHEC: Le message déchiffré ne correspond pas")

if __name__ == "__main__":
    test_protocol_simple()
