import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

from .validate import ValidationReport


def write_processed_csv(tables: dict[str, pd.DataFrame], processed_dir: Path, analytics_dir: Path) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    analytics_dir.mkdir(parents=True, exist_ok=True)

    for table_name, data in tables.items():
        output_dir = analytics_dir if table_name.startswith("mart_") else processed_dir
        data.to_csv(output_dir / f"{table_name}.csv", index=False)


def load_sqlite(tables: dict[str, pd.DataFrame], database_path: Path) -> Path:
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="customer_analytics_", ignore_cleanup_errors=True) as temp_dir:
        temp_database = Path(temp_dir) / database_path.name

        connection = sqlite3.connect(temp_database)
        try:
            for table_name, data in tables.items():
                data.to_sql(table_name, connection, if_exists="replace", index=False)
            connection.commit()
        finally:
            connection.close()

        if _copy_and_verify_database(temp_database, database_path):
            return database_path

        fallback_path = Path(tempfile.gettempdir()) / "CustomerAnalytics" / database_path.name
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        if _copy_and_verify_database(temp_database, fallback_path):
            return fallback_path

        raise OSError("Unable to create a readable SQLite warehouse")


def _copy_and_verify_database(source: Path, target: Path) -> bool:
    try:
        shutil.copy2(source, target)
        with sqlite3.connect(target) as connection:
            connection.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
        return True
    except sqlite3.Error:
        return False
    except OSError:
        return False


def write_validation_report(report: ValidationReport, analytics_dir: Path) -> None:
    analytics_dir.mkdir(parents=True, exist_ok=True)
    report_path = analytics_dir / "validation_report.json"
    report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
