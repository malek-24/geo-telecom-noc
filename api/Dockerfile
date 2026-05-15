# =============================================================
# Dockerfile — API Flask (Plateforme SIG Mahdia)
# Multi-stage build : stage builder + stage runtime allégé
# =============================================================

# ── STAGE 1 : Builder ─────────────────────────────────────
# Installe les dépendances dans un environnement complet
FROM python:3.10-slim AS builder

# Installer les compilateurs nécessaires pour certains packages Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /install

# Copier et installer les dépendances dans un dossier isolé
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install/packages -r requirements.txt


# ── STAGE 2 : Runtime ─────────────────────────────────────
# Image finale légère, sans compilateur
FROM python:3.10-slim

# Dépendances système minimales pour psycopg2 (client libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    wget \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les packages installés par le stage builder
COPY --from=builder /install/packages /usr/local

# Copier le code de l'application et les scripts utilitaires
COPY . .

# Exposition du port Flask
EXPOSE 5000

# Démarrage via Gunicorn : 2 workers, timeout 120 secondes
CMD ["gunicorn", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:5000", "app:app"]