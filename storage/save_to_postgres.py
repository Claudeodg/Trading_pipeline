import pandas as pd
from sqlalchemy import create_engine, text
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
    """
    Create and return a SQLAlchemy engine using credentials from .env
    """
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
    engine = create_engine(url)
    logger.info("Database engine created successfully")
    return engine

def save_ohlcv(df: pd.DataFrame, table_name: str = "raw_ohlcv") -> None:
        if df.empty:
            logger.warning("Empty DataFrame — nothing to save")
            return

        engine = get_engine()

        with engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(
                    text(f"""
                        INSERT INTO {table_name}
                        (symbol, open_time, open, high, low, close, volume, trades_count)
                        VALUES (:symbol, :open_time, :open, :high, :low, :close, :volume, :trades_count)
                        ON CONFLICT (symbol, open_time) DO NOTHING
                    """),
                    row.to_dict()
                )

        logger.info(f"{len(df)} rows processed for table '{table_name}'")


