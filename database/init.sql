-- =============================================================
-- Tunisie Telecom NOC — PostgreSQL/PostGIS initialization
-- PFE Licence — Supervision intelligente des antennes — 2026
-- Mahdia, Tunisie — 120 antennes, 9 zones
-- 
-- MÉTRIQUES CONSERVÉES : température, cpu, signal, latence, disponibilite
-- MÉTRIQUES SUPPRIMÉES  : ram, traffic, packet_loss, jitter
-- =============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

DROP VIEW  IF EXISTS antennes_geo    CASCADE;
DROP VIEW  IF EXISTS antennes_statut CASCADE;
DROP TABLE IF EXISTS commentaires_incidents CASCADE;
DROP TABLE IF EXISTS incidents        CASCADE;
DROP TABLE IF EXISTS mesures          CASCADE;
DROP TABLE IF EXISTS antennes         CASCADE;

-- ── TABLE: antennes ──────────────────────────────────────────
CREATE TABLE antennes (
    id                SERIAL PRIMARY KEY,
    nom               VARCHAR(100) NOT NULL,
    zone              VARCHAR(100) NOT NULL,
    type              VARCHAR(50)  DEFAULT '4G',
    latitude          NUMERIC(9,6) NOT NULL,
    longitude         NUMERIC(9,6) NOT NULL,
    operateur         VARCHAR(100) DEFAULT 'Tunisie Telecom',
    date_installation DATE         DEFAULT CURRENT_DATE,
    geom              geometry(Point, 4326),
    statut            VARCHAR(30)  DEFAULT 'normal',
    disponibilite     NUMERIC(5,2) DEFAULT 100,
    temperature       NUMERIC(5,2),
    cpu               NUMERIC(5,2),
    date_mesure       TIMESTAMP    DEFAULT NOW()
);

-- ── TABLE: mesures ───────────────────────────────────────────
-- Métriques conservées : temperature, cpu, signal, latence, disponibilite
CREATE TABLE mesures (
    id            SERIAL PRIMARY KEY,
    antenne_id    INTEGER      NOT NULL REFERENCES antennes(id) ON DELETE CASCADE,
    temperature   NUMERIC(5,2) CHECK (temperature >= -10 AND temperature <= 80),
    cpu           NUMERIC(5,2) CHECK (cpu >= 0 AND cpu <= 100),
    signal        NUMERIC(5,2),           -- RSSI en dBm (ex: -75 dBm)
    latence       NUMERIC(8,2),           -- Latence en ms
    disponibilite NUMERIC(5,2),           -- Disponibilité réseau en %
    -- Colonnes remplies par l'IA Isolation Forest
    statut        VARCHAR(30)  DEFAULT NULL,
    risk_score    NUMERIC(5,2) DEFAULT 0,
    date_mesure   TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX idx_mesures_antenne_date ON mesures(antenne_id, date_mesure DESC);

-- ── TABLE: audit_logs ────────────────────────────────────────
CREATE TABLE audit_logs (
    id          SERIAL PRIMARY KEY,
    utilisateur VARCHAR(100) NOT NULL,
    action      VARCHAR(255) NOT NULL,
    cible       VARCHAR(255),
    date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── TABLE: historique_etats ──────────────────────────────────
CREATE TABLE historique_etats (
    id              SERIAL PRIMARY KEY,
    antenne_id      INTEGER NOT NULL REFERENCES antennes(id) ON DELETE CASCADE,
    ancien_etat     VARCHAR(30),
    nouvel_etat     VARCHAR(30) NOT NULL,
    date_changement TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_historique_antenne ON historique_etats(antenne_id, date_changement DESC);

-- ── TABLE: incidents ─────────────────────────────────────────
CREATE TABLE incidents (
    id               SERIAL PRIMARY KEY,
    antenne_id       INTEGER      NOT NULL REFERENCES antennes(id) ON DELETE CASCADE,
    titre            VARCHAR(255) NOT NULL,
    type_anomalie    VARCHAR(100) DEFAULT 'Anomalie Réseau',
    description      TEXT,
    statut           VARCHAR(50)  DEFAULT 'en_cours',
    criticite        VARCHAR(50)  DEFAULT 'warning',
    source_detection VARCHAR(100) DEFAULT 'Isolation Forest',
    metriques        JSONB        DEFAULT '{}'::jsonb,
    risk_score       NUMERIC(5,2) DEFAULT 0,
    duree_minutes    INTEGER      DEFAULT 30,
    date_creation    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    date_resolution  TIMESTAMP
);

-- ── TABLE: commentaires_incidents ────────────────────────────
CREATE TABLE commentaires_incidents (
    id                 SERIAL PRIMARY KEY,
    incident_id        INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
    utilisateur_id     INTEGER,
    utilisateur_nom    VARCHAR(100),
    role               VARCHAR(50),
    contenu            TEXT NOT NULL,
    statut_validation  VARCHAR(30) DEFAULT 'en_attente',
    etat_resolution    VARCHAR(30) DEFAULT 'en_cours',
    date_creation      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── VIEW: antennes_statut ────────────────────────────────────
CREATE VIEW antennes_statut AS
SELECT DISTINCT ON (m.antenne_id)
    a.id,
    a.nom,
    a.zone,
    a.type,
    a.date_installation,
    m.temperature,
    m.cpu,
    m.signal,
    m.signal AS signal_strength,
    m.latence,
    m.disponibilite,
    COALESCE(a.statut, 'normal')     AS statut,
    COALESCE(m.risk_score, 0)        AS risk_score,
    CASE WHEN COALESCE(a.statut,'') = 'critique' THEN true ELSE false END AS anomalie,
    a.latitude,
    a.longitude,
    m.date_mesure
FROM antennes a
JOIN mesures m ON a.id = m.antenne_id
ORDER BY m.antenne_id, m.date_mesure DESC;

-- ── VIEW: antennes_geo ───────────────────────────────────────
CREATE VIEW antennes_geo AS
SELECT
    a.id,
    a.nom,
    a.zone,
    a.type,
    a.operateur,
    COALESCE(s.temperature, 0)   AS temperature,
    COALESCE(s.cpu, 0)           AS cpu,
    COALESCE(s.statut, 'normal') AS statut,
    a.geom
FROM antennes a
LEFT JOIN antennes_statut s ON s.id = a.id;

-- ── SEED: 120 antennes réparties sur 9 zones de Mahdia ───────
DO $$
DECLARE
    zones TEXT[][] := ARRAY[
        ARRAY['Mahdia Centre', '35.504', '11.030', '0.020', '16'],
        ARRAY['Hiboun',        '35.520', '11.020', '0.014', '13'],
        ARRAY['Ksour Essef',   '35.414', '10.980', '0.020', '13'],
        ARRAY['Boumerdes',     '35.438', '10.721', '0.022', '13'],
        ARRAY['Chebba',        '35.230', '11.000', '0.020', '13'],
        ARRAY['El Jem',        '35.292', '10.711', '0.024', '13'],
        ARRAY['Mellouleche',   '35.176', '10.990', '0.018', '13'],
        ARRAY['Sidi Alouane',  '35.367', '10.931', '0.018', '13'],
        ARRAY['Rejiche',       '35.471', '11.015', '0.014', '13']
    ];
    z TEXT[];
    i INTEGER := 1;
    j INTEGER;
    lat_pt NUMERIC;
    lon_pt NUMERIC;
    lat_c NUMERIC;
    lon_c NUMERIC;
    spread NUMERIC;
    nb INTEGER;
    tech TEXT;
BEGIN
    FOREACH z SLICE 1 IN ARRAY zones LOOP
        lat_c  := z[2]::NUMERIC;
        lon_c  := z[3]::NUMERIC;
        spread := z[4]::NUMERIC;
        nb     := z[5]::INTEGER;

        FOR j IN 1..nb LOOP
            lat_pt := lat_c + ((abs(hashtext(i::TEXT || z[1]))        % 1000) / 1000.0 * spread) - (spread / 2);
            lon_pt := lon_c + ((abs(hashtext(i::TEXT || z[1] || 'x')) % 1000) / 1000.0 * spread) - (spread / 2);
            tech   := CASE WHEN (i % 10) IN (0, 3, 7) THEN '5G' ELSE '4G' END;

            INSERT INTO antennes (nom, zone, type, latitude, longitude, date_installation, geom)
            VALUES (
                'TT-' || LPAD(i::TEXT, 3, '0'),
                z[1],
                tech,
                ROUND(lat_pt, 6),
                ROUND(lon_pt, 6),
                DATE '2018-01-01' + ((i * 17) % 2400),
                ST_SetSRID(ST_MakePoint(ROUND(lon_pt, 6), ROUND(lat_pt, 6)), 4326)
            );
            i := i + 1;
        END LOOP;
    END LOOP;
END $$;

-- ── SEED: Antenne IoT réelle — ISET Mahdia ──────────────────
-- Antenne physique : Arduino Uno + DHT11
-- Coordonnées GPS : 35.522473 N, 11.030388 E  (ISET Mahdia, Tunisie)
-- Zone : Mahdia Nord (géographiquement la plus proche)
-- ID attribué par PostgreSQL : 121 (après les 120 antennes simulées)
-- IMPORTANT : si la base est recréée, vérifier l'ID avec :
--   SELECT id FROM antennes WHERE nom = 'ISET Mahdia';
INSERT INTO antennes (nom, zone, type, latitude, longitude, operateur, date_installation, geom)
VALUES (
    'ISET Mahdia',
    'Mahdia Nord',
    '4G',
    35.522473,
    11.030388,
    'Tunisie Telecom',
    CURRENT_DATE,
    ST_SetSRID(ST_MakePoint(11.030388, 35.522473), 4326)
);


-- ── SEED: 6 mesures initiales par antenne (historique démo) ──
-- OBJECTIF : toutes les antennes démarrent en état NORMAL.
-- Valeurs centrées autour du comportement sain du réseau :
--   Température  ≈ 28°C     (plage 24–32°C)
--   CPU         ≈ 40%      (plage 30–50%)
--   Signal      ≈ -65 dBm  (plage -75 à -55 dBm)
--   Latence     ≈ 15 ms    (plage 10–22 ms)
--   Disponibilité ≈ 99%    (plage 98.5–99.5%)
--
-- IMPORTANT : aucune anomalie artificielle injectée.
-- Le modèle Isolation Forest apprend ce comportement normal et détecte
-- les écarts par rapport à lui — sans règle codée en dur.
DO $$
DECLARE
    ant RECORD;
    k INTEGER;
    base_cpu    NUMERIC;
    base_temp   NUMERIC;
    base_latence NUMERIC;
    base_dispo  NUMERIC;
    signal_dbm  NUMERIC;
BEGIN
    FOR ant IN SELECT id, type FROM antennes ORDER BY id LOOP
        -- CPU centré autour de 40% (plage 30–50%)
        base_cpu     := 30 + (ant.id % 20);

        -- Température centrée autour de 28°C (plage 24–32°C)
        -- Corrélation thermique légère avec le CPU (équipements qui chauffent)
        base_temp    := 24 + (ant.id % 8) + (base_cpu * 0.02);

        -- Latence centrée autour de 15 ms (plage 10–22 ms)
        base_latence := 10 + (ant.id % 12);

        -- Disponibilité centrée autour de 99% (plage 98.5–99.5%)
        base_dispo   := 98.5 + ((ant.id % 10) / 20.0);

        -- Signal RSSI centré autour de -65 dBm (plage -75 à -55 dBm)
        signal_dbm   := -75 + (ant.id % 20);

        -- Toutes les antennes : comportement normal, aucune anomalie injectée.
        -- L'Isolation Forest découvrira les écarts réels par lui-même.

        FOR k IN 1..6 LOOP
            INSERT INTO mesures (antenne_id, temperature, cpu, signal, latence, disponibilite, statut, risk_score, date_mesure)
            VALUES (
                ant.id,
                -- Progression douce sur les 6 mesures (évolution temporelle réaliste)
                ROUND(LEAST(45.0, GREATEST(15.0, base_temp    + (k - 4) * 0.2))::NUMERIC, 2),
                ROUND(GREATEST(10.0, LEAST(80.0,  base_cpu     + (k - 4) * 0.5))::NUMERIC, 2),
                ROUND((signal_dbm   + (k % 3) * 0.3)::NUMERIC, 2),
                ROUND(GREATEST(5.0,              base_latence + (k - 4) * 0.4)::NUMERIC,  2),
                ROUND(LEAST(100.0, GREATEST(97.0, base_dispo   - (k % 2) * 0.03))::NUMERIC, 2),
                'normal',
                0,
                NOW() - ((6 - k) * INTERVAL '30 minutes')
            );
        END LOOP;
    END LOOP;
END $$;


-- ── Mesure initiale pour l'antenne ISET Mahdia ───────────────
-- Valeurs de départ correspondant au profil de la zone Hiboun
-- La température réelle viendra de l'Arduino via serial_bridge.py
-- Les autres métriques seront simulées avec transition douce
INSERT INTO mesures (antenne_id, temperature, cpu, signal, latence, disponibilite, statut, risk_score, date_mesure)
SELECT id, 28.0, 38.0, -61.0, 12.0, 99.5, 'normal', 0, NOW()
FROM antennes
WHERE nom = 'ISET Mahdia';

