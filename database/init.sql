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
    temperature   NUMERIC(5,2) CHECK (temperature > 0),
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
    COALESCE(m.statut, 'en_attente') AS statut,
    COALESCE(m.risk_score, 0)        AS risk_score,
    CASE WHEN COALESCE(m.statut,'') = 'critique' THEN true ELSE false END AS anomalie,
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
        ARRAY['Rejiche',       '35.471', '11.015', '0.014', '11']
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

-- ── SEED: 6 mesures initiales par antenne (historique démo) ──
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
        base_cpu     := 22 + (ant.id % 38);
        base_temp    := 36 + (ant.id % 18) + base_cpu * 0.07;
        base_latence := 10 + (ant.id % 24);
        base_dispo   := 97.5 + ((ant.id % 20) / 40.0);
        signal_dbm   := -85  + (ant.id % 32);

        -- Anomalies réalistes sur des sites spécifiques
        IF ant.id IN (17, 46, 88, 112) THEN
            base_cpu     := base_cpu + 38;
            base_temp    := base_temp + 20;
            base_latence := base_latence + 48;
            base_dispo   := 92.5;
        ELSIF ant.id IN (29, 63, 104) THEN
            base_cpu     := base_cpu + 18;
            base_temp    := base_temp + 10;
            base_latence := base_latence + 22;
        END IF;

        FOR k IN 1..6 LOOP
            INSERT INTO mesures (antenne_id, temperature, cpu, signal, latence, disponibilite, statut, risk_score, date_mesure)
            VALUES (
                ant.id,
                ROUND((base_temp    + (k - 4) * 0.5) ::NUMERIC, 2),
                ROUND((base_cpu     + (k - 4) * 0.8) ::NUMERIC, 2),
                ROUND((signal_dbm   + (k % 3) * 0.5) ::NUMERIC, 2),
                ROUND((base_latence + (k - 4) * 0.7) ::NUMERIC, 2),
                ROUND((base_dispo   - (k % 2) * 0.05)::NUMERIC, 2),
                NULL,
                0,
                NOW() - ((6 - k) * INTERVAL '30 minutes')
            );
        END LOOP;
    END LOOP;
END $$;
