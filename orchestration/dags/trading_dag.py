from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

# Add project root to Python path
sys.path.insert(0, '/opt/airflow')

from ingestion.fetch_binance import fetch_ohlcv
from storage.save_to_postgres import save_ohlcv
from quality.validate_ohlcv import validate_ohlcv

default_args = {
    'owner': 'claude',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_ingestion():
    """Fetch OHLCV data from Binance and save to PostgreSQL"""
    df = fetch_ohlcv(symbol="BTCUSDT", interval="1h", limit=100)
    save_ohlcv(df)

def run_validation():
    """Run data quality validation"""
    result = validate_ohlcv()
    if not result:
        raise ValueError("Data quality checks failed — stopping pipeline")

with DAG(
    dag_id='trading_pipeline',
    default_args=default_args,
    description='Hourly BTC/USDT data pipeline',
    schedule_interval='@hourly',
    start_date=datetime(2026, 9, 1),
    catchup=False,
    tags=['trading', 'btc', 'data-engineering'],
) as dag:

    # Task 1: Fetch and save data
    ingestion_task = PythonOperator(
        task_id='fetch_and_save_btcusdt',
        python_callable=run_ingestion,
    )
    validation_task = PythonOperator(
        task_id='validate_data_quality',
        python_callable=run_validation,
    )
    # Task 2: Run dbt transformations
    dbt_task = BashOperator(
        task_id='run_dbt_transformations',
        bash_command='cd /opt/airflow/transformation/trading_transforms && dbt deps && dbt run',
    )

    # Define order: ingestion first, then dbt
    ingestion_task >> validation_task >> dbt_task