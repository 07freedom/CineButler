"""LLM provider with priority fallback (DeepSeek -> OpenRouter)."""

import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def _project_root():
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent.parent
    return p if (p / "config.yaml").exists() else Path.cwd()


def _get_providers() -> list[dict[str, Any]]:
    """Parse LLM_PROVIDERS from env (JSON array)."""
    load_dotenv(_project_root() / ".env", override=False)
    raw = os.getenv("LLM_PROVIDERS", "[]")
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def get_llm_with_fallback(
    *,
    temperature: float = 0,
    max_retries: int = 2,
) -> ChatOpenAI:
    """Return first working LLM from configured providers."""
    providers = _get_providers()
    last_error: Exception | None = None

    for prov in providers:
        if not isinstance(prov, dict):
            continue
        base_url = prov.get("base_url", "")
        api_key = prov.get("api_key", "")
        model = prov.get("model", "gpt-4")
        name = prov.get("name", "unknown")
        if not base_url or not api_key:
            continue
        try:
            llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key,
                model=model,
                temperature=temperature,
                max_retries=max_retries,
            )
            return llm
        except Exception as e:
            last_error = e
            continue

    msg = "No LLM provider available"
    if last_error:
        msg += f"; last error: {last_error}"
    raise RuntimeError(msg)
