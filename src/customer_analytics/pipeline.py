from .config import ANALYTICS_DIR, PROCESSED_DIR, RAW_DIR, WAREHOUSE_DB, ensure_directories
from .extract import extract_sources
from .load import load_sqlite, write_processed_csv, write_validation_report
from .transform import build_warehouse_tables, clean_sources
from .validate import validate_raw_sources


def run_pipeline() -> dict[str, object]:
    ensure_directories()

    sources = extract_sources(RAW_DIR)
    report = validate_raw_sources(sources)
    write_validation_report(report, ANALYTICS_DIR)

    if not report.passed:
        raise ValueError(f"Data validation failed. See {ANALYTICS_DIR / 'validation_report.json'}")

    cleaned = clean_sources(sources)
    tables = build_warehouse_tables(cleaned)
    write_processed_csv(tables, PROCESSED_DIR, ANALYTICS_DIR)
    database_path = load_sqlite(tables, WAREHOUSE_DB)

    return {
        "database": str(database_path),
        "processed_dir": str(PROCESSED_DIR),
        "analytics_dir": str(ANALYTICS_DIR),
        "tables": sorted(tables),
        "validation": report.to_dict(),
    }


def main() -> None:
    result = run_pipeline()
    print("Customer Analytics pipeline completed successfully.")
    print(f"SQLite warehouse: {result['database']}")
    print(f"Processed CSVs: {result['processed_dir']}")
    print(f"Analytics CSVs: {result['analytics_dir']}")
    print("Tables:")
    for table_name in result["tables"]:
        print(f" - {table_name}")
