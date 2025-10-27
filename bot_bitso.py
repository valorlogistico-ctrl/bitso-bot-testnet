import ccxt
import pandas as pd
import numpy as np
import time
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("BITSO_API_KEY")
api_secret = os.getenv("BITSO_API_SECRET")

exchange = ccxt.bitso({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True
})

symbol = 'BTC/MXN'
timeframe = '4h'
ma_short = 5
ma_long = 20

print("🚀 Iniciando bot automático (Bitso Testnet)")
print(f"Configuración: {symbol} | timeframe={timeframe} | MAs={ma_short}/{ma_long}")

while True:
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=200)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['ma_short'] = df['close'].rolling(window=ma_short).mean()
        df['ma_long'] = df['close'].rolling(window=ma_long).mean()

        last_row = df.iloc[-1]
        signal = "buy" if last_row['ma_short'] > last_row['ma_long'] else "sell"
        print(f"\n[{last_row['timestamp']}] Señal: {signal.upper()} | Precio: {last_row['close']:.2f}")

        if signal == "buy":
            print("🟢 Simulando compra BTC/MXN")
        else:
            print("🔴 Simulando venta BTC/MXN")

        time.sleep(300)
    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(60)

