"""LLM provider configuration."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def _project_root():
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent.parent
    return p if (p / "config.yaml").exists() else Path.cwd()


def get_llm_with_fallback(
    *,
    temperature: float = 0,
    max_retries: int = 2,
) -> ChatOpenAI:
    """Return LLM from configured provider."""
    load_dotenv(_project_root() / ".env", override=False)
    base_url = os.getenv("LLM_BASE_URL", "")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "deepseek-chat")

    if not base_url or not api_key:
        raise RuntimeError("LLM_BASE_URL and LLM_API_KEY must be set in .env")

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_retries=max_retries,
    )
