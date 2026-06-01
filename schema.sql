-- schema.sql
-- Definicja tabel bazy danych finance.db (SQLite)

-- Tabela cen ETF-ów i instrumentów finansowych
CREATE TABLE IF NOT EXISTS prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        DATE    NOT NULL,
    ticker      TEXT    NOT NULL,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL    NOT NULL,
    volume      REAL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, ticker)
);

CREATE INDEX IF NOT EXISTS idx_prices_date   ON prices(date);
CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(ticker);

-- Tabela kursów walut
CREATE TABLE IF NOT EXISTS exchange_rates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        DATE    NOT NULL,
    pair        TEXT    NOT NULL,   -- np. "USD_PLN", "EUR_PLN"
    close       REAL    NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, pair)
);

CREATE INDEX IF NOT EXISTS idx_fx_date ON exchange_rates(date);
CREATE INDEX IF NOT EXISTS idx_fx_pair ON exchange_rates(pair);

-- Tabela indeksów giełdowych
CREATE TABLE IF NOT EXISTS indices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        DATE    NOT NULL,
    symbol      TEXT    NOT NULL,   -- np. "^GSPC" (S&P500)
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL    NOT NULL,
    volume      REAL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, symbol)
);

CREATE INDEX IF NOT EXISTS idx_indices_date   ON indices(date);
CREATE INDEX IF NOT EXISTS idx_indices_symbol ON indices(symbol);
