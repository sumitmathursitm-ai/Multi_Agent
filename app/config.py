from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"

def load_project_env() -> None:
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)


load_project_env()


class Settings(BaseSettings):
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_sales_table: str = Field(default="sales_orders", alias="SUPABASE_SALES_TABLE")

    openrouter_api_key: str = Field(alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4o-mini", alias="OPENROUTER_MODEL")
    openrouter_site_url: str = Field(default="http://localhost:8000", alias="OPENROUTER_SITE_URL")
    openrouter_app_name: str = Field(default="Ecom Sales Agent", alias="OPENROUTER_APP_NAME")

    gmail_sender: str = Field(alias="GMAIL_SENDER")
    gmail_app_password: str = Field(alias="GMAIL_APP_PASSWORD")
    gmail_recipient: str = Field(alias="GMAIL_RECIPIENT")
    gmail_smtp_host: str = Field(default="smtp.gmail.com", alias="GMAIL_SMTP_HOST")
    gmail_smtp_port: int = Field(default=465, alias="GMAIL_SMTP_PORT")

    report_output_dir: Path = Field(default=Path("reports"), alias="REPORT_OUTPUT_DIR")
    seed_default_rows: int = Field(default=250, alias="SEED_DEFAULT_ROWS")

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")


def get_settings() -> Settings:
    load_project_env()
    env_file = ENV_PATH if ENV_PATH.exists() else None
    return Settings(_env_file=env_file)


def reload_settings() -> Settings:
    return get_settings()


def settings_debug_summary() -> dict[str, str | bool]:
    return {
        "project_root": str(PROJECT_ROOT),
        "env_path": str(ENV_PATH),
        "env_exists": ENV_PATH.exists(),
        "env_example_path": str(ENV_EXAMPLE_PATH),
        "env_example_exists": ENV_EXAMPLE_PATH.exists(),
        "runtime_env_source": ".env file + process environment" if ENV_PATH.exists() else "process environment",
    }
