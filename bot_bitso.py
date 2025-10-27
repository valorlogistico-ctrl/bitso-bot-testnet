# ==========================================================
# 🤖 BITSO BOT TESTNET (versión con heartbeat y reinicio diario)
# Autor: Jorge Macías / valorlogistico-ctrl
# ==========================================================

import os
import csv
import time
import requests
import logging
import sys
from datetime import datetime, timedelta
import ccxt
from dotenv import load_dotenv

# ==========================================================
# ⚙️ CONFIGURACIÓN INICIAL
# ==========================================================

load_dotenv()

BITSO_API_KEY = os.getenv("BITSO_API_KEY")
BITSO_API_SECRET = os.getenv("BITSO_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "BTC/MXN"
INTERVAL = 300  # 5 minutos
COMISION_MAKER = 0.003  # 0.3%
CSV_FILE = "bitso_trades.csv"

balance_neto = 0.0
ultimo_trade = datetime.now() - timedelta(days=1)
ultimo_heartbeat = datetime.now() - timedelta(hours=1)
ultimo_reinicio = datetime.now().date()

# ==========================================================
# 🧾 LOGGING
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ==========================================================
# 📡 FUNCIÓN: Enviar mensaje a Telegram
# ==========================================================
def enviar_telegram(mensaje):
    """Envía mensajes al chat de Telegram configurado."""
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
            requests.post(url, data=data)
    except Exception as e:
        logging.warning(f"⚠️ Error enviando Telegram: {e}")

# ==========================================================
# 💾 FUNCIÓN: Registrar operación
# ==========================================================
def registrar_operacion(par, accion, precio, monto, comision_pct):
    global balance_neto, ultimo_trade
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comision = precio * monto * comision_pct
    resultado_neto = -(precio * monto + comision) if accion == "BUY" else (precio * monto - comision)
    balance_neto += resultado_neto
    ultimo_trade = datetime.now()

    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        if not file_exists:
            writer.writerow(["timestamp", "par", "acción", "precio", "monto", "comisión", "resultado_neto"])
        writer.writerow([fecha, par, accion, precio, monto, comision, resultado_neto])

    mensaje = f"{'🟢 Compra' if accion == 'BUY' else '🔴 Venta'} {par} — {monto:.6f} BTC ejecutados | Balance actual: {balance_neto:,.2f} MXN"
    enviar_telegram(mensaje)
    logging.info(f"💾 {accion} {monto} BTC @ {precio} | Balance: {balance_neto:.2f}")

# ==========================================================
# 🧮 FUNCIÓN: Calcular monto óptimo
# ==========================================================
def calcular_monto_optimo(precio_actual, balance_mxn=1000):
    MONTO_BASE = 0.0001
    max_monto = balance_mxn / precio_actual
    monto_final = min(MONTO_BASE * 5, max_monto)
    return round(monto_final, 6)

# ==========================================================
# 💓 HEARTBEAT (verificador de vida del bot)
# ==========================================================
def heartbeat():
    """Envía mensaje de confirmación solo si no hubo operaciones recientes."""
    global ultimo_heartbeat
    ahora = datetime.now()
    if (ahora - ultimo_heartbeat).total_seconds() >= 3600:
        horas_desde_trade = (ahora - ultimo_trade).total_seconds() / 3600
        if horas_desde_trade >= 2:
            enviar_telegram(f"💓 Bot activo | {ahora.strftime('%d %b %H:%M')} | Sin trades recientes (último hace {horas_desde_trade:.1f}h)")
            logging.info("💓 Heartbeat enviado (sin actividad reciente).")
        ultimo_heartbeat = ahora

# ==========================================================
# 🔁 FUNCIÓN: Reinicio diario
# ==========================================================
def verificar_reinicio_diario():
    """Reinicia el bot automáticamente todos los días a las 06:00 AM."""
    global ultimo_reinicio
    ahora = datetime.now()
    hora_actual = ahora.time()
    if hora_actual.hour == 6 and hora_actual.minute < 5:  # ventana de 5 min
        if ultimo_reinicio != ahora.date():
            enviar_telegram("🔄 Reinicio automático diario a las 06:00 AM")
            logging.info("🔄 Reinicio automático iniciado...")
            ultimo_reinicio = ahora.date()
            sys.exit(0)  # Render relanza el servicio automáticamente

# ==========================================================
# 🔁 LOOP PRINCIPAL
# ==========================================================
def ejecutar_bot():
    logging.info("🤖 Iniciando bot automático profesional (Bitso Testnet)")

    exchange = ccxt.bitso({
        "apiKey": BITSO_API_KEY,
        "secret": BITSO_API_SECRET,
        "enableRateLimit": True,
    })

    while True:
        try:
            ticker = exchange.fetch_ticker(PAIR)
            precio_actual = ticker["last"]
            senal = "BUY" if int(time.time()) % 2 == 0 else "SELL"
            monto = calcular_monto_optimo(precio_actual)

            registrar_operacion(PAIR, senal, precio_actual, monto, COMISION_MAKER)
            heartbeat()
            verificar_reinicio_diario()

            time.sleep(INTERVAL)

        except Exception as e:
            logging.error(f"⚠️ Error en el ciclo: {e}")
            time.sleep(15)

# ==========================================================
# ▶️ EJECUCIÓN
# ==========================================================
if __name__ == "__main__":
    ejecutar_bot()

