# ==========================================================
# 🤖 BITSO BOT TESTNET (versión optimizada)
# Autor: Jorge Macías / valorlogistico-ctrl
# ==========================================================

import os
import csv
import time
import requests
import logging
from datetime import datetime
import ccxt
from dotenv import load_dotenv

# ==========================================================
# ⚙️ CONFIGURACIÓN INICIAL
# ==========================================================

load_dotenv()  # Carga variables del archivo .env

# Credenciales Bitso
BITSO_API_KEY = os.getenv("BITSO_API_KEY")
BITSO_API_SECRET = os.getenv("BITSO_API_SECRET")

# Credenciales Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Variables globales
balance_neto = 0.0
CSV_FILE = "bitso_trades.csv"
DAILY_FILE = "daily_summary.csv"
ultimo_dia = None

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
        print(f"⚠️ Error enviando Telegram: {e}")

# ==========================================================
# 💾 FUNCIÓN: Registrar operación
# ==========================================================
def registrar_operacion(par, accion, precio, monto, comision_pct):
    """Guarda operaciones y actualiza el balance neto."""
    global balance_neto

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comision = precio * monto * comision_pct
    resultado_neto = -(precio * monto + comision) if accion == "BUY" else (precio * monto - comision)
    balance_neto += resultado_neto

    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        if not file_exists:
            writer.writerow(["timestamp", "par", "acción", "precio", "monto", "comisión", "resultado_neto"])
        writer.writerow([fecha, par, accion, precio, monto, comision, resultado_neto])

    logging.info(f"💾 Registro guardado: {accion} {monto} {par} @ {precio} | Comisión: {comision:.2f}")
    enviar_telegram(f"{accion} {par}\nPrecio: {precio:,.2f}\nMonto: {monto:.6f}\nBalance: {balance_neto:,.2f} MXN")

# ==========================================================
# 🧮 FUNCIÓN: Calcular monto óptimo
# ==========================================================
def calcular_monto_optimo(precio_actual, balance_mxn=1000):
    """Calcula el monto máximo rentable considerando comisiones."""
    MONTO_BASE = 0.0001  # BTC mínimo base (~210 MXN aprox)
    max_monto = balance_mxn / precio_actual
    monto_final = min(MONTO_BASE * 5, max_monto)
    return round(monto_final, 6)

# ==========================================================
# 🧾 FUNCIÓN: Registro de balance diario
# ==========================================================
def registrar_resumen_diario():
    """Guarda el balance neto al cierre de cada día y envía resumen por Telegram."""
    global ultimo_dia, balance_neto
    hoy = datetime.now().strftime("%Y-%m-%d")

    if ultimo_dia == hoy:
        return

    file_exists = os.path.isfile(DAILY_FILE)
    with open(DAILY_FILE, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        if not file_exists:
            writer.writerow(["fecha", "balance_neto"])
        writer.writerow([hoy, round(balance_neto, 2)])

    enviar_telegram(f"🕛 Cierre diario {hoy}\nBalance acumulado: {balance_neto:.2f} MXN")
    logging.info(f"📘 Resumen diario registrado para {hoy} | Balance: {balance_neto:.2f} MXN")
    ultimo_dia = hoy

# ==========================================================
# 🔁 LOOP PRINCIPAL DEL BOT (con modo de prueba corto)
# ==========================================================
def ejecutar_bot(modo_test=False, ciclos_test=3):
    logging.info("🤖 Iniciando bot automático optimizado (Bitso Testnet)")

    exchange = ccxt.bitso({
        "apiKey": BITSO_API_KEY,
        "secret": BITSO_API_SECRET,
        "enableRateLimit": True,
    })

    PAIR = "BTC/MXN"
    INTERVAL = 10 if modo_test else 300  # 10 seg en test, 5 min en producción
    COMISION_MAKER = 0.003  # 0.3%

    contador = 0
    while True:
        try:
            ticker = exchange.fetch_ticker(PAIR)
            precio_actual = ticker["last"]
            senal = "BUY" if int(time.time()) % 2 == 0 else "SELL"
            monto = calcular_monto_optimo(precio_actual)

            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Señal: {senal} | Precio: {precio_actual}")

            if senal == "BUY":
                registrar_operacion(PAIR, "BUY", precio_actual, monto, COMISION_MAKER)
            else:
                registrar_operacion(PAIR, "SELL", precio_actual, monto, COMISION_MAKER)

            enviar_telegram(f"📊 Balance acumulado: {balance_neto:.2f} MXN")

            if modo_test:
                contador += 1
                if contador >= ciclos_test:
                    enviar_telegram("✅ Test corto finalizado correctamente en Render.")
                    print("✅ Test corto finalizado correctamente.")
                    break

            time.sleep(INTERVAL)

        except Exception as e:
            logging.error(f"⚠️ Error en el ciclo: {e}")
            if "rate limit" in str(e).lower():
                time.sleep(60)
            else:
                time.sleep(15)

# ==========================================================
# ▶️ EJECUCIÓN DEL BOT (modo producción persistente)
# ==========================================================
if __name__ == "__main__":
    try:
        enviar_telegram("🚀 Bot Bitso iniciado correctamente en Render (modo producción).")
        ejecutar_bot(modo_test=False)
    except Exception as e:
        logging.error(f"❌ Error crítico: {e}")
        enviar_telegram(f"⚠️ Error crítico en bot: {e}")
        while True:
            # Mantiene el proceso vivo aunque ocurra un error
            time.sleep(300)

