import argparse
import json

from app.agents import SalesAgentOrchestrator
from app.models import AgentRequest
from app.seed_sales import seed_sales


def main() -> None:
    parser = argparse.ArgumentParser(description="Ecommerce sales multi-agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Generate fake sales rows and insert them into Supabase")
    seed_parser.add_argument("--rows", type=int, default=None)

    ask_parser = subparsers.add_parser("ask", help="Ask the multi-agent orchestrator a question")
    ask_parser.add_argument("query")
    ask_parser.add_argument("--recipient", default=None)

    args = parser.parse_args()

    if args.command == "seed":
        inserted = seed_sales(args.rows)
        print(json.dumps({"inserted": inserted}, indent=2))
        return

    response = SalesAgentOrchestrator().run(AgentRequest(query=args.query, recipient=args.recipient))
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
