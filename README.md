# BTC/USDT Trading Pipeline

A production-grade data engineering pipeline that fetches, stores, transforms and visualizes Bitcoin price data in real time.

**Live dashboard:** [trading-pipeline.streamlit.app](https://trading-pipeline.streamlit.app)

---

## Architecture

```
Binance API → PostgreSQL (Neon) → dbt → Airflow → Streamlit
```

- **Ingestion:** Binance REST API, hourly OHLCV candles (BTC/USDT)
- **Storage:** PostgreSQL hosted on Neon (serverless, cloud-native)
- **Transformation:** dbt — `stg_ohlcv` + `mart_indicators` (SMA-7, SMA-20, price change %)
- **Orchestration:** Apache Airflow 2.9 — 3 tasks: ingest → validate → dbt
- **Dashboard:** Streamlit — dark/light mode, EN/DE toggle, candlestick chart

## Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| Orchestration | Apache Airflow 2.9 |
| Database | PostgreSQL via Neon |
| Transformation | dbt 1.x |
| Dashboard | Streamlit + Plotly |
| Containerization | Docker Compose |

## Project Structure

```
trading_pipeline/
├── ingestion/fetch_binance.py
├── storage/save_to_postgres.py
├── quality/validate_ohlcv.py
├── transformation/trading_transforms/
│   └── models/
│       ├── staging/stg_ohlcv.sql
│       └── marts/mart_indicators.sql
├── orchestration/dags/trading_dag.py
├── dashboard/app.py
├── docker-compose.yml
└── requirements.txt
```

## Setup

**1. Clone and configure**

```bash
git clone https://github.com/Claudeodg/trading_pipeline.git
cd trading_pipeline
```

Create `.env`:

```env
DB_HOST=<your-neon-host>
DB_PORT=5432
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=<your-neon-password>
```

**2. Create the table on Neon**

```sql
CREATE TABLE IF NOT EXISTS raw_ohlcv (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    open_time TIMESTAMP NOT NULL,
    open NUMERIC(18,8),
    high NUMERIC(18,8),
    low NUMERIC(18,8),
    close NUMERIC(18,8),
    volume NUMERIC(24,8),
    trades_count INTEGER,
    UNIQUE (symbol, open_time)
);
```

**3. Start**

```bash
docker-compose up airflow-webserver airflow-scheduler streamlit
```

- Airflow UI: http://localhost:8080
- Dashboard: http://localhost:8501

**4. Trigger the DAG**

Airflow UI → `trading_pipeline` → Play

## Key Engineering Decisions

| Decision | Rationale |
|---|---|
| Neon over local PostgreSQL | Cloud-hosted, enables public deployment |
| `connect_args` over SQLAlchemy URL | Avoids UnicodeDecodeError with special chars |
| `sslmode: require` | Mandatory for Neon connections |
| dbt views over tables | No storage cost on free tier |
| Docker Compose | Reproducible local environment |

## Dashboard Features

- Candlestick chart with SMA-7 and SMA-20 overlays
- Hourly price change bar chart
- Custom metric cards (price, SMAs, volume)
- Dark / light mode toggle
- EN / DE language switch

## Author

**Sonafouo Claude** — TU Dortmund — [github.com/Claudeodg](https://github.com/Claudeodg)