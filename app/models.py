from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Route(str, Enum):
    query_sales = "query_sales"
    email_report = "email_report"


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=3)
    recipient: str | None = None


class AgentResponse(BaseModel):
    route: Route
    answer: str
    report_path: Path | None = None
    emailed_to: str | None = None
    data: dict[str, Any] | None = None


class SalesSummary(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    total_orders: int = 0
    total_quantity: int = 0
    gross_revenue: float = 0
    average_order_value: float = 0
    top_categories: list[dict[str, Any]] = Field(default_factory=list)
    top_regions: list[dict[str, Any]] = Field(default_factory=list)
    top_products: list[dict[str, Any]] = Field(default_factory=list)
