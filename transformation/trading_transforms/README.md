# BTC/USDT Trading Data Pipeline

A production-grade data engineering pipeline that ingests, validates, transforms, and visualizes hourly BTC/USDT candlestick data from the Binance public API.

Built as a portfolio project to demonstrate end-to-end Data Engineering skills: orchestration, data quality, SQL transformations, containerization, and real-time dashboarding.



## Architecture


Binance API (public)
       │
       ▼
┌─────────────────┐
│   Ingestion     │  fetch_binance.py — OHLCV klines endpoint
│  (Python)       │  100 hourly candles per run
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Storage       │  save_to_postgres.py — upsert with ON CONFLICT
│  (PostgreSQL)   │  raw_ohlcv table — UNIQUE(symbol, open_time)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Quality    │  validate_ohlcv.py — 18 pure-pandas checks
│  (pandas)       │  Blocks pipeline if any check fails
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Transformation  │  dbt-postgres — staging + marts
│   (dbt)         │  SMA7, SMA20, price_change_pct, avg_volume_7
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestration  │  Apache Airflow — @hourly DAG
│  (Airflow)      │  3 tasks: ingest → validate → dbt run
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │  Streamlit + Plotly
│  (Streamlit)    │  Candlestick chart, SMA overlay, metrics
└─────────────────┘

All services run in Docker Compose


## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Ingestion | Python + Requests | 3.12 |
| Storage | PostgreSQL | 18 |
| Data Quality | pandas | 2.x |
| Transformation | dbt-postgres | 1.12 |
| Orchestration | Apache Airflow | 2.9.0 |
| Dashboard | Streamlit + Plotly | latest |
| Containerization | Docker + Docker Compose | latest |
| DB Driver | SQLAlchemy + psycopg2 | latest |
| Data Source | Binance Public API | v3 |


##  Project Structure

trading_pipeline/
├── ingestion/
│   └── fetch_binance.py          # Fetch OHLCV data from Binance API
├── storage/
│   └── save_to_postgres.py       # Upsert data into PostgreSQL
├── quality/
│   └── validate_ohlcv.py         # 18 data quality checks
├── transformation/
│   └── trading_transforms/
│       ├── dbt_project.yml
│       ├── profiles.yml
│       └── models/
│           ├── staging/
│           │   ├── sources.yml
│           │   └── stg_ohlcv.sql
│           └── marts/
│               └── mart_indicators.sql
├── orchestration/
│   └── dags/
│       └── trading_dag.py
├── dashboard/
│   └── app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py
├── .env
└── .gitignore
```

---

##  Pipeline DAG

```
fetch_and_save_btcusdt  →  validate_data_quality  →  run_dbt_transformations
       (Python)                   (Python)                  (Bash)
```

- **fetch_and_save_btcusdt** — Calls Binance `/api/v3/klines`, fetches the last 100 hourly candles, upserts into `raw_ohlcv`. Duplicate timestamps are silently skipped via `ON CONFLICT DO NOTHING`.
- **validate_data_quality** — Runs 18 checks on `raw_ohlcv`. Raises `ValueError` if any check fails, blocking the dbt step.
- **run_dbt_transformations** — Runs `dbt deps && dbt run`, materializing `stg_ohlcv` and `mart_indicators` in PostgreSQL.

Schedule: `@hourly` | `catchup=False` | 1 retry with 5-minute delay

---

## Data Quality Checks (18 total)

| Category | Check |
|---|---|
| Completeness | Table is not empty |
| Null checks | No NULLs in symbol, open_time, open, high, low, close, volume |
| Price validity | open, high, low, close > 0 |
| OHLC consistency | high >= low |
| OHLC consistency | low <= close <= high |
| Volume | volume >= 0 |
| Business rule | symbol == BTCUSDT |
| Uniqueness | No duplicate open_time |
| Freshness | Latest candle < 2 hours old |


## dbt Models

### `staging/stg_ohlcv`
Cleans and enriches raw data:
- Filters out rows with zero prices
- Adds `price_range` (high - low)
- Adds `direction` (1 = bullish candle, -1 = bearish candle)

### `marts/mart_indicators`
Computes technical indicators using SQL window functions:
- `sma_7` — 7-period Simple Moving Average (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
- `sma_20` — 20-period Simple Moving Average
- `avg_volume_7` — 7-period average volume
- `price_change_pct` — percentage change vs previous candle (LAG + arithmetic)

---

## Dashboard

Streamlit dashboard reads from `mart_indicators` and displays:
- **Candlestick chart** with SMA7 and SMA20 overlays (Plotly)
- **Price change bar chart** — bullish/bearish coloring
- **Metrics cards** — last price, 24h change, volume
- **Raw data table** — last 200 rows

Cache TTL: 1 hour (`@st.cache_data(ttl=3600)`)

Access: [http://localhost:8501](http://localhost:8501)

---

## Setup

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- PostgreSQL 18 running locally on port 5432
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Claudeodg/trading_pipeline.git
cd trading_pipeline
```

### 2. Configure environment variables

```env
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=your_password
```

> **Note:** Use `localhost` instead of `host.docker.internal` when running scripts locally outside Docker.

### 3. Create the PostgreSQL database and table

```sql
CREATE DATABASE trading_db;

\c trading_db

CREATE TABLE raw_ohlcv (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    open_time TIMESTAMP NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume FLOAT NOT NULL,
    trades_count INT,
    UNIQUE (symbol, open_time)
);
```

### 4. Configure dbt profiles

```yaml
trading_transforms:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      dbname: trading_db
      user: postgres
      password: your_password
      schema: public
      threads: 1
```

### 5. Build and start Docker services

```bash
docker-compose up --build -d
```

### 6. Trigger the pipeline

Open [http://localhost:8080](http://localhost:8080) (admin / admin), enable `trading_pipeline`, trigger a manual run.

### 7. View the dashboard

Open [http://localhost:8501](http://localhost:8501)

---

## Access URLs

| Service | URL | Credentials |
|---|---|---|
| Airflow UI | http://localhost:8080 | admin / admin |
| Streamlit dashboard | http://localhost:8501 | — |
| PostgreSQL | localhost:5432 | voir .env |



## Author

**Claude Sonafouo**  
Computer Science student — TU Dortmund  
[github.com/Claudeodg](https://github.com/Claudeodg) · [sonafouobonte@gmail.com](mailto:sonafouobonte@gmail.com)

---

*Portfolio project — Data Engineering track | October 2026*
