-- =============================================================
-- Tunisie Telecom NOC — PostgreSQL/PostGIS initialization
-- PFE Licence — Supervision intelligente des antennes — 2026
-- Mahdia, Tunisie — 120 antennes, 9 zones
-- 
-- ARCHITECTURE IA :
--   Le simulateur insère des mesures brutes SANS statut.
--   L'IA Isolation Forest (API Flask) calcule ensuite :
--     - risk_score (0-100)
--     - statut IA : 'normal' | 'alerte' | 'critique'
-- =============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

DROP VIEW  IF EXISTS antennes_geo    CASCADE;
DROP VIEW  IF EXISTS antennes_statut CASCADE;
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
    -- Colonnes résumé (mises à jour par l'IA après chaque cycle)
    statut            VARCHAR(30)  DEFAULT 'normal',  -- 'normal' | 'alerte' | 'critique'
    disponibilite     NUMERIC(5,2) DEFAULT 100,
    temperature       NUMERIC(5,2),
    cpu               NUMERIC(5,2),
    debit             NUMERIC(8,2),
    date_mesure       TIMESTAMP    DEFAULT NOW()
);

-- ── TABLE: mesures ───────────────────────────────────────────
-- Une ligne par antenne par cycle de 30 minutes.
-- Le statut est initialement NULL — l'IA le remplit après analyse.
CREATE TABLE mesures (
    id            SERIAL PRIMARY KEY,
    antenne_id    INTEGER      NOT NULL REFERENCES antennes(id) ON DELETE CASCADE,
    temperature   NUMERIC(5,2) CHECK (temperature > 0),
    cpu           NUMERIC(5,2) CHECK (cpu >= 0 AND cpu <= 100),
    ram           NUMERIC(5,2) CHECK (ram >= 0 AND ram <= 100),
    signal        NUMERIC(5,2),            -- RSSI en dBm
    traffic       NUMERIC(8,2) DEFAULT 0,  -- Débit en Mbps
    latence       NUMERIC(8,2),            -- Latence en ms
    packet_loss   NUMERIC(5,2) DEFAULT 0,  -- Perte paquets en %
    jitter        NUMERIC(5,2) DEFAULT 0,  -- Gigue en ms
    disponibilite NUMERIC(5,2),            -- Disponibilité réseau en %
    -- Colonnes remplies par l'IA Isolation Forest
    statut        VARCHAR(30)  DEFAULT NULL, -- NULL = en attente d'analyse IA
    risk_score    NUMERIC(5,2) DEFAULT 0,
    date_mesure   TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX idx_mesures_antenne_date ON mesures(antenne_id, date_mesure DESC);

-- ── TABLE: incidents ─────────────────────────────────────────
-- Créés et résolus automatiquement par l'IA.
CREATE TABLE incidents (
    id               SERIAL PRIMARY KEY,
    antenne_id       INTEGER      NOT NULL REFERENCES antennes(id) ON DELETE CASCADE,
    titre            VARCHAR(255) NOT NULL,
    type_anomalie    VARCHAR(100) DEFAULT 'Anomalie Réseau',
    description      TEXT,
    statut           VARCHAR(50)  DEFAULT 'en_cours',  -- 'en_cours' | 'resolu'
    criticite        VARCHAR(50)  DEFAULT 'warning',   -- 'warning'  | 'critical'
    source_detection VARCHAR(100) DEFAULT 'Isolation Forest',
    metriques        JSONB        DEFAULT '{}'::jsonb,
    risk_score       NUMERIC(5,2) DEFAULT 0,
    duree_minutes    INTEGER      DEFAULT 30,
    date_creation    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    date_resolution  TIMESTAMP
);

-- ── VIEW: antennes_statut ────────────────────────────────────
-- Vue principale : dernière mesure par antenne, enrichie par l'IA.
-- C'est LA source de vérité pour toutes les pages du dashboard.
CREATE VIEW antennes_statut AS
SELECT DISTINCT ON (m.antenne_id)
    a.id,
    a.nom,
    a.zone,
    a.type,
    a.date_installation,
    m.temperature,
    m.cpu,
    m.ram,
    m.signal,
    m.signal     AS signal_strength,
    m.traffic,
    m.traffic    AS debit,
    m.latence,
    COALESCE(m.packet_loss, 0) AS packet_loss,
    COALESCE(m.jitter, 0)      AS jitter,
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
-- Vue GeoServer : couche géospatiale pour la carte WMS.
CREATE VIEW antennes_geo AS
SELECT
    a.id,
    a.nom,
    a.zone,
    a.type,
    a.operateur,
    COALESCE(s.temperature, 0)   AS temperature,
    COALESCE(s.cpu, 0)           AS cpu,
    COALESCE(s.ram, 0)           AS ram,
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

-- ── SEED: 6 mesures initiales par antenne (3h d'historique) ──
-- Le statut est NULL — sera mis à jour par l'IA au premier démarrage.
DO $$
DECLARE
    ant RECORD;
    k INTEGER;
    base_cpu      NUMERIC;
    base_ram      NUMERIC;
    base_temp     NUMERIC;
    base_debit    NUMERIC;
    base_latence  NUMERIC;
    base_dispo    NUMERIC;
    base_pkt_loss NUMERIC;
    base_jitter   NUMERIC;
    signal_dbm    NUMERIC;
BEGIN
    FOR ant IN SELECT id, type FROM antennes ORDER BY id LOOP
        -- Valeurs de base déterministes basées sur l'ID de l'antenne
        base_cpu      := 22 + (ant.id % 38);
        base_ram      := 34 + (ant.id % 30);
        base_temp     := 36 + (ant.id % 18) + base_cpu * 0.07;
        base_latence  := 10 + (ant.id % 24);
        base_dispo    := 97.5 + ((ant.id % 20) / 40.0);
        base_pkt_loss := 0.1  + ((ant.id % 15) * 0.06);
        base_jitter   := 2.0  + (ant.id % 8);
        signal_dbm    := -85  + (ant.id % 32);

        IF ant.type = '5G' THEN
            base_debit := 120 + (ant.id % 8) * 25;
        ELSE
            base_debit := 55  + (ant.id % 8) * 18;
        END IF;

        -- Anomalies réalistes sur des sites spécifiques pour l'historique démo
        IF ant.id IN (17, 46, 88, 112) THEN
            base_cpu      := base_cpu + 38;
            base_ram      := base_ram + 22;
            base_temp     := base_temp + 20;
            base_latence  := base_latence + 48;
            base_dispo    := 92.5;
            base_pkt_loss := 3.2;
            base_jitter   := 18.0;
            base_debit    := base_debit * 0.4;
        ELSIF ant.id IN (29, 63, 104) THEN
            base_cpu      := base_cpu + 18;
            base_temp     := base_temp + 10;
            base_latence  := base_latence + 22;
            base_pkt_loss := 1.6;
            base_jitter   := 12.0;
        END IF;

        FOR k IN 1..6 LOOP
            INSERT INTO mesures (
                antenne_id, temperature, cpu, ram, signal, traffic, latence,
                packet_loss, jitter, disponibilite, statut, risk_score, date_mesure
            )
            VALUES (
                ant.id,
                ROUND((base_temp    + (k - 4) * 0.5) ::NUMERIC, 2),
                ROUND((base_cpu     + (k - 4) * 0.8) ::NUMERIC, 2),
                ROUND((base_ram     + (k - 4) * 0.4) ::NUMERIC, 2),
                ROUND((signal_dbm   + (k % 3) * 0.5) ::NUMERIC, 2),
                ROUND((base_debit   + (k - 4) * 2.0) ::NUMERIC, 2),
                ROUND((base_latence + (k - 4) * 0.7) ::NUMERIC, 2),
                ROUND(GREATEST(0, base_pkt_loss + (k-4)*0.04)::NUMERIC, 2),
                ROUND(GREATEST(0, base_jitter   + (k-4)*0.5) ::NUMERIC, 2),
                ROUND((base_dispo   - (k % 2) * 0.05)::NUMERIC, 2),
                NULL,   -- statut sera assigné par l'IA
                0,      -- risk_score sera calculé par l'IA
                NOW() - ((6 - k) * INTERVAL '30 minutes')
            );
        END LOOP;
    END LOOP;
END $$;
