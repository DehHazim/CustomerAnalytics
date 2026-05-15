import json
from pathlib import Path

import pandas as pd


def read_csv_source(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def read_json_source(path: Path, record_path: str | None = None) -> pd.DataFrame:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if record_path:
        payload = payload[record_path]

    return pd.DataFrame(payload)


def extract_sources(raw_dir: Path) -> dict[str, pd.DataFrame]:
    """Extract data from local files that represent CSV, JSON, and API sources."""
    return {
        "customers": read_csv_source(raw_dir / "customers.csv"),
        "orders": read_csv_source(raw_dir / "orders.csv"),
        "campaigns": read_json_source(raw_dir / "campaigns.json", record_path="campaigns"),
        "payments": read_json_source(raw_dir / "api_payments.json", record_path="payments"),
    }
