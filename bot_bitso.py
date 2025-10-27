# ==========================================================
# 🤖 BITSO BOT TESTNET (versión con heartbeat y reinicio diario)
# Autor: Jorge Macías / valorlogistico-ctrl
# ==========================================================

import os
import time
import ccxt
import requests
import datetime
import logging
from dotenv import load_dotenv

# ==========================================================
# 🧩 CONFIGURACIÓN INICIAL
# ==========================================================
load_dotenv()

BITSO_API_KEY = os.getenv("BITSO_API_KEY")
BITSO_API_SECRET = os.getenv("BITSO_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "btc_mxn"
INTERVAL = 300  # Intervalo de operación en segundos (5 min)
COMISION_MAKER = 0.001

ultimo_heartbeat = None
ultimo_reinicio = datetime.date.today()
telegram_fails = 0  # contador de fallos consecutivos de Telegram

# ==========================================================
# 🪵 LOGGING
# ==========================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==========================================================
# 📡 FUNCIONES DE SOPORTE
# ==========================================================

def enviar_telegram(msg):
    """Envía mensajes a Telegram con reintentos y control de errores."""
    global telegram_fails
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        resp = requests.post(url, data=data, timeout=10)

        if resp.status_code == 200:
            telegram_fails = 0
            return True
        else:
            telegram_fails += 1
            logging.warning(f"⚠️ Fallo Telegram ({telegram_fails}/3): {resp.text}")
            if telegram_fails >= 3:
                logging.error("❌ Telegram sin respuesta (3 intentos fallidos)")
                requests.post(
                    url,
                    data={"chat_id": TELEGRAM_CHAT_ID,
                          "text": "⚠️ Error: Telegram sin respuesta (3 fallos seguidos)"}
                )
    except requests.exceptions.RequestException as e:
        telegram_fails += 1
        logging.error(f"🚫 Error conexión Telegram: {e}")
        if telegram_fails >= 3:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID,
                      "text": "⚠️ Problema persistente al conectar con Telegram."}
            )
    return False


def calcular_monto_optimo(precio):
    """Monto fijo simulado (ajústalo a tu balance real)."""
    return 100 / precio  # Compra equivalente a 100 MXN


def registrar_operacion(par, tipo, precio, monto, comision):
    """Guarda logs y simula operación."""
    logging.info(f"{tipo} {monto:.6f} BTC @ {precio:.2f} | Balance simulado")
    enviar_telegram(f"{'🟢 Compra' if tipo == 'BUY' else '🔴 Venta'} BTC/MXN — {monto:.6f} BTC ejecutados a {precio:,.2f} MXN")


def heartbeat():
    """Envía un mensaje de vida cada hora para confirmar que el bot sigue activo."""
    global ultimo_heartbeat
    ahora = datetime.datetime.now()
    if ultimo_heartbeat is None or (ahora - ultimo_heartbeat).total_seconds() >= 3600:
        enviar_telegram(f"💓 Heartbeat OK — Bot activo (Bitso Testnet)\n🕒 {ahora.strftime('%d-%b %H:%M')}")
        ultimo_heartbeat = ahora


def verificar_reinicio_diario():
    """Reinicio automático diario a las 06:00 AM (GMT-7)."""
    global ultimo_reinicio
    ahora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-7)))
    hora_actual = ahora.time()
    if hora_actual.hour == 6 and (datetime.date.today() != ultimo_reinicio):
        enviar_telegram("🔁 Reinicio automático diario en curso (06:00 AM GMT-7)")
        logging.info("⏳ Reinicio automático diario programado.")
        ultimo_reinicio = datetime.date.today()
        os._exit(0)  # Render relanza el servicio automáticamente

# ==========================================================
# 🔄 LOOP PRINCIPAL
# ==========================================================

def ejecutar_bot():
    """Loop continuo principal del bot."""
    logging.info("🤖 Iniciando bot automático profesional (Bitso Testnet)")

    exchange = ccxt.bitso({
        "apiKey": BITSO_API_KEY,
        "secret": BITSO_API_SECRET,
        "enableRateLimit": True
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
            logging.error(f"⚠️ Error en el ciclo principal: {e}")
            enviar_telegram(f"⚠️ Error en ejecución: {str(e)[:150]}")
            time.sleep(15)

# ==========================================================
# 🚀 EJECUCIÓN PRINCIPAL
# ==========================================================
if __name__ == "__main__":
    ejecutar_bot()

