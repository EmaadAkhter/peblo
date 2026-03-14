"""Application settings loaded from environment variables."""

import itertools
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Reads configuration from .env file."""

    groq_api_keys: str = ""
    mongodb_uri: str = ""
    database_name: str = "peblo"
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def groq_keys_list(self) -> list[str]:
        """Parse comma-separated Groq API keys."""
        return [k.strip() for k in self.groq_api_keys.split(",") if k.strip()]

    def get_groq_key_cycle(self) -> itertools.cycle:
        """Return an infinite round-robin cycle over Groq API keys."""
        keys = self.groq_keys_list
        if not keys:
            raise ValueError("No Groq API keys configured. Set GROQ_API_KEYS in .env")
        return itertools.cycle(keys)


settings = Settings()

# Global key rotator — call next(groq_key_rotator) to get the next key
groq_key_rotator = settings.get_groq_key_cycle()
