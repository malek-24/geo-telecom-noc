import psycopg2
from utils.globals import DATABASE_URL

def connecter_base_de_donnees():
    return psycopg2.connect(DATABASE_URL)

def rows_to_dicts(cur):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row))] if cur.rowcount == 1 else [dict(zip(cols, row)) for row in cur.fetchall()]
