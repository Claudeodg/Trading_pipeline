import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

BINANCE_URL = "https://api.binance.com/api/v3/klines"

def fetch_ohlcv(symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
    """
    Fetch OHLCV candlestick data from Binance public API.
    
    Args:
        symbol   : trading pair e.g. BTCUSDT
        interval : candlestick interval e.g. 1h, 4h, 1d
        limit    : number of candles to fetch (max 1000)
    
    Returns:
        pd.DataFrame with raw OHLCV data
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }

    logger.info(f"Fetching {symbol} data — interval {interval} — limit {limit}")

    response = requests.get(BINANCE_URL, params=params)

    if response.status_code != 200:
        logger.error(f"Binance API error : {response.status_code} — {response.text}")
        return pd.DataFrame()

    raw_data = response.json()

    # Binance returns a list of lists — each inner list is one candle
    df = pd.DataFrame(raw_data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades_count",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    # Convert timestamps from milliseconds to datetime
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    # Add symbol column for identification
    df["symbol"] = symbol

    # Cast price and volume columns to float
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    # Keep only relevant columns
    df = df[[
        "symbol", "open_time", "open", "high",
        "low", "close", "volume", "trades_count"
    ]]

    logger.info(f"Successfully fetched {len(df)} candles for {symbol}")

    return df


if __name__ == "__main__":
    df = fetch_ohlcv(symbol="BTCUSDT", interval="1h", limit=100)
    print(df.head())
    print(f"\nShape : {df.shape}")
    print(f"\nColumn types :\n{df.dtypes}")