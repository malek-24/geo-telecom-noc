#!/bin/sh
# =============================================================
# entrypoint.sh — Script de démarrage du conteneur simulation
# Étape 1 : Attendre que PostgreSQL soit prêt
# Étape 2 : Insérer exactement 120 antennes (seed)
# Étape 3 : Lancer la simulation temps réel
# =============================================================

echo "[ENTRYPOINT] Démarrage du conteneur simulation..."

# Attendre que PostgreSQL soit disponible
echo "[ENTRYPOINT] Attente de PostgreSQL..."
MAX_RETRIES=30
RETRY=0
until python -c "import psycopg2; psycopg2.connect(dbname='antennes_mahdia', user='postgres', password='1234', host='postgres', port='5432')" 2>/dev/null; do
    RETRY=$((RETRY + 1))
    if [ $RETRY -ge $MAX_RETRIES ]; then
        echo "[ENTRYPOINT] ERREUR: PostgreSQL non disponible après ${MAX_RETRIES} tentatives."
        exit 1
    fi
    echo "[ENTRYPOINT] PostgreSQL non prêt (${RETRY}/${MAX_RETRIES}), nouvel essai dans 3s..."
    sleep 3
done

echo "[ENTRYPOINT] PostgreSQL disponible !"

# Vérifier si les antennes sont déjà insérées
NB_ANTENNES=$(python -c "
import psycopg2
conn = psycopg2.connect(dbname='antennes_mahdia', user='postgres', password='1234', host='postgres', port='5432')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM antennes')
print(cur.fetchone()[0])
conn.close()
" 2>/dev/null || echo "0")

echo "[ENTRYPOINT] Antennes actuellement en base: ${NB_ANTENNES}"

if [ "$NB_ANTENNES" != "120" ]; then
    echo "[ENTRYPOINT] Initialisation des 120 antennes..."
    python generate_antennes.py
    echo "[ENTRYPOINT] Antennes initialisées avec succès."
else
    echo "[ENTRYPOINT] 120 antennes déjà présentes — pas de réinitialisation."
fi

# Lancer la simulation temps réel
echo "[ENTRYPOINT] Lancement de la simulation..."
exec python -u generate_mesures.py
