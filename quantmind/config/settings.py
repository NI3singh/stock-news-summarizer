"""QuantMind v2 — application settings (pydantic-settings).

Configuration is loaded from environment variables / the project-root ``.env``
file and validated once, at import time, via the module-level ``settings``
singleton. If a required API key is absent, importing this module fails fast
with a clear, actionable error.
"""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    chroma_persist_path: str = "./quantmind_chroma"
    db_path: str = "./quantmind.db"
    max_concurrent_tickers: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
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


# Singleton — instantiating here validates configuration at import time (fail-fast).
settings = Settings()
