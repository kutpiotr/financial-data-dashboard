"""
load_data.py
------------
Ładuje przetworzone pliki CSV do bazy SQLite (finance.db).

Funkcje:
- Logowanie liczby załadowanych rekordów
- Obsługa duplikatów przy ponownym uruchomieniu (INSERT OR REPLACE)
- Walidacja przed ładowaniem
"""

import os
import logging
import sqlite3
from typing import Optional

import pandas as pd

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "load_data.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

DB_PATH = "finance.db"
PROCESSED_DIR = os.path.join("data", "processed")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Baza danych nie istnieje: {db_path}. Uruchom najpierw db_setup.py"
        )
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def load_csv(filename: str) -> Optional[pd.DataFrame]:
    path = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(path):
        logger.error(f"Plik nie istnieje: {path}")
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    logger.info(f"Wczytano {path}: {len(df)} wierszy")
    return df


def upsert_prices(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """
    Ładuje ceny ETF-ów do tabeli prices.
    Dane z fetch_data mają kolumny: date, Close_VWRA.L, Close_SPY, ...
    Musimy je spivotować do formatu long (date, ticker, close, ...).
    """
    # Wykryj kolumny OHLCV per ticker
    close_cols = [c for c in df.columns if c.startswith("Close_") or c.lower() == "close"]
    if not close_cols:
        # Spróbuj znaleźć kolumny bez prefiksu (pojedynczy ticker)
        close_cols = [c for c in df.columns if c.lower() in ("close", "adj close")]

    records_loaded = 0
    cursor = conn.cursor()

    if len(close_cols) == 1 and close_cols[0].lower() in ("close", "adj close"):
        # Format z jednym tickerem — kolumna ticker nie istnieje, dodaj ją
        ticker_name = "UNKNOWN"
        rows = df[["date"] + close_cols].copy()
        rows.rename(columns={close_cols[0]: "close"}, inplace=True)
        rows["ticker"] = ticker_name
        for _, row in rows.iterrows():
            cursor.execute(
                """INSERT OR REPLACE INTO prices (date, ticker, close)
                   VALUES (?, ?, ?)""",
                (str(row["date"].date()), row["ticker"], row["close"]),
            )
            records_loaded += 1
    else:
        # Format multi-ticker (kolumny: Close_SPY, Close_VWRA.L, ...)
        for col in close_cols:
            ticker = col.replace("Close_", "").replace("Adj Close_", "")
            open_col = col.replace("Close_", "Open_")
            high_col = col.replace("Close_", "High_")
            low_col  = col.replace("Close_", "Low_")
            vol_col  = col.replace("Close_", "Volume_")

            for _, row in df.iterrows():
                close_val = row.get(col)
                if pd.isna(close_val):
                    continue
                cursor.execute(
                    """INSERT OR REPLACE INTO prices
                       (date, ticker, open, high, low, close, volume)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(row["date"].date()),
                        ticker,
                        row.get(open_col) if not pd.isna(row.get(open_col, float("nan"))) else None,
                        row.get(high_col) if not pd.isna(row.get(high_col, float("nan"))) else None,
                        row.get(low_col)  if not pd.isna(row.get(low_col,  float("nan"))) else None,
                        float(close_val),
                        row.get(vol_col)  if not pd.isna(row.get(vol_col,  float("nan"))) else None,
                    ),
                )
                records_loaded += 1

    conn.commit()
    return records_loaded


def upsert_exchange_rates(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Ładuje kursy walut do tabeli exchange_rates."""
    cursor = conn.cursor()
    records_loaded = 0

    required = {"date", "pair", "close"}
    if not required.issubset(df.columns):
        logger.error(f"Brak kolumn w exchange_rates: {required - set(df.columns)}")
        return 0

    for _, row in df.iterrows():
        cursor.execute(
            """INSERT OR REPLACE INTO exchange_rates (date, pair, close)
               VALUES (?, ?, ?)""",
            (str(row["date"].date()), row["pair"], float(row["close"])),
        )
        records_loaded += 1

    conn.commit()
    return records_loaded


def upsert_indices(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Ładuje dane indeksów do tabeli indices."""
    cursor = conn.cursor()
    records_loaded = 0

    close_cols = [c for c in df.columns if "close" in c.lower()]
    if not close_cols:
        logger.error("Brak kolumny close w danych indeksów")
        return 0

    close_col = close_cols[0]
    symbol = "^GSPC"  # domyślnie S&P500

    for _, row in df.iterrows():
        close_val = row.get(close_col)
        if pd.isna(close_val):
            continue
        cursor.execute(
            """INSERT OR REPLACE INTO indices
               (date, symbol, close)
               VALUES (?, ?, ?)""",
            (str(row["date"].date()), symbol, float(close_val)),
        )
        records_loaded += 1

    conn.commit()
    return records_loaded


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return row[0] if row else 0


def main():
    logger.info("=== START: load_data.py ===")

    conn = get_connection()
    try:
        # 1. Ceny ETF-ów
        df_etfs = load_csv("etf_prices_clean.csv")
        if df_etfs is not None:
            n = upsert_prices(conn, df_etfs)
            logger.info(f"prices: załadowano {n} rekordów (łącznie w bazie: {count_rows(conn, 'prices')})")

        # 2. Kursy walut
        df_fx = load_csv("exchange_rates_clean.csv")
        if df_fx is not None:
            n = upsert_exchange_rates(conn, df_fx)
            logger.info(f"exchange_rates: załadowano {n} rekordów (łącznie: {count_rows(conn, 'exchange_rates')})")

        # 3. S&P500
        df_sp = load_csv("sp500_clean.csv")
        if df_sp is not None:
            n = upsert_indices(conn, df_sp)
            logger.info(f"indices: załadowano {n} rekordów (łącznie: {count_rows(conn, 'indices')})")

    finally:
        conn.close()

    logger.info("=== KONIEC: load_data.py ===")


if __name__ == "__main__":
    main()
