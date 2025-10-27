# ============================================
# 🧠 BITSO BOT TESTNET (versión optimizada)
# Autor: Jorge Macías / valorlogistico-ctrl
# ============================================

import os
import time
import ccxt
import csv
import logging
from datetime import datetime
from dotenv import load_dotenv

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================

load_dotenv()  # Carga las variables desde .env
API_KEY = os.getenv("BITSO_API_KEY")
API_SECRET = os.getenv("BITSO_API_SECRET")

exchange = ccxt.bitso({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
})

# Configura logging (Render muestra los print/logs)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# ============================================
# PARÁMETROS DE OPERACIÓN
# ============================================

PAIR = "BTC/MXN"               # Par de trading
INTERVAL = 30                  # Tiempo entre ciclos (segundos)
MONTOS_BASE = 0.0001           # Tamaño base de operación BTC (≈ 2.1 MXN test)
COMISION_MAKER = 0.001         # 0.1% Bitso maker
COMISION_TAKER = 0.003         # 0.3% Bitso taker
CSV_FILE = "bitso_trades.csv"  # Archivo histórico

# ============================================
# FUNCIÓN DE REGISTRO HISTÓRICO
# ============================================

def registrar_operacion(par, accion, precio, monto, comision_pct):
    """Guarda operación simulada en CSV."""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    comision = precio * monto * comision_pct
    resultado_neto = (precio * monto) - comision if accion == "SELL" else -(precio * monto) - comision

    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="") as archivo:
        writer = csv.writer(archivo)
        if not file_exists:
            writer.writerow(["timestamp", "par", "accion", "precio", "monto", "comision", "resultado_neto"])
        writer.writerow([fecha, par, accion, precio, monto, comision, resultado_neto])

    logging.info(f"💾 Registro guardado: {accion} {monto} {par} @ {precio} | Comisión: {comision:.4f}")

# ============================================
# FUNCIÓN DE CÁLCULO DE MONTO ÓPTIMO
# ============================================

def calcular_monto_optimo(precio_actual, balance_mxn=1000):
    """Calcula el monto máximo rentable considerando comisiones."""
    max_monto = balance_mxn / precio_actual
    monto_final = max(MONTOS_BASE, min(max_monto, MONTOS_BASE * 5))
    return round(monto_final, 6)

# ============================================
# LOOP PRINCIPAL DEL BOT
# ============================================

def ejecutar_bot():
    logging.info("🚀 Iniciando bot automático optimizado (Bitso Testnet)")

    while True:
        try:
            ticker = exchange.fetch_ticker(PAIR)
            precio_actual = ticker["last"]

            logging.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Señal: BUY | Precio: {precio_actual}")

            # Simulación de compra
            monto = calcular_monto_optimo(precio_actual)
            logging.info(f"🟢 Simulando compra {PAIR} | Monto: {monto} BTC @ {precio_actual} MXN")

            # Registrar la operación simulada
            registrar_operacion(PAIR, "BUY", precio_actual, monto, COMISION_MAKER)

            # Esperar hasta el siguiente ciclo
            time.sleep(INTERVAL)

        except Exception as e:
            logging.error(f"❌ Error en el ciclo: {e}")
            time.sleep(10)

# ============================================
# EJECUCIÓN DEL BOT
# ============================================

if __name__ == "__main__":
    ejecutar_bot()

