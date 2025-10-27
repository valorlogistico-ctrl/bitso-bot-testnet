# ==========================================================
# 🤖 BITSO BOT TESTNET (versión agresiva con control adaptativo)
# Autor: Jorge Macías / valorlogistico-ctrl
# ==========================================================

import ccxt
import time
import pandas as pd
import requests
import numpy as np
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# ==========================================================
# 🔧 CONFIGURACIÓN GENERAL
# ==========================================================
load_dotenv()

BITSO_API_KEY = os.getenv("BITSO_API_KEY")
BITSO_API_SECRET = os.getenv("BITSO_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "BTC/MXN"
TIMEFRAME = "4h"

# ==========================================================
# 💰 GESTIÓN DE RIESGO
# ==========================================================
RISK_PERCENT = 0.25
MIN_TRADE_MXN = 150
MAX_TRADE_MXN = 1500
STOP_LOSS_PCT = -2.5
TAKE_PROFIT_PCT = 4.5
ADAPTIVE_REDUCTION = 0.15  # tras 3 stops consecutivos

# ==========================================================
# ⏰ CONTROL DE CICLO
# ==========================================================
GMT_OFFSET = -7
RESTART_HOUR = 6  # reinicio diario 06:00 GMT-7
SUMMARY_HOUR = 23  # resumen diario 23:59 GMT-7
HEARTBEAT_INTERVAL = 3600  # cada hora

# ==========================================================
# 📤 FUNCIÓN TELEGRAM
# ==========================================================
def send_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")

# ==========================================================
# 📈 CONFIGURAR EXCHANGE (Bitso Testnet)
# ==========================================================
exchange = ccxt.bitso({
    "apiKey": BITSO_API_KEY,
    "secret": BITSO_API_SECRET,
    "enableRateLimit": True,
})

# ==========================================================
# ⚙️ FUNCIÓN PRINCIPAL DE OPERACIÓN
# ==========================================================
def get_signals():
    df = pd.DataFrame(exchange.fetch_ohlcv(PAIR, TIMEFRAME), columns=["time","open","high","low","close","volume"])
    df["ma_fast"] = df["close"].rolling(5).mean()
    df["ma_slow"] = df["close"].rolling(20).mean()
    last = df.iloc[-1]
    if last["ma_fast"] > last["ma_slow"]:
        return "BUY", last["close"]
    elif last["ma_fast"] < last["ma_slow"]:
        return "SELL", last["close"]
    return None, last["close"]

def execute_trade(signal, price, balance):
    global RISK_PERCENT
    trade_mxn = min(max(balance * RISK_PERCENT, MIN_TRADE_MXN), MAX_TRADE_MXN)
    qty = trade_mxn / price
    result = f"🟢 Compra BTC/MXN — {qty:.5f} BTC ejecutados | Balance usado: {trade_mxn:.2f} MXN" if signal == "BUY" \
        else f"🔴 Venta BTC/MXN — {qty:.5f} BTC ejecutados | Balance recibido: {trade_mxn:.2f} MXN"
    send_telegram(result)
    print(result)
    return {"side": signal, "price": price, "qty": qty}

# ==========================================================
# 📊 MONITOREO Y RESUMEN
# ==========================================================
def daily_summary(trades):
    if not trades:
        send_telegram("📊 Sin operaciones registradas hoy.")
        return
    df = pd.DataFrame(trades)
    gains = np.sum([
        ((row["price_exit"] - row["price_entry"]) / row["price_entry"]) * 100
        if row["side"] == "BUY" else
        ((row["price_entry"] - row["price_exit"]) / row["price_entry"]) * 100
        for _, row in df.iterrows()
    ])
    send_telegram(
        f"📅 Resumen diario:\n"
        f"Operaciones: {len(df)} | Resultado neto: {gains:.2f}%\n"
        f"Ganadoras: {(gains > 0)} | Reinicio programado a las 06:00 AM GMT-7"
    )

# ==========================================================
# ♻️ LOOP PRINCIPAL
# ==========================================================
def main():
    print("🚀 Iniciando bot (modo agresivo con control adaptativo)")
    send_telegram("🤖 Bot activo (modo testnet agresivo con control adaptativo).")

    trades = []
    consecutive_losses = 0

    while True:
        now = datetime.now(timezone(timedelta(hours=GMT_OFFSET)))
        hour = now.hour

        # Reinicio diario
        if hour == RESTART_HOUR and now.minute == 0:
            daily_summary(trades)
            send_telegram("♻️ Reinicio diario ejecutado.")
            os.system("python bot_bitso.py")
            break

        # Heartbeat
        if now.minute == 0:
            send_telegram(f"💓 Bot activo ({PAIR}) | {now.strftime('%H:%M')} GMT-7")

        # Señales
        signal, price = get_signals()
        balance = 1000  # balance simulado MXN
        if signal:
            trade = execute_trade(signal, price, balance)
            # Simular resultado
            variation = np.random.uniform(STOP_LOSS_PCT, TAKE_PROFIT_PCT)
            trade["price_entry"] = price
            trade["price_exit"] = price * (1 + variation / 100)
            trades.append(trade)
            if variation < 0:
                consecutive_losses += 1
                if consecutive_losses >= 3:
                    RISK_PERCENT = ADAPTIVE_REDUCTION
                    send_telegram("⚠️ 3 pérdidas seguidas — Riesgo reducido temporalmente a 15%")
            else:
                consecutive_losses = 0
                RISK_PERCENT = 0.25

        time.sleep(300)  # Esperar 5 min entre iteraciones

if __name__ == "__main__":
    main()

