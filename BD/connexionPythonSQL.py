import sqlalchemy
import getpass
from sqlalchemy import text
import os
import json


def ouvrir_connexion(user, passwd, host, database):
    """ouvre une connexion MySQL et retourne (connexion, engine)."""
    try:
        engine = sqlalchemy.create_engine(f"mysql://{user}:{passwd}@{host}/{database}")
        cnx = engine.connect()
    except Exception as err:
        print(err)
        raise err
    print("connexion réussie")
    return cnx, engine


def syncdb(user, passwd, host, database) -> None:
    """Charge et exécute bd.sql pour créer les tables (sans globals)."""
    try:
        _, engine = ouvrir_connexion(user, passwd, host, database)
    except Exception:
        return

    sql_file = os.path.join(os.path.dirname(__file__), 'bd.sql')
    if not os.path.exists(sql_file):
        print(f"Fichier bd.sql non trouvé: {sql_file}")
        return

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    with engine.begin() as conn:
        for statement in sql_content.split(';'):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    print('Base de donnée synchronisée!')


def loaddb(user, passwd, host, database) -> None:
    """Charge toutes les données de la base MySQL dans base.db"""
    try:
        cnx, engine = ouvrir_connexion(user, passwd, host, database)
    except Exception:
        return
    
    # Récupérer toutes les tables
    tables = ['COMPTE', 'PARTIE', 'JOUER']
    data = {}
    
    with engine.begin() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT * FROM {table}"))
                rows = result.fetchall()
                # Convertir les résultats en liste de dictionnaires
                data[table] = [dict(row._mapping) for row in rows]
                print(f"Table {table}: {len(data[table])} enregistrement(s) chargé(s)")
            except Exception as e:
                print(f"Erreur lors du chargement de {table}: {e}")
                data[table] = []
    
    # Sauvegarder dans base.db
    db_file = os.path.join(os.path.dirname(__file__), 'base.db')
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    
    print(f'Base de données chargée dans {db_file}')
    cnx.close()


if __name__ == "__main__":
    
    login = input("login MySQL : ")
    passwd = getpass.getpass("mot de passe MySQL : ")
    serveur= "servinfo-maria"
    bd = input("nom de la base de données : ")
    
    print("\n[1] Synchroniser la BD (créer les tables)")
    print("\n[2] Charger la BD dans base.db")
    choix = input("Choix : ")
    
    if choix == "1":
        syncdb(login, passwd, serveur, bd)
    elif choix == "2":
        loaddb(login, passwd, serveur, bd)
