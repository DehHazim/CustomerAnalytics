from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ANALYTICS_DIR = DATA_DIR / "analytics"
WAREHOUSE_DIR = PROJECT_ROOT / "warehouse"
WAREHOUSE_DB = WAREHOUSE_DIR / "customer_analytics.db"


def ensure_directories() -> None:
    for path in (RAW_DIR, PROCESSED_DIR, ANALYTICS_DIR, WAREHOUSE_DIR):
        path.mkdir(parents=True, exist_ok=True)
