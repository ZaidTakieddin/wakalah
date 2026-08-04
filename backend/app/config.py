"""Runtime settings, loaded once from the environment.

Secrets live in `backend/.env` (git-ignored). Nothing in the codebase reads
os.environ directly — everything imports `settings` from here, so there is a
single place to see what the service needs to run.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """All configuration for the Wakalah backend."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Nokia Network as Code (via RapidAPI) --------------------------------
    rapidapi_key: str = Field(default="", alias="RAPIDAPI_KEY")
    nac_base_url: str = Field(
        default="https://network-as-code.p-eu.rapidapi.com", alias="NAC_BASE_URL"
    )
    nac_rapidapi_host: str = Field(
        default="network-as-code.nokia.rapidapi.com", alias="NAC_RAPIDAPI_HOST"
    )

    # --- Supabase (server-side only; the frontend never sees these) ----------
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")

    # --- Agent brains (Tooling-Guide approved, free tiers) -------------------
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )

    # --- Demo / operational behaviour ---------------------------------------
    nac_mode: str = Field(default="live", alias="NAC_MODE")
    """How NacClient talks to the network: 'live' | 'replay'.

    'replay' serves recorded responses so the demo survives a dead network or a
    rate-limited sandbox. Replayed evidence is always labelled as such — it is
    never presented as a live network response (docs/04 section 5).
    """

    nac_record: bool = Field(default=True, alias="NAC_RECORD")
    """When live, write every response into the replay cache. Rehearsals build
    the fallback data automatically."""

    nac_timeout_seconds: float = Field(default=20.0, alias="NAC_TIMEOUT_SECONDS")

    replay_dir: Path = Field(default=BACKEND_DIR / "replay_cache", alias="REPLAY_DIR")

    @property
    def nac_headers(self) -> dict[str, str]:
        """Headers every Nokia NaC request needs."""
        return {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.nac_rapidapi_host,
            "Content-Type": "application/json",
        }


@lru_cache
def get_settings() -> Settings:
    """Settings are read once per process and cached."""
    return Settings()


settings = get_settings()
