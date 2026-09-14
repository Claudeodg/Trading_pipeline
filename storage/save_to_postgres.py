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
    """
    Save OHLCV DataFrame to PostgreSQL.
    Appends new rows — does not overwrite existing data.

    Args:
        df         : DataFrame returned by fetch_ohlcv()
        table_name : target table name in PostgreSQL
    """
    if df.empty:
        logger.warning("Empty DataFrame — nothing to save")
        return

    engine = get_engine()

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False
    )

    logger.info(f"{len(df)} rows saved to table '{table_name}'")


