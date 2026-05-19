/*
 * ================================================================
 *  GEO-TÉLÉCOM NOC — Capteur IoT ESP32 + DHT22
 *  PFE Licence 3 — Réseaux & Télécommunications 2025/2026
 *  Auteurs : Malek Maadi & Abir Said
 * ================================================================
 *
 *  Matériel requis :
 *    - Carte : ESP32 (ESP32-WROOM-32 ou ESP32 DevKitC)
 *    - Capteur : DHT22 (AM2302) → Température + Humidité
 *    - Câblage DHT22 :
 *        VCC  → 3.3V (pin 3V3 de l'ESP32)
 *        GND  → GND
 *        DATA → GPIO 4 (avec résistance pull-up 10kΩ entre DATA et VCC)
 *
 *  Librairies Arduino nécessaires (Gestionnaire de bibliothèques) :
 *    - "DHT sensor library" by Adafruit
 *    - "Adafruit Unified Sensor" by Adafruit
 *    - "ArduinoJson" by Benoit Blanchon (version 6.x)
 *    - "HTTPClient" (incluse avec ESP32)
 *
 *  Fonctionnement :
 *    1. L'ESP32 se connecte au WiFi
 *    2. Toutes les 30 secondes, il lit la température du DHT22
 *    3. Il envoie un POST JSON à l'API Flask → /iot/mesure
 *    4. L'API insère la mesure en DB et déclenche l'IA
 *
 *  Configuration : modifiez les defines ci-dessous
 * ================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ─── CONFIGURATION — À MODIFIER ──────────────────────────────────

// WiFi
const char* WIFI_SSID     = "VOTRE_WIFI";        // ← Nom de votre réseau WiFi
const char* WIFI_PASSWORD = "VOTRE_MOT_DE_PASSE"; // ← Mot de passe WiFi

// API Flask — Adresse IP de votre PC (pas localhost !)
// Sur Windows : ipconfig → "Adresse IPv4"
const char* API_HOST      = "192.168.1.100";      // ← IP de votre PC (ex: 192.168.1.100)
const int   API_PORT      = 7000;                  // Port exposé par Docker
const char* API_KEY       = "esp32-noc-secret-2026"; // Doit correspondre à IOT_API_KEY dans Flask

// ID de l'antenne dans la base de données à laquelle cet ESP32 est associé
const int   ANTENNE_ID    = 1;                    // ← ID d'une antenne réelle en DB

// Capteur DHT22
#define DHT_PIN  4         // GPIO 4 — broche DATA du DHT22
#define DHT_TYPE DHT22     // Type de capteur : DHT22 (AM2302)

// Intervalle d'envoi (millisecondes)
const unsigned long INTERVALLE_MS = 30000;  // 30 secondes

// ─── VARIABLES GLOBALES ───────────────────────────────────────────

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long dernierEnvoi = 0;
int compteurEnvois         = 0;
int compteurErreurs        = 0;

// ─── SETUP ───────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n========================================");
  Serial.println("  GEO-TÉLÉCOM NOC — Capteur IoT ESP32  ");
  Serial.println("========================================");

  // Initialisation DHT22
  dht.begin();
  Serial.println("[DHT22] Capteur initialisé sur GPIO " + String(DHT_PIN));

  // Connexion WiFi
  connecterWiFi();
}

// ─── LOOP ─────────────────────────────────────────────────────────

void loop() {
  // Vérifie la connexion WiFi et reconnecte si nécessaire
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Connexion perdue — reconnexion...");
    connecterWiFi();
  }

  // Envoi toutes les INTERVALLE_MS millisecondes
  unsigned long maintenant = millis();
  if (maintenant - dernierEnvoi >= INTERVALLE_MS) {
    dernierEnvoi = maintenant;
    lireEtEnvoyer();
  }
}

// ─── CONNEXION WIFI ───────────────────────────────────────────────

void connecterWiFi() {
  Serial.print("[WiFi] Connexion à : ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int tentatives = 0;
  while (WiFi.status() != WL_CONNECTED && tentatives < 20) {
    delay(500);
    Serial.print(".");
    tentatives++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] ✅ Connecté !");
    Serial.print("[WiFi] Adresse IP ESP32 : ");
    Serial.println(WiFi.localIP());
    Serial.print("[WiFi] Signal RSSI : ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n[WiFi] ❌ Échec de connexion. Vérifiez SSID/Password.");
  }
}

// ─── LECTURE DHT22 ET ENVOI API ──────────────────────────────────

void lireEtEnvoyer() {
  compteurEnvois++;
  Serial.println("\n--- Cycle #" + String(compteurEnvois) + " ---");

  // Lecture température et humidité
  float temperature = dht.readTemperature();  // En °C
  float humidite    = dht.readHumidity();     // En %

  // Vérification validité lecture
  if (isnan(temperature) || isnan(humidite)) {
    Serial.println("[DHT22] ❌ Erreur de lecture — câblage ou capteur défaillant ?");
    compteurErreurs++;
    return;
  }

  Serial.print("[DHT22] 🌡️  Température : ");
  Serial.print(temperature, 1);
  Serial.println(" °C");

  Serial.print("[DHT22] 💧  Humidité    : ");
  Serial.print(humidite, 1);
  Serial.println(" %");

  // Construction du JSON à envoyer (5 métriques conservées)
  StaticJsonDocument<256> doc;
  doc["antenne_id"]    = ANTENNE_ID;
  doc["temperature"]   = round(temperature * 10.0) / 10.0;
  doc["cpu"]           = simulerCPU(temperature);
  doc["signal"]        = WiFi.RSSI();   // Signal WiFi réel de l'ESP32
  doc["latence"]       = random(5, 50);
  doc["disponibilite"] = (temperature < 70.0) ? 99.5 : 85.0;

  String jsonBody;
  serializeJson(doc, jsonBody);

  Serial.print("[API] Envoi vers http://");
  Serial.print(API_HOST);
  Serial.print(":");
  Serial.print(API_PORT);
  Serial.println("/iot/mesure");
  Serial.print("[API] Body : ");
  Serial.println(jsonBody);

  // Envoi HTTP POST
  envoyerMesure(jsonBody);
}

// ─── ENVOI HTTP POST ──────────────────────────────────────────────

void envoyerMesure(String jsonBody) {
  HTTPClient http;

  String url = "http://" + String(API_HOST) + ":" + String(API_PORT) + "/iot/mesure";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key",    API_KEY);
  http.setTimeout(10000);  // 10 secondes timeout

  int httpCode = http.POST(jsonBody);

  if (httpCode > 0) {
    String reponse = http.getString();
    if (httpCode == 201) {
      Serial.println("[API] ✅ Mesure acceptée ! HTTP 201");
      Serial.print("[API] Réponse : ");
      Serial.println(reponse);
    } else {
      Serial.print("[API] ⚠️  HTTP ");
      Serial.print(httpCode);
      Serial.print(" — ");
      Serial.println(reponse);
      compteurErreurs++;
    }
  } else {
    Serial.print("[API] ❌ Erreur réseau : ");
    Serial.println(http.errorToString(httpCode));
    Serial.println("[API] Vérifiez que Docker tourne et que l'IP est correcte.");
    compteurErreurs++;
  }

  http.end();

  // Affichage des statistiques
  Serial.print("[STATS] Envois : ");
  Serial.print(compteurEnvois);
  Serial.print(" | Erreurs : ");
  Serial.print(compteurErreurs);
  Serial.print(" | Taux succès : ");
  int taux = compteurEnvois > 0 ? ((compteurEnvois - compteurErreurs) * 100 / compteurEnvois) : 0;
  Serial.print(taux);
  Serial.println("%");
}

// ─── SIMULATION CPU basée sur température ────────────────────────
// Plus la température est élevée, plus le CPU est chargé
float simulerCPU(float temp) {
  if (temp < 35.0) return random(10, 30);
  if (temp < 50.0) return random(30, 55);
  if (temp < 65.0) return random(55, 75);
  if (temp < 80.0) return random(75, 90);
  return random(88, 100);  // Surchauffe critique
}
