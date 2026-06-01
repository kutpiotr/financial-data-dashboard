# Power BI Dashboard — Instrukcja konfiguracji

Ponieważ pliki `.pbix` nie mogą być generowane programistycznie, poniżej znajdziesz
krok po kroku jak zbudować dashboard opisany w projekcie.

---

## Wymagania

- Power BI Desktop (bezpłatny, [pobierz tutaj](https://powerbi.microsoft.com/pl-pl/desktop/))
- Sterownik ODBC do SQLite: [SQLite ODBC Driver](http://www.ch-werner.de/sqliteodbc/)

---

## Krok 1 — Połącz się z bazą SQLite

1. Otwórz Power BI Desktop
2. Kliknij **Pobierz dane** → **Więcej...**
3. Wyszukaj **ODBC** i kliknij **Połącz**
4. W oknie ODBC wybierz **SQLite3 Datasource** lub wpisz connection string:
   ```
   Driver={SQLite3 ODBC Driver};Database=C:\ścieżka\do\finance.db;
   ```
5. Kliknij **OK** → załaduj tabele: `prices`, `exchange_rates`, `indices`

---

## Krok 2 — Transformacje w Power Query

Po załadowaniu danych kliknij **Przekształć dane**:

- `prices.date` → zmień typ na **Data**
- `exchange_rates.date` → zmień typ na **Data**
- `indices.date` → zmień typ na **Data**
- Upewnij się, że `close` ma typ **Liczba dziesiętna**

---

## Krok 3 — Miary DAX

W zakładce **Modelowanie** → **Nowa miara** dodaj:

```dax
-- Ostatnia cena
Ostatnia cena =
CALCULATE(LASTNONBLANK(prices[close], 1), ALLEXCEPT(prices, prices[ticker]))

-- Zmiana 1-dniowa %
Zmiana dzienna % =
VAR ostatnia = CALCULATE(MAX(prices[close]), ALLEXCEPT(prices, prices[ticker]))
VAR poprzednia = CALCULATE(
    MAX(prices[close]),
    FILTER(ALLEXCEPT(prices, prices[ticker]),
           prices[date] = EDATE(MAX(prices[date]), 0) - 1))
RETURN DIVIDE(ostatnia - poprzednia, poprzednia) * 100

-- Zwrot YTD
Zwrot YTD % =
VAR cena_teraz = MAX(prices[close])
VAR cena_poczatek = CALCULATE(
    FIRSTNONBLANK(prices[close], 1),
    FILTER(ALL(prices), YEAR(prices[date]) = YEAR(TODAY()) AND prices[ticker] = MAX(prices[ticker])))
RETURN DIVIDE(cena_teraz - cena_poczatek, cena_poczatek) * 100
```

---

## Krok 4 — Strona 1: Ceny ETF-ów

**Elementy wizualne:**

| Wizualizacja | Pola | Opis |
|---|---|---|
| Wykres liniowy | Oś X: `date`, Wartości: `close`, Legenda: `ticker` | Historyczne ceny ETF-ów |
| Karta KPI | Miara: `Ostatnia cena` | Aktualna cena każdego ETF |
| Karta KPI | Miara: `Zmiana dzienna %` | Zmiana z poprzedniego dnia |
| Karta KPI | Miara: `Zwrot YTD %` | Zwrot od początku roku |
| Slicer dat | `prices[date]` | Filtr zakresu dat |
| Slicer tickerów | `prices[ticker]` | Filtr instrumentów |

**Formatowanie warunkowe kart KPI:**
- Zielony gdy wartość > 0, Czerwony gdy < 0
- Kliknij kartę → Format → Kolor czcionki → Formatowanie warunkowe → Reguły

---

## Krok 5 — Strona 2: Kursy walut

**Elementy wizualne:**

| Wizualizacja | Pola | Opis |
|---|---|---|
| Tabela | `date`, `pair`, `close` | Tabela kursów |
| Wykres liniowy | Oś X: `date`, Wartości: `close`, Legenda: `pair` | Trend kursów |
| Karta | `close` (ostatni) | Aktualny kurs |

**Alert na odchylenia > 2%:**
1. W tabeli zaznacz kolumnę `pct_dev` (jeśli ją dodałeś w Power Query)
2. Format → Formatowanie warunkowe → Kolor tła
3. Ustaw reguły: `wartość > 2` → pomarańczowy, `wartość < -2` → pomarańczowy

**Miara odchylenia:**
```dax
Odchylenie od sr. 30d % =
VAR srednia30 = AVERAGEX(
    FILTER(exchange_rates,
           exchange_rates[pair] = MAX(exchange_rates[pair]) &&
           exchange_rates[date] >= MAX(exchange_rates[date]) - 30),
    exchange_rates[close])
RETURN DIVIDE(MAX(exchange_rates[close]) - srednia30, srednia30) * 100
```

---

## Krok 6 — Slicer dat (wspólny dla obu stron)

1. Wstaw **Slicer** → wybierz `date`
2. Zmień typ na **Zakres dat** (Formatowanie → Typ slicera → Zakres)
3. Zsynchronizuj slicery między stronami: **Widok** → **Synchronizuj slicery**

---

## Krok 7 — Publikacja (opcjonalnie)

Aby udostępnić dashboard:
1. Kliknij **Opublikuj** w Power BI Desktop
2. Zaloguj się kontem Microsoft (wymagane konto Power BI Service)
3. Wybierz obszar roboczy

---

## Struktura pliku .pbix (do referencji)

```
dashboard.pbix
├── Połączenia danych → SQLite (ODBC)
├── Tabele: prices, exchange_rates, indices
├── Miary DAX: Ostatnia cena, Zmiana dzienna %, Zwrot YTD %, Odchylenie od sr. 30d %
├── Strona 1: ETF Prices (line chart + 3x KPI card + 2x slicer)
└── Strona 2: FX Rates (tabela + line chart + alert na odchylenia)
```
