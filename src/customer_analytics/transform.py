import pandas as pd


def _parse_date_columns(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        data[column] = pd.to_datetime(data[column], errors="coerce")
    return data


def _normalize_segment(series: pd.Series) -> pd.Series:
    segment_map = {
        "enterprise": "Enterprise",
        "mid-market": "Mid-Market",
        "smb": "SMB",
    }
    return series.str.strip().str.lower().map(segment_map).fillna(series.str.strip())


def clean_sources(sources: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    customers = sources["customers"].copy()
    customers["name"] = customers["name"].str.strip()
    customers["email"] = customers["email"].str.strip().str.lower()
    customers["segment"] = _normalize_segment(customers["segment"])
    customers = _parse_date_columns(customers, ["signup_date"])

    orders = sources["orders"].copy()
    orders["status"] = orders["status"].str.strip().str.lower()
    orders["product_category"] = orders["product_category"].str.strip().str.title()
    orders = _parse_date_columns(orders, ["order_date"])
    orders["gross_amount"] = orders["quantity"] * orders["unit_price"]
    orders["discount_amount"] = orders["gross_amount"] * orders["discount_pct"]
    orders["net_amount"] = orders["gross_amount"] - orders["discount_amount"]

    payments = sources["payments"].copy()
    payments["payment_status"] = payments["payment_status"].str.strip().str.lower()
    payments["payment_method"] = payments["payment_method"].str.strip().str.title()
    payments = _parse_date_columns(payments, ["processed_at"])

    campaigns = sources["campaigns"].copy()
    campaigns["segment"] = _normalize_segment(campaigns["segment"])
    campaigns["channel"] = campaigns["channel"].str.strip().str.title()
    campaigns = _parse_date_columns(campaigns, ["start_date", "end_date"])

    return {
        "customers": customers,
        "orders": orders,
        "payments": payments,
        "campaigns": campaigns,
    }


def build_warehouse_tables(cleaned: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    customers = cleaned["customers"]
    orders = cleaned["orders"]
    payments = cleaned["payments"]
    campaigns = cleaned["campaigns"]

    fact_orders = (
        orders.merge(customers[["customer_id", "segment", "country"]], on="customer_id", how="left")
        .merge(payments[["order_id", "payment_method", "payment_status"]], on="order_id", how="left")
    )
    fact_orders["order_month"] = fact_orders["order_date"].dt.to_period("M").astype(str)
    fact_orders["is_completed_paid"] = (
        (fact_orders["status"] == "completed") & (fact_orders["payment_status"] == "paid")
    )

    paid_orders = fact_orders[fact_orders["is_completed_paid"]].copy()

    monthly_revenue = (
        paid_orders.groupby("order_month", as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            gross_revenue=("gross_amount", "sum"),
            discounts=("discount_amount", "sum"),
            net_revenue=("net_amount", "sum"),
        )
        .sort_values("order_month")
    )

    segment_performance = (
        paid_orders.groupby("segment", as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            net_revenue=("net_amount", "sum"),
            average_order_value=("net_amount", "mean"),
        )
        .sort_values("net_revenue", ascending=False)
    )

    customer_lifetime_value = (
        paid_orders.groupby("customer_id", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            lifetime_value=("net_amount", "sum"),
            first_order_date=("order_date", "min"),
            last_order_date=("order_date", "max"),
        )
        .merge(customers[["customer_id", "name", "email", "segment", "country"]], on="customer_id", how="left")
        .sort_values("lifetime_value", ascending=False)
    )

    campaign_performance = _build_campaign_performance(paid_orders, campaigns)

    return {
        "dim_customers": customers,
        "dim_campaigns": campaigns,
        "fact_orders": fact_orders,
        "fact_payments": payments,
        "mart_customer_lifetime_value": customer_lifetime_value,
        "mart_monthly_revenue": monthly_revenue,
        "mart_segment_performance": segment_performance,
        "mart_campaign_performance": campaign_performance,
    }


def _build_campaign_performance(orders: pd.DataFrame, campaigns: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for campaign in campaigns.itertuples(index=False):
        matched_orders = orders[
            (orders["segment"] == campaign.segment)
            & (orders["order_date"] >= campaign.start_date)
            & (orders["order_date"] <= campaign.end_date)
        ]
        revenue = float(matched_orders["net_amount"].sum())
        spend = float(campaign.spend)
        rows.append(
            {
                "campaign_id": campaign.campaign_id,
                "campaign_name": campaign.campaign_name,
                "segment": campaign.segment,
                "channel": campaign.channel,
                "spend": spend,
                "attributed_orders": int(matched_orders["order_id"].nunique()),
                "attributed_revenue": revenue,
                "roi": round((revenue - spend) / spend, 4) if spend else None,
            }
        )

    return pd.DataFrame(rows).sort_values("attributed_revenue", ascending=False)
