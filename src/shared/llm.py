from langchain_openai import ChatOpenAI

from src.shared.config import load_config


def build_llm() -> ChatOpenAI:
    cfg = load_config()
    return ChatOpenAI(
        model=cfg.default_llm_model,
        timeout=cfg.request_timeout_seconds,
        max_retries=cfg.max_retries,
        api_key=cfg.openai_api_key,
        temperature=0,
    )
