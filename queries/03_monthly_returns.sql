-- 03_monthly_returns.sql
-- Porównuje indeksy i ETF-y miesiąc do miesiąca.
-- Oblicza miesięczny zwrot procentowy na podstawie ceny zamknięcia
-- pierwszego i ostatniego dnia handlowego każdego miesiąca.

-- Miesięczne zwroty dla ETF-ów
WITH monthly_prices AS (
    SELECT
        ticker                                          AS symbol,
        'ETF'                                           AS asset_type,
        STRFTIME('%Y', date)                            AS year,
        STRFTIME('%m', date)                            AS month,
        STRFTIME('%Y-%m', date)                         AS year_month,
        -- Cena z pierwszego dnia miesiąca
        FIRST_VALUE(close) OVER (
            PARTITION BY ticker, STRFTIME('%Y-%m', date)
            ORDER BY date
        )                                               AS open_price,
        -- Cena z ostatniego dnia miesiąca
        LAST_VALUE(close) OVER (
            PARTITION BY ticker, STRFTIME('%Y-%m', date)
            ORDER BY date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                                               AS close_price,
        ROW_NUMBER() OVER (
            PARTITION BY ticker, STRFTIME('%Y-%m', date)
            ORDER BY date DESC
        )                                               AS rn
    FROM prices

    UNION ALL

    SELECT
        symbol,
        'Index'                                         AS asset_type,
        STRFTIME('%Y', date)                            AS year,
        STRFTIME('%m', date)                            AS month,
        STRFTIME('%Y-%m', date)                         AS year_month,
        FIRST_VALUE(close) OVER (
            PARTITION BY symbol, STRFTIME('%Y-%m', date)
            ORDER BY date
        )                                               AS open_price,
        LAST_VALUE(close) OVER (
            PARTITION BY symbol, STRFTIME('%Y-%m', date)
            ORDER BY date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                                               AS close_price,
        ROW_NUMBER() OVER (
            PARTITION BY symbol, STRFTIME('%Y-%m', date)
            ORDER BY date DESC
        )                                               AS rn
    FROM indices
)
SELECT
    year_month,
    year,
    month,
    symbol,
    asset_type,
    ROUND(open_price, 4)                                                AS month_open,
    ROUND(close_price, 4)                                               AS month_close,
    -- Miesięczny zwrot w procentach
    ROUND((close_price - open_price) / open_price * 100, 2)            AS monthly_return_pct,
    -- Zwrot powyżej/poniżej zera
    CASE
        WHEN close_price >= open_price THEN 'positive'
        ELSE 'negative'
    END                                                                  AS direction
FROM monthly_prices
WHERE rn = 1
ORDER BY symbol, year_month;
