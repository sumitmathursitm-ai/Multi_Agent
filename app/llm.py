import json
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.models import Route


ROUTER_SYSTEM_PROMPT = """You are a routing agent for an ecommerce sales assistant.
Choose exactly one route:
- query_sales: for questions asking to inspect, summarize, compare, or analyze sales data.
- email_report: for requests to create, send, mail, or share a PDF sales report.

Return only JSON with keys route and reason."""


ANSWER_SYSTEM_PROMPT = """You are a concise ecommerce sales analyst.
Use the provided sales summary JSON only. Explain the useful business takeaways in plain English."""


def _client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
        default_headers={
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        },
    )


def route_query(query: str) -> Route:
    settings = get_settings()
    heuristic_route = _heuristic_route(query)
    if heuristic_route == Route.email_report:
        return heuristic_route

    try:
        completion = _client().chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content or "{}"
        payload = json.loads(content)
        return Route(payload.get("route"))
    except Exception:
        return _heuristic_route(query)


def write_sales_answer(query: str, summary: dict[str, Any]) -> str:
    settings = get_settings()
    try:
        completion = _client().chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {query}\nSales summary JSON:\n{json.dumps(summary, indent=2)}"},
            ],
            temperature=0.2,
        )
        return completion.choices[0].message.content or _fallback_answer(summary)
    except Exception:
        return _fallback_answer(summary)


def _heuristic_route(query: str) -> Route:
    lowered = query.lower()
    email_actions = ("email", "gmail", "send", "mail", "share", "shoot")
    report_words = ("pdf", "report", "attachment")
    if any(word in lowered for word in email_actions) or any(word in lowered for word in report_words):
        return Route.email_report
    return Route.query_sales


def _fallback_answer(summary: dict[str, Any]) -> str:
    return (
        f"Found {summary.get('total_orders', 0)} orders with "
        f"${summary.get('gross_revenue', 0):,.2f} in gross revenue and an average order value of "
        f"${summary.get('average_order_value', 0):,.2f}."
    )
