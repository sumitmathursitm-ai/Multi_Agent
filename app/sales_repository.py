from collections import defaultdict
from datetime import date, timedelta
import re
from typing import Any

from dateutil.parser import parse

from app.config import get_settings
from app.models import SalesSummary
from app.supabase_client import get_supabase


def _parse_date_from_query(query: str) -> tuple[date | None, date | None]:
    lowered = query.lower()
    today = date.today()
    if "today" in lowered:
        return today, today
    if "this week" in lowered:
        start = today - timedelta(days=today.weekday())
        return start, today
    if "this month" in lowered:
        return today.replace(day=1), today
    if "this year" in lowered:
        return today.replace(month=1, day=1), today

    tokens = re.findall(r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{2,4}", query)
    dates: list[date] = []
    for word in tokens:
        try:
            parsed = parse(word, fuzzy=False).date()
        except (ValueError, OverflowError):
            continue
        dates.append(parsed)
    if len(dates) >= 2:
        return min(dates), max(dates)
    if len(dates) == 1:
        return dates[0], None
    return None, None


def fetch_sales_rows(query: str = "", limit: int = 1000) -> list[dict[str, Any]]:
    settings = get_settings()
    start_date, end_date = _parse_date_from_query(query)
    request = get_supabase().table(settings.supabase_sales_table).select("*").order("order_date", desc=True).limit(limit)
    if start_date:
        request = request.gte("order_date", start_date.isoformat())
    if end_date:
        request = request.lte("order_date", end_date.isoformat())
    response = request.execute()
    return response.data or []


def summarize_sales(rows: list[dict[str, Any]]) -> SalesSummary:
    if not rows:
        return SalesSummary()

    total_revenue = sum(float(row["revenue"]) for row in rows)
    total_quantity = sum(int(row["quantity"]) for row in rows)
    category_revenue: dict[str, float] = defaultdict(float)
    region_revenue: dict[str, float] = defaultdict(float)
    product_revenue: dict[str, float] = defaultdict(float)
    dates = [parse(str(row["order_date"])).date() for row in rows]

    for row in rows:
        revenue = float(row["revenue"])
        category_revenue[str(row["product_category"])] += revenue
        region_revenue[str(row["region"])] += revenue
        product_revenue[str(row["product_name"])] += revenue

    return SalesSummary(
        start_date=min(dates),
        end_date=max(dates),
        total_orders=len(rows),
        total_quantity=total_quantity,
        gross_revenue=round(total_revenue, 2),
        average_order_value=round(total_revenue / len(rows), 2),
        top_categories=_top_items(category_revenue),
        top_regions=_top_items(region_revenue),
        top_products=_top_items(product_revenue),
    )


def _top_items(values: dict[str, float], limit: int = 5) -> list[dict[str, Any]]:
    return [
        {"name": name, "revenue": round(revenue, 2)}
        for name, revenue in sorted(values.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]
