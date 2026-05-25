/*
 * ================================================================
 *  GEO-TELECOM NOC — Antenne IoT ISET Mahdia
 *  Arduino Uno + DHT11 — Communication Serial USB
 *  PFE Licence — Réseaux & Télécommunications 2025/2026
 *  Auteurs : Malek Maadi & Abir Said
 * ================================================================
 *
 *  Matériel requis :
 *    - Carte  : Arduino Uno
 *    - Capteur: DHT11 (température)
 *    - Câblage DHT11 :
 *        VCC  -> 5V
 *        GND  -> GND
 *        DATA -> Pin 2 (avec résistance pull-up 10kΩ entre DATA et VCC)
 *
 *  Librairies Arduino nécessaires (Gestionnaire de bibliothèques) :
 *    - "DHT sensor library" by Adafruit
 *    - "Adafruit Unified Sensor" by Adafruit
 *
 *  Fonctionnement :
 *    1. Toutes les INTERVALLE_ENVOI secondes, lit la température du DHT11
 *    2. Envoie un JSON sur Serial (115200 baud)
 *    3. serial_bridge.py reçoit le JSON et l'envoie à l'API Flask -> /iot/mesure
 *    4. L'IA analyse automatiquement les nouvelles mesures
 *
 *  Format JSON envoyé (une ligne) :
 *    {"antenne_id":121,"temperature":28.5}
 *
 *  Les lignes commençant par '#' sont des logs (ignorés par serial_bridge.py).
 *
 * ================================================================
 *
 *  CONFIGURATION DE L'INTERVALLE :
 *
 *  MODE DÉMONSTRATION (jury) : INTERVALLE_ENVOI = 10
 *    -> Envoi toutes les 10 secondes
 *    -> Permet de voir les changements rapidement sur le dashboard
 *    -> Idéal pour montrer l'effet du chauffage du capteur DHT11
 *
 *  MODE NORMAL (production) : INTERVALLE_ENVOI = 30
 *    -> Envoi toutes les 30 secondes
 *    -> Moins de données, plus adapté à une utilisation longue durée
 *
 *  Changer uniquement la ligne INTERVALLE_ENVOI ci-dessous.
 *
 * ================================================================
 *
 *  IDENTIFIANT DE L'ANTENNE :
 *
 *  L'antenne "ISET Mahdia" a l'identifiant 121 dans la base de données
 *  (elle est insérée après les 120 antennes simulées TT-001 à TT-120).
 *
 *  Pour vérifier en cas de doute :
 *    SELECT id FROM antennes WHERE nom = 'ISET Mahdia';
 *  -> devrait retourner 121
 *
 *  Si la base est recréée et l'ID change, modifier ANTENNE_ID ci-dessous.
 *
 * ================================================================
 */

#include <DHT.h>

// ----------------------------------------------------------------
//  CONFIGURATION — modifier ces valeurs si nécessaire
// ----------------------------------------------------------------

#define DHT_PIN   2       // Broche DATA du DHT11 (avec résistance pull-up)
#define DHT_TYPE  DHT11   // Type de capteur

// ── IDENTIFIANT DE L'ANTENNE ─────────────────────────────────────
//
//  L'antenne "ISET Mahdia" a l'identifiant 121 dans la base de données
//  PostgreSQL (elle est insérée après les 120 antennes simulées TT-001
//  à TT-120).
//
//  IMPORTANT : l'identifiant réel est récupéré automatiquement par
//  serial_bridge.py au démarrage via :
//    GET /iot/antenne/lookup?nom=ISET+Mahdia&create=1&lat=35.522473&lon=11.030388
//
//  La valeur ci-dessous (121) est utilisée UNIQUEMENT comme fallback si
//  serial_bridge.py ne peut pas interroger l'API (hors-ligne, etc.).
//
//  Pour vérifier l'ID réel en base de données :
//    SELECT id FROM antennes WHERE nom = 'ISET Mahdia';
//
//  Si la base est recréée et l'ID change, mettre à jour cette valeur.
//
const int ANTENNE_ID = 121;   // fallback — serial_bridge.py récupère l'ID réel

// ── INTERVALLE D'ENVOI (en secondes) ─────────────────────────────
//
//   MODE DÉMONSTRATION : 10 secondes (défaut — recommandé pour le jury)
//   MODE NORMAL        : 30 secondes (changer la valeur ci-dessous)
//
const unsigned int INTERVALLE_ENVOI = 10;   // secondes


// ----------------------------------------------------------------
//  VARIABLES GLOBALES (ne pas modifier)
// ----------------------------------------------------------------

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long dernierEnvoi = 0;
int compteur = 0;

// ----------------------------------------------------------------
//  SETUP — exécuté une seule fois au démarrage
// ----------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(1500);  // Stabilisation du DHT11 (nécessite 1-2 secondes)

  // Messages de démarrage (commencent par '#' : ignorés par serial_bridge.py)
  Serial.println("# ============================================");
  Serial.println("# GEO-TELECOM NOC -- Arduino Uno");
  Serial.println("# Antenne    : ISET Mahdia");
  Serial.print("# Antenne ID : ");
  Serial.println(ANTENNE_ID);
  Serial.println("# Capteur    : DHT11 (Pin 2)");
  Serial.println("# Metrique   : Temperature exterieure");
  Serial.print("# Intervalle : ");
  Serial.print(INTERVALLE_ENVOI);
  Serial.println("s");
  if (INTERVALLE_ENVOI <= 10) {
    Serial.println("# Mode       : DEMONSTRATION ");
  } else {
    Serial.println("# Mode       : NORMAL (production)");
  }
  Serial.println("# ============================================");
  Serial.println("# En attente de la premiere lecture DHT11...");

  dht.begin();
}

// ----------------------------------------------------------------
//  LOOP — exécuté en boucle
// ----------------------------------------------------------------

void loop() {
  unsigned long maintenant = millis();
  unsigned long intervalle_ms = (unsigned long)INTERVALLE_ENVOI * 1000UL;

  // Vérifier si l'intervalle est écoulé
  if (maintenant - dernierEnvoi >= intervalle_ms) {
    dernierEnvoi = maintenant;
    lireEtEnvoyer();
  }
}

// ----------------------------------------------------------------
//  LECTURE DHT11 ET ENVOI JSON SUR SERIAL
// ----------------------------------------------------------------

void lireEtEnvoyer() {
  compteur++;

  // Lecture de la température du DHT11
  float temperature = dht.readTemperature();   // degrés Celsius

  // Vérification de validité (NaN = erreur de lecture)
  if (isnan(temperature)) {
    Serial.println("# ERREUR : Lecture DHT11 echouee -- verifier le cablage");
    Serial.println("# Conseil : verifier la resistance pull-up 10kOhm sur DATA");
    return;
  }

  // Arrondi à 1 décimale
  temperature = (float)((int)(temperature * 10 + 0.5)) / 10.0;

  // ── Envoi JSON sur Serial ──────────────────────────────────────
  // Format attendu par serial_bridge.py et l'API /iot/mesure
  // Une seule ligne, sans espaces inutiles
  Serial.print("{\"antenne_id\":");
  Serial.print(ANTENNE_ID);
  Serial.print(",\"temperature\":");
  Serial.print(temperature, 1);
  Serial.println("}");

  // ── Log de debug ───────────────────────────────────────────────
  // Lignes commençant par '#' : ignorées par serial_bridge.py
  Serial.print("# Cycle ");
  Serial.print(compteur);
  Serial.print(" | Temp=");
  Serial.print(temperature, 1);
  Serial.print("C | Prochain envoi dans ");
  Serial.print(INTERVALLE_ENVOI);
  Serial.println("s");
}
