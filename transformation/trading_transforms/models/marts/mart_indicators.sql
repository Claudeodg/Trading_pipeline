-- Mart model: calculate technical indicators from staging data

with base as (

    select * from {{ ref('stg_ohlcv') }}

),

indicators as (

    select
        symbol,
        open_time,
        open,
        high,
        low,
        close,
        volume,
        trades_count,
        price_range,
        direction,

        -- Simple Moving Average 7 periods
        avg(close) over (
            partition by symbol
            order by open_time
            rows between 6 preceding and current row
        ) as sma_7,

        -- Simple Moving Average 20 periods
        avg(close) over (
            partition by symbol
            order by open_time
            rows between 19 preceding and current row
        ) as sma_20,

        -- Average volume over 7 periods
        avg(volume) over (
            partition by symbol
            order by open_time
            rows between 6 preceding and current row
        ) as avg_volume_7,

        -- Price change percentage vs previous candle
        round(
            cast(
                (close - lag(close) over (partition by symbol order by open_time))
                / lag(close) over (partition by symbol order by open_time) * 100
            as numeric), 2
        ) as price_change_pct

    from base

)

select * from indicators