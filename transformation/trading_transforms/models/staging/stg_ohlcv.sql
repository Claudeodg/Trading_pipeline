-- Staging model: clean and standardize raw OHLCV data
-- Source: raw_ohlcv table loaded by the ingestion script

with source as (

    select * from {{ source('trading', 'raw_ohlcv') }}

),

cleaned as (

    select
        symbol,
        open_time,
        open,
        high,
        low,
        close,
        volume,
        trades_count,

        -- Price range for the candle
        high - low as price_range,

        -- Candle direction: 1 = bullish, -1 = bearish
        case
            when close >= open then 1
            else -1
        end as direction

    from source
    where
        open > 0
        and high > 0
        and low > 0
        and close > 0
        and volume > 0

)

select * from cleaned