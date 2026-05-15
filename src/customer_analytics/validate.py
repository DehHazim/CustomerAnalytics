from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _require_columns(report: ValidationReport, table_name: str, data: pd.DataFrame, columns: set[str]) -> None:
    missing = columns.difference(data.columns)
    if missing:
        report.add_error(f"{table_name} is missing required columns: {sorted(missing)}")


def _require_unique(report: ValidationReport, table_name: str, data: pd.DataFrame, column: str) -> None:
    duplicate_count = int(data[column].duplicated().sum())
    if duplicate_count:
        report.add_error(f"{table_name}.{column} has {duplicate_count} duplicate values")


def validate_raw_sources(sources: dict[str, pd.DataFrame]) -> ValidationReport:
    report = ValidationReport()

    required_columns = {
        "customers": {"customer_id", "name", "email", "signup_date", "city", "country", "segment"},
        "orders": {
            "order_id",
            "customer_id",
            "order_date",
            "product_category",
            "quantity",
            "unit_price",
            "discount_pct",
            "status",
        },
        "payments": {"payment_id", "order_id", "payment_method", "payment_status", "processed_at"},
        "campaigns": {"campaign_id", "segment", "channel", "campaign_name", "spend", "start_date", "end_date"},
    }

    for table_name, columns in required_columns.items():
        _require_columns(report, table_name, sources[table_name], columns)

    if report.errors:
        return report

    _require_unique(report, "customers", sources["customers"], "customer_id")
    _require_unique(report, "orders", sources["orders"], "order_id")
    _require_unique(report, "payments", sources["payments"], "payment_id")
    _require_unique(report, "campaigns", sources["campaigns"], "campaign_id")

    missing_customers = set(sources["orders"]["customer_id"]).difference(sources["customers"]["customer_id"])
    if missing_customers:
        report.add_error(f"orders contains unknown customer_id values: {sorted(missing_customers)}")

    missing_orders = set(sources["payments"]["order_id"]).difference(sources["orders"]["order_id"])
    if missing_orders:
        report.add_error(f"payments contains unknown order_id values: {sorted(missing_orders)}")

    if (sources["orders"]["quantity"] <= 0).any():
        report.add_error("orders.quantity must be greater than zero")

    if (sources["orders"]["unit_price"] < 0).any():
        report.add_error("orders.unit_price must be non-negative")

    if ((sources["orders"]["discount_pct"] < 0) | (sources["orders"]["discount_pct"] > 1)).any():
        report.add_error("orders.discount_pct must be between 0 and 1")

    unpaid_completed = sources["payments"].query("payment_status != 'paid'")
    if not unpaid_completed.empty:
        report.add_warning(f"{len(unpaid_completed)} payment records are not paid and will remain visible for audit")

    return report
