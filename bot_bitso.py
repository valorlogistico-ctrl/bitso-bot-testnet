# ==========================================================
# 🤖 BITSO BOT TESTNET (versión profesional con heartbeat)
# Autor: Jorge Macías / valorlogistico-ctrl
# ==========================================================

import os
import csv
import time
import requests
import logging
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
    """Envía mensaje de confirmación cada hora."""
    global ultimo_heartbeat
    ahora = datetime.now()
    if (ahora - ultimo_heartbeat).total_seconds() >= 3600:  # cada hora
        enviar_telegram(f"💓 Bot activo | {ahora.strftime('%d %b %H:%M')} | Último trade hace {(ahora - ultimo_trade).seconds // 60} min")
        ultimo_heartbeat = ahora
        logging.info("💓 Heartbeat enviado correctamente.")

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

            time.sleep(INTERVAL)

        except Exception as e:
            logging.error(f"⚠️ Error en el ciclo: {e}")
            time.sleep(15)

# ==========================================================
# ▶️ EJECUCIÓN
# ==========================================================
if __name__ == "__main__":
    ejecutar_bot()

