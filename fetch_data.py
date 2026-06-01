"""
fetch_data.py
-------------
Pobiera dane finansowe z Yahoo Finance i zapisuje je jako surowe pliki CSV
w folderze data/raw/.

Dane pobierane:
- Ceny ETF-ów: VWRA.L, SPY, CSPX.L
- Kursy walut: USD/PLN, EUR/PLN
- Indeks S&P500: ^GSPC
"""

import os
import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

# --- Konfiguracja ---
RAW_DATA_DIR = os.path.join("data", "raw")
LOG_DIR = "logs"
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "fetch_data.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# --- Parametry pobierania ---
END_DATE = datetime.today().strftime("%Y-%m-%d")
START_DATE = (datetime.today() - timedelta(days=3 * 365)).strftime("%Y-%m-%d")

TICKERS = {
    "etfs": ["VWRA.L", "SPY", "CSPX.L"],
    "fx": ["PLN=X", "EURPLN=X"],   # USD/PLN, EUR/PLN
    "indices": ["^GSPC"],           # S&P500
}


def fetch_ohlcv(tickers: list[str], label: str) -> pd.DataFrame:
    """Pobiera dane OHLCV dla listy tickerów."""
    logger.info(f"Pobieranie danych dla {label}: {tickers}")
    try:
        raw = yf.download(
            tickers,
            start=START_DATE,
            end=END_DATE,
            auto_adjust=True,
            progress=False,
        )
        if raw.empty:
            logger.warning(f"Brak danych dla {label}")
            return pd.DataFrame()

        # Spłaszcz multi-level columns jeśli więcej niż jeden ticker
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = ["_".join(col).strip() for col in raw.columns.values]

        raw.index.name = "date"
        raw.reset_index(inplace=True)
        raw["date"] = pd.to_datetime(raw["date"]).dt.date
        logger.info(f"  -> {len(raw)} wierszy")
        return raw
    except Exception as e:
        logger.error(f"Błąd pobierania {label}: {e}")
        return pd.DataFrame()


def fetch_fx_rates(tickers: list[str]) -> pd.DataFrame:
    """Pobiera kursy walut i zwraca w znormalizowanym formacie."""
    logger.info(f"Pobieranie kursów walut: {tickers}")
    frames = []
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=START_DATE, end=END_DATE,
                             auto_adjust=True, progress=False)
            if df.empty:
                logger.warning(f"Brak danych dla {ticker}")
                continue
            df = df[["Close"]].copy()
            df.columns = ["close"]
            df.index.name = "date"
            df.reset_index(inplace=True)
            df["date"] = pd.to_datetime(df["date"]).dt.date
            # Ujednolicaj nazwy walut
            pair_map = {"PLN=X": "USD_PLN", "EURPLN=X": "EUR_PLN"}
            df["pair"] = pair_map.get(ticker, ticker)
            frames.append(df)
            logger.info(f"  {ticker}: {len(df)} wierszy")
        except Exception as e:
            logger.error(f"Błąd pobierania {ticker}: {e}")

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


def save_csv(df: pd.DataFrame, filename: str) -> None:
    """Zapisuje DataFrame do pliku CSV."""
    if df.empty:
        logger.warning(f"Pusty DataFrame — pominięto zapis: {filename}")
        return
    path = os.path.join(RAW_DATA_DIR, filename)
    df.to_csv(path, index=False)
    logger.info(f"Zapisano: {path} ({len(df)} wierszy)")


def main():
    logger.info("=== START: fetch_data.py ===")

    # 1. ETF-y
    df_etfs = fetch_ohlcv(TICKERS["etfs"], "ETFs")
    save_csv(df_etfs, "etf_prices_raw.csv")

    # 2. Kursy walut
    df_fx = fetch_fx_rates(TICKERS["fx"])
    save_csv(df_fx, "exchange_rates_raw.csv")

    # 3. S&P500
    df_sp500 = fetch_ohlcv(TICKERS["indices"], "S&P500")
    save_csv(df_sp500, "sp500_raw.csv")

    logger.info("=== KONIEC: fetch_data.py ===")


if __name__ == "__main__":
    main()
