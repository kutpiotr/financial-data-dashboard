"""
clean_data.py
-------------
Czyści i waliduje surowe pliki CSV z folderu data/raw/.
Wyniki zapisywane do data/processed/.

Operacje:
- Usuwanie duplikatów
- Obsługa brakujących wartości
- Standaryzacja formatów dat
- Walidacja kompletności (czy wszystkie dni robocze są pokryte)
"""

import os
import logging
from datetime import date

import numpy as np
import pandas as pd

# --- Konfiguracja ---
RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")
LOG_DIR = "logs"
os.makedirs(PROCESSED_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "clean_data.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        logger.error(f"Plik nie istnieje: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    logger.info(f"Wczytano {path}: {len(df)} wierszy, {df.shape[1]} kolumn")
    return df


def standardize_dates(df: pd.DataFrame, col: str = "date") -> pd.DataFrame:
    """Konwertuje kolumnę dat do formatu YYYY-MM-DD."""
    df[col] = pd.to_datetime(df[col]).dt.normalize()
    return df


def remove_duplicates(df: pd.DataFrame, subset: list[str]) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="last")
    removed = before - len(df)
    if removed:
        logger.warning(f"Usunięto {removed} duplikatów (klucz: {subset})")
    return df


def handle_missing(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    """Wypełnia braki metodą forward-fill, potem backward-fill."""
    missing_before = df[numeric_cols].isnull().sum().sum()
    df[numeric_cols] = df[numeric_cols].ffill().bfill()
    missing_after = df[numeric_cols].isnull().sum().sum()
    if missing_before:
        logger.warning(
            f"Obsłużono brakujące wartości: {missing_before} -> {missing_after} braków"
        )
    return df


def validate_business_days(df: pd.DataFrame, date_col: str = "date") -> None:
    """Sprawdza czy są luki w dniach roboczych."""
    dates = pd.to_datetime(df[date_col]).sort_values().unique()
    if len(dates) < 2:
        return
    full_range = pd.bdate_range(start=dates[0], end=dates[-1])
    missing = set(full_range.date) - set(pd.to_datetime(dates).date)
    if missing:
        logger.warning(
            f"Brakujące dni robocze ({len(missing)}): "
            f"{sorted(missing)[:5]}{'...' if len(missing) > 5 else ''}"
        )
    else:
        logger.info("Walidacja dni roboczych: OK")


def clean_etf_prices(filename: str = "etf_prices_raw.csv") -> pd.DataFrame:
    df = load_csv(filename)
    if df.empty:
        return df

    df = standardize_dates(df, "date")

    # Kolumny numeryczne to wszystko poza 'date'
    numeric_cols = [c for c in df.columns if c != "date"]

    df = remove_duplicates(df, subset=["date"])
    df = handle_missing(df, numeric_cols)
    validate_business_days(df)

    # Usuń wiersze gdzie wszystkie ceny są NaN
    df = df.dropna(subset=numeric_cols, how="all")

    df = df.sort_values("date").reset_index(drop=True)
    logger.info(f"ETF prices po czyszczeniu: {len(df)} wierszy")
    return df


def clean_exchange_rates(filename: str = "exchange_rates_raw.csv") -> pd.DataFrame:
    df = load_csv(filename)
    if df.empty:
        return df

    df = standardize_dates(df, "date")
    df = remove_duplicates(df, subset=["date", "pair"])
    df = handle_missing(df, ["close"])

    # Walidacja dla każdej pary osobno
    for pair in df["pair"].unique():
        subset = df[df["pair"] == pair]
        logger.info(f"Waluta {pair}: {len(subset)} wierszy")
        validate_business_days(subset)

    df = df.sort_values(["pair", "date"]).reset_index(drop=True)
    logger.info(f"Exchange rates po czyszczeniu: {len(df)} wierszy")
    return df


def clean_sp500(filename: str = "sp500_raw.csv") -> pd.DataFrame:
    df = load_csv(filename)
    if df.empty:
        return df

    df = standardize_dates(df, "date")

    numeric_cols = [c for c in df.columns if c != "date"]
    df = remove_duplicates(df, subset=["date"])
    df = handle_missing(df, numeric_cols)
    validate_business_days(df)

    df = df.sort_values("date").reset_index(drop=True)
    logger.info(f"S&P500 po czyszczeniu: {len(df)} wierszy")
    return df


def save_csv(df: pd.DataFrame, filename: str) -> None:
    if df.empty:
        logger.warning(f"Pusty DataFrame — pominięto zapis: {filename}")
        return
    path = os.path.join(PROCESSED_DIR, filename)
    df.to_csv(path, index=False)
    logger.info(f"Zapisano: {path}")


def main():
    logger.info("=== START: clean_data.py ===")

    df_etfs = clean_etf_prices()
    save_csv(df_etfs, "etf_prices_clean.csv")

    df_fx = clean_exchange_rates()
    save_csv(df_fx, "exchange_rates_clean.csv")

    df_sp500 = clean_sp500()
    save_csv(df_sp500, "sp500_clean.csv")

    logger.info("=== KONIEC: clean_data.py ===")


if __name__ == "__main__":
    main()
