from ingestion.fetch_binance import fetch_ohlcv
from storage.save_to_postgres import save_ohlcv

if __name__ == "__main__":
    df = fetch_ohlcv(symbol="BTCUSDT", interval="1h", limit=100)
    save_ohlcv(df)