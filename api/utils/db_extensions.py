"""
db_extensions.py — Tables complémentaires (audit, historique états, chat)
Créées ou migrées au démarrage si nécessaire.
"""


def _migrate_messages_chat(cur) -> None:
    """Aligne messages_chat sur le schéma messagerie publique + privée."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages_chat (
            id                SERIAL PRIMARY KEY,
            auteur_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
            auteur_nom        VARCHAR(100),
            auteur_role       VARCHAR(50),
            destinataire_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
            destinataire_nom  VARCHAR(100),
            contenu           TEXT NOT NULL,
            is_private        BOOLEAN DEFAULT FALSE,
            date_envoi        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cols = [
        ("auteur_role", "VARCHAR(50)"),
        ("destinataire_id", "INTEGER REFERENCES users(id) ON DELETE SET NULL"),
        ("destinataire_nom", "VARCHAR(100)"),
        ("is_private", "BOOLEAN DEFAULT FALSE"),
    ]
    for name, typedef in cols:
        cur.execute(f"""
            ALTER TABLE messages_chat
            ADD COLUMN IF NOT EXISTS {name} {typedef}
        """)


def _migrate_audit_logs(cur) -> None:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id           SERIAL PRIMARY KEY,
            utilisateur  VARCHAR(100) NOT NULL,
            action       VARCHAR(255) NOT NULL,
            cible        VARCHAR(255),
            type_objet   VARCHAR(80),
            valeur_avant TEXT,
            valeur_apres TEXT,
            adresse_ip   VARCHAR(64),
            date_action  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for name, typedef in [
        ("type_objet", "VARCHAR(80)"),
        ("valeur_avant", "TEXT"),
        ("valeur_apres", "TEXT"),
        ("adresse_ip", "VARCHAR(64)"),
    ]:
        cur.execute(f"""
            ALTER TABLE audit_logs
            ADD COLUMN IF NOT EXISTS {name} {typedef}
        """)


def initialiser_tables_extensions(conn) -> None:
    cur = conn.cursor()
    _migrate_audit_logs(cur)
    _migrate_messages_chat(cur)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historique_etats (
            id              SERIAL PRIMARY KEY,
            antenne_id      INTEGER NOT NULL REFERENCES antennes(id) ON DELETE CASCADE,
            ancien_etat     VARCHAR(30),
            nouvel_etat     VARCHAR(30) NOT NULL,
            date_changement TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_historique_antenne
        ON historique_etats(antenne_id, date_changement DESC)
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_lectures (
            user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            peer_id      INTEGER NOT NULL DEFAULT 0,
            last_read_id INTEGER NOT NULL DEFAULT 0,
            updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, peer_id)
        )
    """)
    conn.commit()
    cur.close()
