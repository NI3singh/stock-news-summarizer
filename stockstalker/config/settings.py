"""StockStalker v2 — application settings (pydantic-settings).

Configuration is loaded from environment variables / the project-root ``.env``
file and validated once, at import time, via the module-level ``settings``
singleton. If a required API key is absent, importing this module fails fast
with a clear, actionable error.
"""
from pathlib import Path

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the project-root .env (this file is stockstalker/config/settings.py).
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

# Load it with override=True BEFORE Settings is built, so the .env values WIN over
# any stale shell/OS environment variable. A leftover GEMINI_API_KEY holding an
# "AQ.*" OAuth token (e.g. injected by a shell profile or gcloud) is the classic
# cause of Gemini "401 UNAUTHENTICATED / ACCESS_TOKEN_TYPE_UNSUPPORTED": by default
# pydantic-settings AND os.environ readers (the LLM client reads GEMINI_API_KEY
# directly) prefer the OS var over .env, so the wrong key gets used. Loading here
# also makes the key resolve no matter which directory the app is launched from.
# On a host with no .env file this is a harmless no-op — the platform's real
# environment variables are used.
load_dotenv(_ENV_PATH, override=True)


class Settings(BaseSettings):
    # Required secrets. Defaulted to "" (rather than left as bare required
    # fields) so the @model_validator below can emit a clear "which key + set it
    # in .env" message for BOTH missing and empty values — a truly-absent
    # required field would otherwise trip pydantic's generic "field required"
    # error before the validator runs.
    gemini_api_key: str = ""
    polygon_api_key: str = ""

    # Operational config (sensible defaults; overridable via env / .env).
    refresh_time: str = "08:00"
    timezone: str = "Asia/Kolkata"
    log_level: str = "INFO"
    db_path: str = "./stockstalker.db"
    # Postgres/Supabase connection string for deployment. When set, the DB layer
    # uses it (via SQLAlchemy + asyncpg) instead of the local SQLite file, e.g.:
    #   postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
    database_url: str | None = None
    # Comma-separated production frontend origin(s) allowed by CORS, e.g.
    #   https://stockstalker.onrender.com,https://stockstalker.vercel.app
    frontend_origin: str | None = None
    max_concurrent_tickers: int = 3
    # News sentiment engine: "llm" (Gemini; default) or "vader" (rule-based, no
    # network). With "llm", the NewsAgent automatically falls back to VADER when
    # the model is unreachable, so analysis still yields a sentiment score.
    sentiment_engine: str = "llm"

    # LLM client configuration (consumed by the stockstalker.llm factory; env-overridable).
    llm_provider: str = "google"
    deep_think_llm: str = "gemini-2.5-flash"
    quick_think_llm: str = "gemini-2.5-flash-lite"
    backend_url: str | None = None              # custom OpenAI-compatible endpoint; None = provider default
    google_thinking_level: str | None = None    # Gemini thinking level ("high"/"low"/...)
    openai_reasoning_effort: str | None = None  # OpenAI reasoning effort ("low"/"medium"/"high")
    anthropic_effort: str | None = None         # Anthropic extended-thinking effort
    temperature: float | None = None            # cross-provider; None = provider default

    # Telegram integration (Phase B) — OPTIONAL. Intentionally NO validator:
    # bot features are simply disabled when these are unset. gemini/polygon
    # remain required (validator below is unchanged).
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    # MCP server (Phase C) — host/port for the FastMCP server (optional).
    mcp_server_host: str = "127.0.0.1"
    mcp_server_port: int = 8765

    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _require_api_keys(self) -> "Settings":
        missing = []
        if not self.gemini_api_key.strip():
            missing.append("GEMINI_API_KEY")
        if not self.polygon_api_key.strip():
            missing.append("POLYGON_API_KEY")
        if missing:
            keys = ", ".join(missing)
            raise ValueError(
                f"Missing required API key(s): {keys}. "
                f"Set {keys} in your .env file at the project root "
                f"(copy .env.example to .env and fill in the value(s))."
            )
        return self

    @property
    def db_url(self) -> str:
        """SQLAlchemy async DB URL: Postgres (asyncpg) if DATABASE_URL is set, else local SQLite."""
        raw = (self.database_url or "").strip()
        if not raw:
            return f"sqlite+aiosqlite:///{self.db_path}"
        # Normalise the provider scheme to the async driver.
        for prefix in ("postgresql+asyncpg://", "postgresql://", "postgres://"):
            if raw.startswith(prefix):
                raw = "postgresql+asyncpg://" + raw[len(prefix):]
                break
        # asyncpg rejects libpq query params (sslmode / pgbouncer / ...); drop them —
        # SSL + statement caching are configured in the engine's connect_args.
        if "?" in raw:
            raw = raw.split("?", 1)[0]
        return raw


# Singleton — instantiating here validates configuration at import time (fail-fast).
settings = Settings()
