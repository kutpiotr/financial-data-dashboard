"""
db_setup.py
-----------
Tworzy bazę SQLite (finance.db) z tabelami zdefiniowanymi w schema.sql.
Można uruchamiać wielokrotnie — używa IF NOT EXISTS.
"""

import os
import logging
import sqlite3

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "db_setup.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

DB_PATH = "finance.db"
SCHEMA_PATH = "schema.sql"


def create_database(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH) -> None:
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Brak pliku schema: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        logger.info(f"Baza danych utworzona/zaktualizowana: {db_path}")

        # Weryfikacja — lista tabel
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Tabele w bazie: {tables}")
    finally:
        conn.close()


def main():
    logger.info("=== START: db_setup.py ===")
    create_database()
    logger.info("=== KONIEC: db_setup.py ===")


if __name__ == "__main__":
    main()
