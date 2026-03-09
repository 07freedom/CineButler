"""Identify media via LLM + TMDB tools."""

import json
import re

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from cinebutler.config import load_config
from cinebutler.llm import get_llm_with_fallback
from cinebutler.models import CineButlerState
from cinebutler.tools.tmdb import make_tmdb_tools


IDENTIFY_PROMPT = """你是一个媒体识别助手。根据文件名和种子信息，判断这是电影、剧集、成人内容还是无法识别。

规则：
- 电影：单集完整影片
- 剧集：有季/集概念 (S01E01 等)
- 成人内容：色情、 porn 等 -> media_type 填 "adult"
- 无法从 TMDB 匹配到可信结果 -> media_type 填 "unknown"

请使用 TMDB 工具搜索并确认。搜索时用英文或原标题。

最终你必须用以下 JSON 格式回复（不要包含其他文字）：
{{"media_type":"movie"|"tv"|"adult"|"unknown","tmdb_id":数字或null,"title":"作品标题","year":数字或null,"season":数字或null,"episodes":[1,2]}}

文件名: {torrent_name}
解析出的标题线索: {title}
解析出的年份: {year}
解析出的季: {season}
解析出的集: {episodes}
"""


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
        return {
            "media_type": "unknown",
            "tmdb_id": None,
            "title": state.get("title", "Unknown"),
            "year": state.get("year"),
            "season": state.get("season"),
            "episodes": state.get("episodes", []),
            "message": "TMDB API key not configured",
        }

    tools = make_tmdb_tools(api_key, config.tmdb.language)
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
    messages = [HumanMessage(content=prompt)]
    MAX_TURNS = 5
    for _ in range(MAX_TURNS):
        resp = llm_with_tools.invoke(messages)
        if resp.tool_calls:
            for tc in resp.tool_calls:
                fn = tc["name"]
                args = tc.get("args", {}) or {}
                tool_map = {t.name: t for t in tools}
                if fn not in tool_map:
                    continue
                result = tool_map[fn].invoke(args)
                messages.append(resp)
                messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )
            continue
        # No tool calls - parse final response
        text = resp.content if isinstance(resp.content, str) else ""
        parsed = _parse_llm_json(text)
        if parsed:
            media_type = parsed.get("media_type", "unknown")
            tmdb_id = parsed.get("tmdb_id")
            title = parsed.get("title") or state.get("title", "Unknown")
            year = parsed.get("year") or state.get("year")
            season = parsed.get("season") or state.get("season")
            episodes = parsed.get("episodes") or state.get("episodes", [])
            return {
                "media_type": media_type,
                "tmdb_id": tmdb_id,
                "title": title,
                "year": year,
                "season": season,
                "episodes": episodes,
            }
        break

    return {
        "media_type": "unknown",
        "tmdb_id": None,
        "title": state.get("title", "Unknown"),
        "year": state.get("year"),
        "season": state.get("season"),
        "episodes": state.get("episodes", []),
        "message": "LLM response could not be parsed",
    }
