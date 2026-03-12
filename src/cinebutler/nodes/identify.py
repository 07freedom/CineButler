"""Identify media via LLM + TMDB tools."""

import json
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from cinebutler.config import load_config
from cinebutler.llm import get_llm_with_fallback
from cinebutler.models import CineButlerState
from cinebutler.prompts import IDENTIFY_PROMPT
from cinebutler.tools.tmdb import make_tmdb_tools

logger = logging.getLogger("cinebutler.identify")


def _parse_llm_json(text: str) -> dict | None:
    """Extract JSON from LLM response."""
    # Try to find {...} block
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def identify_node(state: CineButlerState) -> dict:
    """Use LLM + TMDB to identify the media."""
    config = load_config()
    api_key = config.tmdb.api_key
    if not api_key:
        logger.warning("TMDB API key not configured")
        return {
            "media_type": "unknown",
            "tmdb_id": None,
            "title": state.get("title", "Unknown"),
            "year": state.get("year"),
            "season": state.get("season"),
            "episodes": state.get("episodes", []),
            "message": "TMDB API key not configured",
        }

    tools = make_tmdb_tools(api_key, config.tmdb.language, config.tmdb.base_url)
    llm = get_llm_with_fallback()
    llm_with_tools = llm.bind_tools(tools)

    episodes = state.get("episodes", [])
    prompt = IDENTIFY_PROMPT.format(
        torrent_name=state.get("torrent_name", ""),
        title=state.get("title", ""),
        year=state.get("year") or "",
        season=state.get("season") or "",
        episodes=episodes,
    )
    logger.info("LLM prompt:\n%s", prompt)
    messages = [HumanMessage(content=prompt)]
    MAX_TOOL_ROUNDS = 6
    tool_rounds = 0
    while tool_rounds <= MAX_TOOL_ROUNDS:
        try:
            resp = llm_with_tools.invoke(messages)
        except Exception as e:
            logger.error("LLM invoke failed (tool_rounds=%d): %s", tool_rounds, e)
            break
        if resp.tool_calls:
            tool_rounds += 1
            if tool_rounds > MAX_TOOL_ROUNDS:
                logger.warning("exceeded %d tool rounds, stopping", MAX_TOOL_ROUNDS)
                break
            for tc in resp.tool_calls:
                fn = tc["name"]
                args = tc.get("args", {}) or {}
                logger.info("round %d tool_call: %s(%s)", tool_rounds, fn, args)
                tool_map = {t.name: t for t in tools}
                if fn not in tool_map:
                    logger.warning("round %d unknown tool: %s", tool_rounds, fn)
                    continue
                try:
                    result = tool_map[fn].invoke(args)
                except Exception as e:
                    logger.error("round %d tool %s error: %s", tool_rounds, fn, e)
                    result = f"Error: {e}"
                logger.info("round %d tool_result(%s): %.500s", tool_rounds, fn, str(result))
                messages.append(resp)
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )
            continue
        # No tool calls - parse final response
        text = resp.content if isinstance(resp.content, str) else ""
        logger.info("LLM final text (after %d tool rounds): %.800s", tool_rounds, text)
        parsed = _parse_llm_json(text)
        if parsed:
            logger.info("parsed JSON: %s", parsed)
            media_type = parsed.get("media_type", "unknown")
            tmdb_id = parsed.get("tmdb_id")
            title = parsed.get("title") or state.get("title", "Unknown")
            year = parsed.get("year") or state.get("year")
            season = parsed.get("season") or state.get("season")
            episodes = parsed.get("episodes") or state.get("episodes", [])
            result = {
                "media_type": media_type,
                "tmdb_id": tmdb_id,
                "title": title,
                "year": year,
                "season": season,
                "episodes": episodes,
            }
            logger.info("identify result: %s", result)
            return result
        logger.warning("JSON parse failed, raw text: %.500s", text)
        break

    logger.warning("identify gave up after %d tool rounds, returning unknown", tool_rounds)
    return {
        "media_type": "unknown",
        "tmdb_id": None,
        "title": state.get("title", "Unknown"),
        "year": state.get("year"),
        "season": state.get("season"),
        "episodes": state.get("episodes", []),
        "message": "LLM response could not be parsed",
    }
