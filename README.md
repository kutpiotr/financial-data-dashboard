# Financial Data Dashboard

> Python · SQLite · Excel · Power BI

Projekt demonstracyjny pokazujący kompletny pipeline danych finansowych:
pobieranie danych z API → czyszczenie → baza SQL → raporty Excel → dashboard Power BI.

---

## Opis projektu

Pipeline automatycznie pobiera dane z Yahoo Finance (ceny ETF-ów, kursy walutowe USD/PLN i EUR/PLN, indeks S&P500),
czyści je, ładuje do bazy SQLite, a następnie generuje:

- **Raport Excel** (`financial_report.xlsx`) z formatowaniem warunkowym
- **Dashboard Power BI** (instrukcja w `POWER_BI_GUIDE.md`)

---

## Instrumenty finansowe

| Kategoria | Ticker | Opis |
|---|---|---|
| ETF | VWRA.L | Vanguard FTSE All-World (LSE) |
| ETF | CSPX.L | iShares Core S&P 500 (LSE) |
| ETF | SPY | SPDR S&P 500 (NYSE) |
| Kurs walutowy | USD/PLN | Dolar amerykański do złotego |
| Kurs walutowy | EUR/PLN | Euro do złotego |
| Indeks | ^GSPC | S&P 500 |

---

## Struktura projektu

```
financial-data-dashboard/
├── data/
│   ├── raw/                    # Surowe pliki CSV pobrane z API
│   │   ├── etf_prices_raw.csv
│   │   ├── exchange_rates_raw.csv
│   │   └── sp500_raw.csv
│   └── processed/              # Przetworzone pliki CSV
│       ├── etf_prices_clean.csv
│       ├── exchange_rates_clean.csv
│       └── sp500_clean.csv
├── queries/                    # Analityczne zapytania SQL
│   ├── 01_moving_averages.sql  # Średnie kroczące SMA20/SMA50
│   ├── 02_fx_volatility.sql    # Zmienność kursów walut
│   ├── 03_monthly_returns.sql  # Miesięczne zwroty M/M
│   └── 04_nav_summary.sql      # Zestawienie NAV portfela
├── logs/                       # Logi z uruchomień skryptów
├── fetch_data.py               # Pobieranie danych z Yahoo Finance
├── clean_data.py               # Czyszczenie i walidacja danych
├── db_setup.py                 # Tworzenie bazy SQLite
├── load_data.py                # ETL: ładowanie danych do bazy
├── export_excel.py             # Generowanie raportu Excel
├── schema.sql                  # Definicja tabel bazy danych
├── POWER_BI_GUIDE.md           # Instrukcja budowy dashboardu Power BI
├── requirements.txt
└── .gitignore
```

---

## Instalacja i uruchomienie

### Wymagania

- Python 3.10+
- pip

### Krok 1 — Sklonuj repozytorium

```bash
git clone https://github.com/kutpiotr1/financial-data-dashboard.git
cd financial-data-dashboard
```

### Krok 2 — Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### Krok 3 — Uruchom pipeline

```bash
# 1. Pobierz dane (ostatnie 3 lata)
python fetch_data.py

# 2. Wyczyść i zwaliduj dane
python clean_data.py

# 3. Stwórz bazę SQLite
python db_setup.py

# 4. Załaduj dane do bazy
python load_data.py

# 5. Wygeneruj raport Excel
python export_excel.py
```

Po wykonaniu tych kroków znajdziesz:
- `data/raw/` — surowe pliki CSV
- `data/processed/` — przetworzone pliki CSV
- `finance.db` — baza SQLite z danymi
- `financial_report.xlsx` — raport Excel

---

## Opis skryptów

### `fetch_data.py`
Pobiera dane z Yahoo Finance za pomocą biblioteki `yfinance`. Parametry (tickery, zakres dat) są konfigurowane na początku pliku. Dane zapisywane są do `data/raw/` jako pliki CSV.

### `clean_data.py`
Przetwarza surowe CSV: usuwa duplikaty, wypełnia brakujące wartości metodą forward-fill/backward-fill, standaryzuje format dat oraz waliduje kompletność (sprawdza luki w dniach roboczych). Wyniki trafiają do `data/processed/`.

### `db_setup.py`
Tworzy bazę SQLite `finance.db` na podstawie pliku `schema.sql`. Używa `IF NOT EXISTS`, więc można uruchamiać wielokrotnie bez ryzyka utraty danych.

### `load_data.py`
Ładuje przetworzone CSV do odpowiednich tabel bazy (`prices`, `exchange_rates`, `indices`). Używa `INSERT OR REPLACE` do obsługi duplikatów przy ponownym uruchomieniu. Loguje liczbę załadowanych rekordów.

### `export_excel.py`
Generuje plik `financial_report.xlsx` z trzema arkuszami:
- **Summary NAV** — ostatnie ceny ETF-ów, zmiany dzienne i YTD (zielone/czerwone formatowanie)
- **Exchange Rates** — kursy walut z odchyleniami od 30-dniowej średniej (alert pomarańczowy >2%)
- **Monthly Returns** — pivot z miesięcznymi zwrotami procentowymi

---

## Zapytania SQL

Folder `queries/` zawiera gotowe zapytania analityczne:

| Plik | Opis |
|---|---|
| `01_moving_averages.sql` | SMA20 i SMA50 dla każdego instrumentu |
| `02_fx_volatility.sql` | Zmienność kursów walut (stddev 20d, odchylenie od avg30d) |
| `03_monthly_returns.sql` | Miesięczne zwroty procentowe M/M |
| `04_nav_summary.sql` | NAV portfela: ostatnia cena, zmiana dzienna, YTD |

Przykładowe uruchomienie:
```bash
sqlite3 finance.db < queries/01_moving_averages.sql
```

---

## Power BI Dashboard

Szczegółowa instrukcja budowy dashboardu krok po kroku znajduje się w pliku [`POWER_BI_GUIDE.md`](POWER_BI_GUIDE.md).

Dashboard zawiera dwie strony:
1. **ETF Prices** — wykres liniowy cen + karty KPI (cena, zmiana dzienna %, YTD %) + slicer dat
2. **FX Rates** — tabela kursów walut z alertem na odchylenia >2% + wykres trendu

---

## Logi

Każdy skrypt zapisuje logi do folderu `logs/`:
- `fetch_data.log` — liczba pobranych wierszy per instrument
- `clean_data.log` — informacje o duplikatach i brakach
- `db_setup.log` — lista tabel w bazie
- `load_data.log` — liczba załadowanych rekordów per tabela
- `export_excel.log` — status generowania raportu

---

## Licencja

MIT
