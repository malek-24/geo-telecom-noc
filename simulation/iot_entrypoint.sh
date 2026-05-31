#!/bin/sh
echo "[IOT-BRIDGE] Démarrage passerelle capteur..."

MODE="${IOT_MODE:-simulate}"
API="${API_URL:-http://api:5000}"

if [ "$MODE" = "serial" ]; then
  PORT="${IOT_SERIAL_PORT:-COM3}"
  echo "[IOT-BRIDGE] Mode SERIAL — port $PORT"
  exec python -u serial_bridge.py --port "$PORT" --api "$API"
else
  echo "[IOT-BRIDGE] Mode SIMULATE (DHT11 simulé — logs Docker Desktop)"
  exec python -u simulate_dht11_docker.py
fi
