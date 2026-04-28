from pathlib import Path

import streamlit as st

from app.agents import SalesAgentOrchestrator
from app.config import reload_settings, settings_debug_summary
from app.emailer import email_debug_summary, test_email_provider
from app.models import AgentRequest
from app.seed_sales import seed_sales


st.set_page_config(page_title="Ecom Sales Agent", page_icon="📊", layout="wide")


def get_orchestrator() -> SalesAgentOrchestrator:
    return SalesAgentOrchestrator()


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ask me about ecommerce sales, or ask me to generate and email a PDF sales report.",
        }
    ]


st.title("Ecommerce Sales Multi-Agent")
st.caption("Routes your request to a Supabase sales agent or email PDF report agent.")

with st.sidebar:
    st.header("Controls")
    seed_rows = st.number_input("Fake sales rows", min_value=1, max_value=10000, value=500, step=50)
    if st.button("Generate sales data", use_container_width=True):
        with st.spinner("Generating and inserting fake sales rows into Supabase..."):
            inserted = seed_sales(int(seed_rows))
        st.success(f"Inserted {inserted} rows.")

    recipient = st.text_input("Optional report recipient", placeholder="someone@example.com")

    with st.expander("Email diagnostics"):
        st.json(settings_debug_summary())
        if st.button("Reload .env", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            reload_settings()
            st.success(".env reloaded.")
        try:
            st.json(email_debug_summary())
        except Exception as exc:
            st.warning(f"Email settings are not fully configured yet: {exc}")
        if st.button("Test email provider", use_container_width=True):
            try:
                sender = test_email_provider()
                st.success(f"Email provider configuration looks ready for {sender}")
            except Exception as exc:
                st.error(str(exc))

    st.divider()
    st.markdown("**Try asking**")
    st.code("What are my top products this month?")
    st.code("Summarize gross revenue and top regions.")
    st.code("Send a PDF sales report to my email.")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


prompt = st.chat_input("Ask a sales question or request a PDF report...")

if prompt:
    add_message("user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Routing your request..."):
            try:
                response = get_orchestrator().run(
                    AgentRequest(query=prompt, recipient=recipient or None)
                )
                st.markdown(response.answer)
                if response.data:
                    with st.expander("Sales summary data"):
                        st.json(response.data)
                if response.report_path:
                    report_path = Path(response.report_path)
                    if response.emailed_to:
                        st.success(f"Email sent to {response.emailed_to}")
                    st.download_button(
                        "Download PDF report",
                        data=report_path.read_bytes(),
                        file_name=report_path.name,
                        mime="application/pdf",
                    )
                add_message("assistant", response.answer)
            except Exception as exc:
                error = f"Request failed: {exc}"
                st.error(error)
                st.info(
                    "If the PDF was created but email failed, check RESEND_API_KEY, EMAIL_FROM, "
                    "and EMAIL_RECIPIENT in your environment variables."
                )
                add_message("assistant", error)
