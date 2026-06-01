-- 04_nav_summary.sql
-- Zestawienie NAV (Net Asset Value) dla portfela ETF-ów.
-- Pokazuje ostatnią cenę, zmianę rok do roku (YTD) oraz zmianę 1-dniową.

WITH latest AS (
    -- Ostatnia dostępna cena każdego tickera
    SELECT
        ticker,
        close    AS latest_close,
        date     AS latest_date
    FROM prices
    WHERE (ticker, date) IN (
        SELECT ticker, MAX(date) FROM prices GROUP BY ticker
    )
),
start_of_year AS (
    -- Cena z pierwszego dnia handlowego danego roku
    SELECT
        ticker,
        close    AS ytd_open,
        date     AS ytd_date
    FROM prices
    WHERE (ticker, date) IN (
        SELECT ticker, MIN(date)
        FROM prices
        WHERE STRFTIME('%Y', date) = STRFTIME('%Y', 'now')
        GROUP BY ticker
    )
),
prev_day AS (
    -- Cena z poprzedniego dnia handlowego
    SELECT p1.ticker, p1.close AS prev_close
    FROM prices p1
    WHERE p1.date = (
        SELECT MAX(p2.date)
        FROM prices p2
        WHERE p2.ticker = p1.ticker
          AND p2.date < (SELECT MAX(date) FROM prices WHERE ticker = p1.ticker)
    )
)
SELECT
    l.ticker,
    l.latest_date                                                   AS as_of_date,
    ROUND(l.latest_close, 4)                                        AS price,
    ROUND(p.prev_close, 4)                                          AS prev_price,
    -- Zmiana 1-dniowa
    ROUND(l.latest_close - p.prev_close, 4)                        AS day_change,
    ROUND((l.latest_close - p.prev_close) / p.prev_close * 100, 2) AS day_change_pct,
    -- Zmiana YTD
    ROUND(s.ytd_open, 4)                                            AS ytd_open_price,
    ROUND(l.latest_close - s.ytd_open, 4)                          AS ytd_change,
    ROUND((l.latest_close - s.ytd_open) / s.ytd_open * 100, 2)    AS ytd_return_pct
FROM latest l
LEFT JOIN start_of_year s ON l.ticker = s.ticker
LEFT JOIN prev_day p      ON l.ticker = p.ticker
ORDER BY l.ticker;
