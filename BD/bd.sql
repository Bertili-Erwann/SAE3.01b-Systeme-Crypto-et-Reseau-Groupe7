DROP TABLE IF EXISTS JOUER;
DROP TABLE IF EXISTS PARTIE;
DROP TABLE IF EXISTS COMPTE;

CREATE TABLE COMPTE (
    id_compt INT PRIMARY KEY AUTO_INCREMENT,
    pseudo VARCHAR(50) UNIQUE NOT NULL,
    mdp VARCHAR(255) NOT NULL
);

CREATE TABLE PARTIE (
    id_partie INT PRIMARY KEY AUTO_INCREMENT,
    histo_coups TEXT,
    duree INT
);

CREATE TABLE JOUER (
    id_compt INT,
    id_partie INT,
    couleur VARCHAR(10) NOT NULL CHECK (couleur IN ('blanc', 'noir')),
    vainqueur BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id_compt, id_partie),
    FOREIGN KEY (id_compt) REFERENCES COMPTE(id_compt),
    FOREIGN KEY (id_partie) REFERENCES PARTIE(id_partie)
);
