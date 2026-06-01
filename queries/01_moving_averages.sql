-- 01_moving_averages.sql
-- Oblicza 20-dniową i 50-dniową średnią kroczącą cen zamknięcia dla każdego tickera.
-- Przydatne do identyfikacji trendów i sygnałów kupna/sprzedaży.

SELECT
    date,
    ticker,
    close,
    -- Średnia kroczaca 20 dni (SMA20)
    ROUND(
        AVG(close) OVER (
            PARTITION BY ticker
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ), 4
    ) AS sma_20,
    -- Średnia krocząca 50 dni (SMA50)
    ROUND(
        AVG(close) OVER (
            PARTITION BY ticker
            ORDER BY date
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
        ), 4
    ) AS sma_50,
    -- Odchylenie ceny od SMA20 w procentach
    ROUND(
        (close - AVG(close) OVER (
            PARTITION BY ticker
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        )) / AVG(close) OVER (
            PARTITION BY ticker
            ORDER BY date
            ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
        ) * 100, 2
    ) AS pct_dev_from_sma20
FROM prices
ORDER BY ticker, date;
