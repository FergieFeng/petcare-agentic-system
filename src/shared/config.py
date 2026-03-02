import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    default_llm_provider: str
    default_llm_model: str
    request_timeout_seconds: int
    max_retries: int
    openai_api_key: str


def load_config() -> AppConfig:
    load_dotenv()

    provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("DEFAULT_LLM_MODEL", "gpt-4.1-mini").strip()
    timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))
    max_retries = int(os.getenv("MAX_RETRIES", "2"))
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if provider != "openai":
        raise ValueError(
            "Only DEFAULT_LLM_PROVIDER=openai is currently supported in this starter app."
        )
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is required in .env for this starter app.")

    return AppConfig(
        default_llm_provider=provider,
        default_llm_model=model,
        request_timeout_seconds=timeout,
        max_retries=max_retries,
        openai_api_key=openai_api_key,
    )
