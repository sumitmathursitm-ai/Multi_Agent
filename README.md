# Ecommerce Sales Multi-Agent

A Python multi-agent solution for an ecommerce company. It can:

- Generate fake sales data with Faker.
- Store the generated sales data in Supabase.
- Route a natural-language request with an OpenRouter LLM.
- Query Supabase for sales summaries.
- Generate a PDF sales report.
- Send the PDF report through Gmail SMTP.
- Use a Streamlit chat UI for browser-based querying.
- Run locally as a CLI or API.
- Deploy to Railway.

## Architecture

```mermaid
flowchart LR
  U["User query"] --> R["RouterAgent - OpenRouter"]
  R -->|sales question| S["SupabaseSalesAgent"]
  R -->|send report| G["GmailReportAgent"]
  S --> DB["Supabase sales_orders"]
  G --> DB
  G --> P["PDF generator"]
  P --> M["Gmail SMTP"]
```

## 1. Create the Supabase Table

Open your Supabase project, go to **SQL Editor**, and run the SQL in:

```bash
supabase_schema.sql
```

Use your Supabase **service role key** for this backend service because it inserts and reads sales rows.

## 2. Configure Environment Variables

Create a local `.env` file:

```bash
cp .env.example .env
```

Fill these values:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_SALES_TABLE=sales_orders

OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=Ecom Sales Agent

GMAIL_SENDER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
GMAIL_RECIPIENT=recipient@gmail.com
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=465

REPORT_OUTPUT_DIR=reports
SEED_DEFAULT_ROWS=250
```

For Gmail, enable 2-Step Verification on the sender account and create an **App Password**. Use that app password, not your normal Gmail password.

Gmail checklist:

1. `GMAIL_SENDER` must be the exact Gmail account that created the app password.
2. `GMAIL_APP_PASSWORD` must be a Gmail App Password from Google Account -> Security -> 2-Step Verification -> App passwords.
3. Do not use your normal Gmail login password.
4. If Google displays the app password with spaces, either paste it as-is or remove spaces. The app strips spaces automatically.
5. After editing `.env`, stop Streamlit with `Ctrl+C` and start it again.

If you see `535 Username and Password not accepted`, the code reached Gmail but Gmail rejected the credentials. Generate a fresh app password and update `.env`.

If the error mentions `your-email@gmail.com`, Streamlit is still reading the placeholder value. Update `.env`, then use the Streamlit sidebar **Gmail diagnostics -> Reload .env** button or restart Streamlit completely.

You can confirm the exact `.env` file and masked Gmail account being loaded with:

```bash
python -c "from app.config import settings_debug_summary; from app.emailer import gmail_debug_summary; print(settings_debug_summary()); print(gmail_debug_summary())"
```

## 3. Run Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 4. Run the Streamlit Chat UI Locally

After creating `.env`, installing dependencies, and creating the Supabase table, start the chat UI:

```bash
streamlit run streamlit_app.py
```

Streamlit will open a local browser page, usually:

```text
http://localhost:8501
```

In the UI:

1. Use the sidebar **Generate sales data** button to create fake ecommerce sales rows in Supabase.
2. Ask sales questions in the chat box.
3. Ask for reports with prompts like `Send a PDF sales report to my Gmail`.
4. Optionally enter a one-off recipient email in the sidebar before asking for a report.
5. Download the generated PDF from the chat response if you want a local copy.

Example chat prompts:

```text
What are my top products this month?
Summarize gross revenue and top regions.
Send a PDF sales report to my Gmail.
Email the latest sales report to finance@example.com.
```

## 5. Optional CLI Usage

Seed fake ecommerce sales data into Supabase:

```bash
python cli.py seed --rows 500
```

Ask a sales question:

```bash
python cli.py ask "What are my top sales categories this month?"
```

Generate and email a PDF report:

```bash
python cli.py ask "Send a PDF sales report to my Gmail"
```

Send to a one-off recipient:

```bash
python cli.py ask "Email the latest sales report" --recipient someone@example.com
```

## 6. Run as an API

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Seed data:

```bash
curl -X POST "http://localhost:8000/seed?rows=500"
```

Ask the agent:

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"query":"Summarize total sales and top products"}'
```

Email report:

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"query":"Send my sales PDF report to Gmail"}'
```

## 7. Deploy to Railway

1. Push this project to GitHub.
2. Create a new Railway project from that GitHub repo.
3. Add the same `.env` values in Railway **Variables**.

Railway does not use your local `.env` file at runtime. Add these variables in the Railway service settings:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_SALES_TABLE
OPENROUTER_API_KEY
OPENROUTER_MODEL
OPENROUTER_SITE_URL
OPENROUTER_APP_NAME
GMAIL_SENDER
GMAIL_APP_PASSWORD
GMAIL_RECIPIENT
GMAIL_SMTP_HOST
GMAIL_SMTP_PORT
REPORT_OUTPUT_DIR
SEED_DEFAULT_ROWS
```

Deploy this repo as two Railway services:

### Service 1: Streamlit UI

Create one Railway service for the Streamlit chat UI.

Start command:

```bash
./start.sh
```

This runs:

```bash
streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=$PORT --server.headless=true
```

### Service 2: FastAPI Backend

Create a second Railway service from the same GitHub repo for the API.

Start command:

```bash
./start_api.sh
```

This runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Railway gives each service its own `$PORT`, so do not try to run both Streamlit and FastAPI inside the same Railway service.

After deployment, seed data once from your FastAPI Railway service endpoint:

```bash
curl -X POST "https://your-railway-domain.up.railway.app/seed?rows=500"
```

Query the hosted FastAPI agent:

```bash
curl -X POST https://your-railway-domain.up.railway.app/agent \
  -H "Content-Type: application/json" \
  -d '{"query":"Send a PDF sales report to my Gmail"}'
```

Use the Streamlit service URL for the browser chat UI.

## Query Examples

Sales data questions:

```text
What is my gross revenue?
What are the top 5 products by revenue?
Summarize sales from 2026-01-01 to 2026-03-31.
Which region is performing best?
```

Email/report requests:

```text
Send a PDF sales report to my Gmail.
Email me the latest sales report.
Create and send a sales PDF.
```

## Notes

- The router uses OpenRouter to classify each request as either `query_sales` or `email_report`.
- PDF reports are saved locally in `reports/` before being emailed.
- Date filtering supports explicit dates like `2026-01-01 to 2026-03-31`.
- Keep `.env` private. Never commit real API keys or Gmail app passwords.
