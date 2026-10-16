import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


def get_engine():
    engine = create_engine(
        "postgresql+psycopg2://",
        connect_args={
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT")),
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
        }
    )
    logger.info("Database engine created successfully")
    return engine


def check(name: str, condition: bool, results: list) -> None:
    status = "PASS" if condition else "FAIL"
    logger.info(f"[{status}] {name}")
    results.append({"check": name, "passed": condition})


def validate_ohlcv() -> bool:
    logger.info("Starting data quality validation on raw_ohlcv")

    engine = get_engine()
    df = pd.read_sql("SELECT * FROM raw_ohlcv", engine)
    logger.info(f"Loaded {len(df)} rows for validation")

    results = []

    check("Table is not empty", len(df) > 0, results)

    for col in ["symbol", "open_time", "open", "high", "low", "close", "volume"]:
        check(f"No NULLs in '{col}'", df[col].isnull().sum() == 0, results)

    for col in ["open", "high", "low", "close"]:
        check(f"'{col}' > 0", (df[col] > 0).all(), results)

    check("high >= low", (df["high"] >= df["low"]).all(), results)
    check("'volume' >= 0", (df["volume"] >= 0).all(), results)
    check("low <= close <= high",
          ((df["close"] >= df["low"]) & (df["close"] <= df["high"])).all(),
          results)

    check("symbol is BTCUSDT", df["symbol"].isin(["BTCUSDT"]).all(), results)

    check("No duplicate open_time", df["open_time"].duplicated().sum() == 0, results)

    latest = pd.to_datetime(df["open_time"]).max()
    now = pd.Timestamp.utcnow().tz_localize(None)
    check("Data is recent (< 2h)", (now - latest).total_seconds() < 7200, results)

    passed = sum(r["passed"] for r in results)
    total = len(results)

    if passed == total:
        logger.info(f"All {total} checks passed")
    else:
        logger.error(f"Only {passed}/{total} checks passed")

    return passed == total


if __name__ == "__main__":
    validate_ohlcv()