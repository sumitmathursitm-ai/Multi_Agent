from fastapi import FastAPI

from app.agents import SalesAgentOrchestrator
from app.models import AgentRequest, AgentResponse
from app.seed_sales import seed_sales


app = FastAPI(title="Ecommerce Sales Multi-Agent API")
orchestrator = SalesAgentOrchestrator()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agent", response_model=AgentResponse)
def run_agent(request: AgentRequest) -> AgentResponse:
    return orchestrator.run(request)


@app.post("/seed")
def seed(rows: int | None = None) -> dict[str, int]:
    inserted = seed_sales(rows)
    return {"inserted": inserted}
