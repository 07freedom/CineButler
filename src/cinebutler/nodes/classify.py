"""Classify media via LLM + TMDB tools.

Replaces the old parse + identify nodes. Responsibilities:
- Detect is_directory from filesystem
- Use LLM + TMDB tools to identify media_type, tmdb_id, title, year, season, episodes
- Fetch all known titles from TMDB for use in the match step
- Determine action (mv/cp/skip) from config
"""

import json
import logging
import re
from pathlib import Path

from langchain_core.messages import HumanMessage, ToolMessage

from cinebutler.config import load_config
from cinebutler.llm import get_llm_with_fallback
from cinebutler.models import CineButlerState
from cinebutler.tools.tmdb import get_tv_titles, make_tmdb_tools

logger = logging.getLogger("cinebutler.classify")

_VIDEO_EXTS = {
    ".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".ts",
    ".m2ts", ".rmvb", ".webm", ".iso",
}

CLASSIFY_PROMPT = """\
You are a media identification assistant. Given a torrent name, identify the content \
using TMDB search tools.

Torrent name: {torrent_name}

Classification rules:
- movie: a single complete film
- tv: has season/episode structure (S01E01, Season 1, etc.) or is a TV series
- adult: adult/pornographic content — do NOT search TMDB, return immediately
- unknown: cannot be confidently matched in TMDB

Instructions:
1. Determine if this looks like adult content first. If yes, return immediately.
2. Otherwise, use TMDB tools to search and confirm the title.
3. For TV, identify the season number and episode numbers if present.
4. Return ONLY a JSON object (no markdown, no explanation):

{{"media_type": "movie|tv|adult|unknown", "tmdb_id": <int or null>, \
"title": "<official title from TMDB>", "year": <int or null>, \
"season": <int or null>, "episodes": [<list of ints>]}}
"""

MAX_TOOL_ROUNDS = 6


def _parse_json(text: str) -> dict | None:
    """Extract the first JSON object from LLM text output."""
    m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def _is_directory(torrent_path: str) -> bool:
    """Determine if torrent is a directory (folder download)."""
    p = Path(torrent_path)
    if p.exists():
        return p.is_dir()
    # Heuristic: no known video extension → likely a directory
    return p.suffix.lower() not in _VIDEO_EXTS


def _run_llm_with_tools(torrent_name: str, tools: list, llm) -> dict | None:
    """Run LLM tool loop. Returns parsed dict or None on failure."""
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}

    prompt = CLASSIFY_PROMPT.format(torrent_name=torrent_name)
    logger.info("classify prompt:\n%s", prompt)
    messages = [HumanMessage(content=prompt)]

    for round_num in range(MAX_TOOL_ROUNDS + 1):
        try:
            resp = llm_with_tools.invoke(messages)
        except Exception as e:
            logger.error("LLM invoke failed (round=%d): %s", round_num, e)
            return None

        if not resp.tool_calls:
            text = resp.content if isinstance(resp.content, str) else ""
            logger.info("LLM final response (round=%d): %.800s", round_num, text)
            return _parse_json(text)

        if round_num >= MAX_TOOL_ROUNDS:
            logger.warning("exceeded %d tool rounds, stopping", MAX_TOOL_ROUNDS)
            return None

        messages.append(resp)
        for tc in resp.tool_calls:
            fn = tc["name"]
            args = tc.get("args", {}) or {}
            logger.info("tool call (round=%d): %s(%s)", round_num + 1, fn, args)
            if fn not in tool_map:
                logger.warning("unknown tool: %s", fn)
                result = f"Error: unknown tool {fn}"
            else:
                try:
                    result = tool_map[fn].invoke(args)
                except Exception as e:
                    logger.error("tool %s error: %s", fn, e)
                    result = f"Error: {e}"
            logger.info("tool result (%s): %.500s", fn, str(result))
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return None


def classify_node(state: CineButlerState) -> dict:
    """Classify media type and determine action."""
    config = load_config()

    torrent_name = state.get("torrent_name", "")
    torrent_dir = state.get("torrent_dir", "")
    torrent_path = state.get("torrent_path") or str(Path(torrent_dir) / torrent_name)

    is_dir = _is_directory(torrent_path)

    # No TMDB key → return unknown
    api_key = config.tmdb.api_key
    if not api_key:
        logger.warning("TMDB API key not configured")
        action = config.actions.unknown
        return {
            "torrent_path": torrent_path,
            "is_directory": is_dir,
            "media_type": "unknown",
            "tmdb_id": None,
            "title": torrent_name,
            "year": None,
            "season": None,
            "episodes": [],
            "all_titles": [],
            "action": action,
            "message": "TMDB API key not configured",
        }

    tools = make_tmdb_tools(api_key, config.tmdb.language, config.tmdb.base_url)
    llm = get_llm_with_fallback()

    parsed = _run_llm_with_tools(torrent_name, tools, llm)

    if not parsed:
        logger.warning("LLM classification failed, returning unknown")
        action = config.actions.unknown
        return {
            "torrent_path": torrent_path,
            "is_directory": is_dir,
            "media_type": "unknown",
            "tmdb_id": None,
            "title": torrent_name,
            "year": None,
            "season": None,
            "episodes": [],
            "all_titles": [],
            "action": action,
            "message": "LLM response could not be parsed",
        }

    media_type = parsed.get("media_type", "unknown")
    tmdb_id = parsed.get("tmdb_id")
    title = parsed.get("title") or torrent_name
    year = parsed.get("year")
    season = parsed.get("season")
    episodes = parsed.get("episodes") or []

    # Fetch all known titles for the match step
    all_titles: list[str] = []
    if media_type == "tv" and tmdb_id:
        try:
            all_titles = get_tv_titles(api_key, tmdb_id, config.tmdb.base_url)
            logger.info("fetched %d known titles for tmdb_id=%s", len(all_titles), tmdb_id)
        except Exception as e:
            logger.warning("get_tv_titles failed: %s", e)
            all_titles = [title]
    elif media_type == "movie":
        # For movies, use title + "title (year)" as search candidates
        all_titles = [title]
        if year:
            all_titles.append(f"{title} ({year})")

    # Determine action from config
    action = getattr(config.actions, media_type, "skip")
    logger.info("classify result: media_type=%s tmdb_id=%s title=%r action=%s",
                media_type, tmdb_id, title, action)

    return {
        "torrent_path": torrent_path,
        "is_directory": is_dir,
        "media_type": media_type,
        "tmdb_id": tmdb_id,
        "title": title,
        "year": year,
        "season": season,
        "episodes": episodes,
        "all_titles": all_titles,
        "action": action,
    }
