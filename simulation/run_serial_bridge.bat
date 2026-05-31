@echo off
REM Passerelle Arduino DHT11 -> API Flask (Windows)
cd /d "%~dp0.."
echo.
echo  GEO-TELECOM NOC - serial_bridge (COM3, API localhost:7000)
echo  Arreter avec Ctrl+C
echo.
python -u simulation\serial_bridge.py --port COM3 --api http://localhost:7000
if errorlevel 1 (
  echo.
  echo [ERREUR] Verifiez : Docker demarre, Arduino branche, pip install pyserial requests
  pause
)
