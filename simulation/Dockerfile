# =============================================================
# Simulation — Dockerfile v2
# 1. Lance generate_antennes.py pour initialiser 120 antennes
# 2. Lance generate_mesures.py en boucle toutes les 30 minutes
# =============================================================
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les deux scripts
COPY generate_antennes.py .
COPY generate_mesures.py .

# Script de démarrage : seed les antennes puis lance la simulation
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN pip install --no-cache-dir psycopg2-binary==2.9.9 schedule requests

CMD ["./entrypoint.sh"]
