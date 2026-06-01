-- 02_fx_volatility.sql
-- Liczy zmienność kursów walut: tygodniowe odchylenie standardowe,
-- miesięczne min/max oraz procentowe odchylenie od 30-dniowej średniej.
-- Alerty na odchylenia większe niż 2%.

SELECT
    date,
    pair,
    close,
    -- 30-dniowa średnia krocząca kursu
    ROUND(
        AVG(close) OVER (
            PARTITION BY pair
            ORDER BY date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 4
    ) AS avg_30d,
    -- Zmienność: odchylenie standardowe z ostatnich 20 dni
    ROUND(
        (
            -- Wariancja: avg(x^2) - avg(x)^2
            SQRT(
                AVG(close * close) OVER (
                    PARTITION BY pair
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                )
                -
                AVG(close) OVER (
                    PARTITION BY pair
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) *
                AVG(close) OVER (
                    PARTITION BY pair
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                )
            )
        ), 4
    ) AS stddev_20d,
    -- Procentowe odchylenie od 30-dniowej średniej
    ROUND(
        (close - AVG(close) OVER (
            PARTITION BY pair
            ORDER BY date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        )) / AVG(close) OVER (
            PARTITION BY pair
            ORDER BY date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) * 100, 2
    ) AS pct_dev_30d,
    -- Flaga alertu: odchylenie > 2%
    CASE
        WHEN ABS(
            (close - AVG(close) OVER (
                PARTITION BY pair
                ORDER BY date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            )) / AVG(close) OVER (
                PARTITION BY pair
                ORDER BY date
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ) * 100
        ) > 2.0 THEN 1
        ELSE 0
    END AS alert_flag
FROM exchange_rates
ORDER BY pair, date;
