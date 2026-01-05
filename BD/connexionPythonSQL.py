import sqlalchemy
import getpass
from sqlalchemy import text
import os


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


if __name__ == "__main__":
    login = input("login MySQL : ")
    passwd = getpass.getpass("mot de passe MySQL : ")
    serveur= "servinfo-maria"
    bd = input("nom de la base de données : ")
    syncdb(login, passwd, serveur, bd)
