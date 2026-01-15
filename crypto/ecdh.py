from tinyec import registry
from tinyec.ec import Point
from Crypto.Cipher import AES
import hashlib
import secrets
import base64

curve = registry.get_curve('brainpoolP256r1')

def generer_cles():
    """Génère une paire de clés (privée, publique)."""
    private_key = secrets.randbelow(curve.field.n)
    public_key = private_key * curve.g
    return private_key, public_key

def export_key_str(public_key):
    """Exporte la clé publique en string format 'x|y'."""
    return f"{public_key.x}|{public_key.y}"

def import_key_from_str(key_str):
    """Importe une clé publique depuis le format 'x|y'."""
    try:
        x_str, y_str = key_str.split('|')
        return Point(curve, int(x_str), int(y_str))
    except Exception as e:
        print(f"Erreur import clé: {e}")
        return None

def ecc_point_to_256_bit_key(point):
    """Dérive une clé de 256 bits depuis un point ECC (x et y)."""
    sha = hashlib.sha256(int.to_bytes(point.x, 32, 'big'))
    sha.update(int.to_bytes(point.y, 32, 'big'))
    return sha.digest()

def ecc_calc_encryption_keys(pubKey):
    """
    Génère une paire de clés éphémère et calcule le secret partagé.
    Retourne (Point_Secret_Partagé, Point_Public_Éphémère)
    Côté Client (Emmetteur) dans un schéma ECIES/ECDH ephemeral.
    """
    ciphertextPrivKey = secrets.randbelow(curve.field.n)
    ciphertextPubKey = ciphertextPrivKey * curve.g
    sharedECCKey = pubKey * ciphertextPrivKey
    return (sharedECCKey, ciphertextPubKey)

def ecc_calc_decryption_key(privKey, ciphertextPubKey):
    """
    Calcule le secret partagé à partir de sa clé privée et de la clé publique éphémère reçue.
    Retourne Point_Secret_Partagé.
    Côté Serveur (Récepteur).
    """
    sharedECCKey = ciphertextPubKey * privKey
    return sharedECCKey

def deriver_secret(private_key, peer_public_key):
    """
    Compatibility wrapper or direct usage. 
    Pour le code existant qui attend des bytes directement.
    """
    shared_point = ecc_calc_decryption_key(private_key, peer_public_key)
    return ecc_point_to_256_bit_key(shared_point)


def chiffrer(msg, secret_key):
    """
    Chiffre un message avec AES-GCM et la clé partagée.
    Retourne: nonce|tag|ciphertext (tout en base64)
    """
    aesCipher = AES.new(secret_key, AES.MODE_GCM)
    ciphertext, authTag = aesCipher.encrypt_and_digest(msg.encode('utf-8'))
    nonce = aesCipher.nonce
    
    c_b64 = base64.b64encode(ciphertext).decode('ascii')
    n_b64 = base64.b64encode(nonce).decode('ascii')
    t_b64 = base64.b64encode(authTag).decode('ascii')
    
    return f"{n_b64}|{t_b64}|{c_b64}"

def dechiffrer(msg_chiffre, secret_key):
    """
    Déchiffre un message formaté 'nonce|tag|ciphertext'.
    """
    try:
        parts = msg_chiffre.strip().split('|')
        if len(parts) != 3:
            return None
            
        n_b64, t_b64, c_b64 = parts
        
        nonce = base64.b64decode(n_b64)
        tag = base64.b64decode(t_b64)
        ciphertext = base64.b64decode(c_b64)
        
        aesCipher = AES.new(secret_key, AES.MODE_GCM, nonce)
        plaintext = aesCipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode('utf-8')
    except Exception:
        return None
