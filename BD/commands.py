import os
import logging as lg
from sqlalchemy import *


def syncdb() -> None:
    """
    Crée la base de données locale base.db avec la structure définie dans bd.sql.
    """
    try:
        sql_file = os.path.join(os.path.dirname(__file__), 'bd.sql')
        
        if not os.path.exists(sql_file):
            lg.error(f"Fichier bd.sql non trouvé: {sql_file}")
            return
        
        # Créer l'engine SQLite pour base.db
        db_file = os.path.join(os.path.dirname(__file__), 'base.db')
        engine = create_engine(f'sqlite:///{db_file}')
        
        # Lire le fichier SQL
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Adapter le SQL pour SQLite
        sql_content = sql_content.replace('AUTO_INCREMENT', '')
        sql_content = sql_content.replace('INT', 'INTEGER')
        
        # Exécuter les commandes SQL
        with engine.begin() as conn:
            for statement in sql_content.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        conn.execute(text(statement))
                    except Exception as e:
                        lg.warning(f"Instruction ignorée: {e}")
        
        lg.warning('Base de donnée synchronisée!')
        lg.info(f'Fichier créé: {db_file}')
    except Exception as e:
        lg.error(f"Erreur lors de la création de base.db: {e}")


if __name__ == "__main__":
    syncdb()




