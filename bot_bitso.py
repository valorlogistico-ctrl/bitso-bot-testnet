import os
import time
import ccxt
import logging
from dotenv import load_dotenv

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
load_dotenv()

BITSO_API_KEY = os.getenv("BITSO_API_KEY")
BITSO_API_SECRET = os.getenv("BITSO_API_SECRET")

# Configurar logs para Render
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger()

# Parámetros principales
INTERVAL = 60          # segundos entre ciclos
RISK_PCT = 0.02        # 2% del balance disponible
MIN_TRADE = 500        # monto mínimo MXN
MAX_TRADE = 10000      # monto máximo MXN
TAKER_FEE = 0.00075    # 0.075% comisión estimada
MAKER_FEE = 0.0005     # 0.05% comisión estimada
SYMBOL = "BTC/MXN"

# Inicializar conexión
bitso = ccxt.bitso({
    "apiKey": BITSO_API_KEY,
    "secret": BITSO_API_SECRET,
    "enableRateLimit": True,
})

logger.info("🚀 Iniciando bot automático optimizado (Bitso Testnet)")
logger.info(f"Par: {SYMBOL} | Intervalo: {INTERVAL}s | Riesgo: {RISK_PCT*100:.1f}%")

# ==============================
# FUNCIÓN PARA CALCULAR MONTO ÓPTIMO
# ==============================
def calcular_tamano_operacion():
    balance = bitso.fetch_balance()
    mxn_balance = balance["total"]["MXN"]

    trade_size = mxn_balance * RISK_PCT
    trade_size = max(MIN_TRADE, min(trade_size, MAX_TRADE))

    logger.info(f"💰 Balance disponible: {mxn_balance:.2f} MXN | Tamaño de orden: {trade_size:.2f} MXN")
    return trade_size

# ==============================
# LOOP PRINCIPAL
# ==============================
last_signal = None

while True:
    try:
        start = time.time()

        ticker = bitso.fetch_ticker(SYMBOL)
        price = ticker["last"]

        # Simulación de señal: alterna entre BUY y SELL
        signal = "BUY" if int(time.time() / 60) % 2 == 0 else "SELL"

        # Calcular tamaño dinámico
        trade_size = calcular_tamano_operacion()

        # Calcular costo estimado de comisiones
        cost_est = trade_size * price * (TAKER_FEE * 2)  # entrada + salida
        logger.info(f"💸 Costo estimado por ciclo: {cost_est:.2f} MXN")

        # Ejemplo de decisión basada en margen esperado
        expected_gain = trade_size * price * 0.003  # margen esperado del 0.3%
        if expected_gain <= cost_est:
            logger.warning("❌ Ganancia esperada insuficiente para cubrir comisiones, se omite la operación.")
        else:
            if signal != last_signal:
                logger.info(f"🟢 Señal: {signal} | Precio: {price:.2f}")

                # Simulación: usar limit order para reducir fee
                amount = trade_size / price
                logger.info(f"📊 Monto estimado: {amount:.6f} BTC | Tipo: LIMIT (maker)")

                last_signal = signal

        elapsed = round(time.time() - start, 2)
        logger.info(f"⏱ Ciclo completado en {elapsed}s | Esperando {INTERVAL}s...\n")
        time.sleep(INTERVAL)

    except Exception as e:
        logger.error(f"⚠️ Error: {e}")
        time.sleep(30)

