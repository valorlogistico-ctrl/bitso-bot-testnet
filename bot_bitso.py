# ==========================================================
# BITSO BOT TESTNET - Versión Optimizada
# Autor: Jorge Macías / valorlogistico-ctrl
# ==========================================================

import os
import time
import csv
import ccxt
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

# ==========================================================
# CONFIGURACIÓN INICIAL
# ==========================================================
load_dotenv()

# Credenciales Bitso (Testnet)
BITSO_API_KEY = os.getenv("JUMPLK1FNYn")
BITSO_API_SECRET = os.getenv("93p93bb381864f679e4b64bfb87efnY")
exchange = ccxt.bitso({
    "apiKey": BITSO_API_KEY,
    "secret": BITSO_API_SECRET,
    "enableRateLimit": True
})

# Credenciales Telegram
TELEGRAM_TOKEN = os.getenv("8394147456")
TELEGRAM_CHAT_ID = os.getenv("AAHP98mB8ey7TKK14A3fMAJtUyiJoA")

# ==========================================================
# PARÁMETROS DEL BOT
# ==========================================================
PAIR = "BTC/MXN"              # Par de trading
INTERVAL = 60                 # Tiempo entre ejecuciones (segundos)
COMISION_MAKER = 0.001        # 0.1% Bitso Maker
MONTOS_BASE = 0.00005         # BTC base (~100 MXN aprox)
CSV_FILE = "bitso_trades.csv" # Archivo de registro

balance_neto = 0.0

# ==========================================================
# CONFIGURACIÓN DE LOGGING
# ==========================================================
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

# ==========================================================
# FUNCIÓN: Enviar mensaje a Telegram
# ==========================================================
def enviar_telegram(mensaje):
    """Envía mensajes al chat de Telegram configurado."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
        requests.post(url, data=data)
    except Exception as e:
        logging.error(f"❌ Error enviando mensaje a Telegram: {e}")

# ==========================================================
# FUNCIÓN: Registrar operación en CSV
# ==========================================================
def registrar_operacion(par, accion, precio, monto, comision_pct):
    """Guarda operaciones en CSV y actualiza balance neto."""
    global balance_neto

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comision = precio * monto * comision_pct
    resultado_neto = (precio * monto) - comision if accion == "SELL" else -(precio * monto + comision)
    balance_neto += resultado_neto

    # Escribir en CSV
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        if not file_exists:
            writer.writerow(["timestamp", "par", "accion", "precio", "monto", "comision", "resultado_neto", "balance_neto"])
        writer.writerow([fecha, par, accion, precio, monto, comision, resultado_neto, balance_neto])

    logging.info(f"💾 {accion} {monto} BTC @ {precio} | Balance: {balance_neto:.2f} MXN")
    enviar_telegram(f"💹 {accion} {par}\nPrecio: {precio:,.2f}\nMonto: {monto} BTC\nBalance: {balance_neto:.2f} MXN")

# ==========================================================
# FUNCIÓN: Calcular monto óptimo
# ==========================================================
def calcular_monto_optimo(precio_actual, balance_mxn=1000):
    """Calcula monto dinámico según riesgo 3% del capital."""
    riesgo_pct = 0.03  # 3%
    monto_mxn = balance_mxn * riesgo_pct
    monto_btc = monto_mxn / precio_actual
    return round(monto_btc, 6)

# ==========================================================
# LOOP PRINCIPAL DEL BOT
# ==========================================================
def ejecutar_bot():
    logging.info("🤖 Iniciando bot automático optimizado (Bitso Testnet)")
    while True:
        try:
            ticker = exchange.fetch_ticker(PAIR)
            precio_actual = ticker["last"]

            # Simular señal (placeholder)
            senal = "BUY" if int(time.time()) % 2 == 0 else "SELL"

            logging.info(f"[{datetime.now().strftime('%H:%M:%S')}] Señal: {senal} | Precio: {precio_actual}")

            monto = calcular_monto_optimo(precio_actual)

            if senal == "BUY":
                logging.info(f"🟢 Simulando compra {PAIR} | Monto: {monto} BTC @ {precio_actual}")
                registrar_operacion(PAIR, "BUY", precio_actual, monto, COMISION_MAKER)
            elif senal == "SELL":
                logging.info(f"🔴 Simulando venta {PAIR} | Monto: {monto} BTC @ {precio_actual}")
                registrar_operacion(PAIR, "SELL", precio_actual, monto, COMISION_MAKER)

            # Enviar resumen cada hora
            if datetime.now().minute == 0:
                enviar_telegram(f"📊 Balance acumulado: {balance_neto:.2f} MXN")

            time.sleep(INTERVAL)

        except Exception as e:
            logging.error(f"⚠️ Error en el ciclo: {e}")
            if "rate limit" in str(e).lower():
                time.sleep(60)
            else:
                time.sleep(15)

# ==========================================================
# EJECUCIÓN DEL BOT
# ==========================================================
if __name__ == "__main__":
    ejecutar_bot()

