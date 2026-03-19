"""Name node: determine the final destination path via LLM.

Focused single-purpose node — no directory scanning, no TMDB calls.
Context is built from state (already populated by classify + match nodes).
"""

import json
import logging
import re
from pathlib import Path

from langchain_core.messages import HumanMessage

from cinebutler.config import load_config
from cinebutler.llm import get_llm_with_fallback
from cinebutler.models import CineButlerState

logger = logging.getLogger("cinebutler.name")

_MAX_TORRENT_ENTRIES = 40  # max files to show for directory torrents

NAME_PROMPT = """\
You are a media file naming assistant. Determine the exact destination path for a download.

## Identified Media
{media_info}

## Download
Torrent filename: {torrent_name}
Type: {torrent_type}
{torrent_structure}
## Library
Target root directories: {target_dirs}
Existing folder: {existing_path}
{existing_listing_section}
## Naming Mode: {file_naming}

### raw — keep original filename
TV single file:   dest = /media/Series/Breaking Bad/Season 03/Breaking.Bad.S03E01.mkv
TV directory:     dest = /media/Series/Breaking Bad/Season 03
Movie single file: dest = /media/Movies/The Dark Knight/The Dark Knight.2008.1080p.mkv
Movie directory:  dest = /media/Movies/The Dark Knight (2008)

### infuse — Infuse/TMDB standard naming
TV single file:    dest = /media/Series/Breaking Bad/Season 03/Breaking Bad.S03E01 {{tmdb-1396}}.mkv
TV directory:      dest = /media/Series/Breaking Bad/Season 03
Movie single file: dest = /media/Movies/The Dark Knight (2008)/The Dark Knight (2008).mkv
Movie directory:   dest = /media/Movies/The Dark Knight (2008)

## Rules
{custom_rules}- dest MUST start with one of the target root directories listed above
- If an existing folder was found, place content inside it (do not create a duplicate)
- If the existing folder's contents are listed, use them to decide whether to place files
  directly in that folder or inside an appropriate subfolder (e.g. a season folder for TV)
- For directories: dest is the full path the directory will be moved/renamed to
- For single files: dest includes the filename with extension
- Preserve the extension from the original torrent filename when renaming
- Movie single files MUST be wrapped in a subfolder (e.g. /Movies/Title (Year)/Title (Year).ext)
  Never place a movie file directly inside the target root directory

Respond with ONLY a JSON object, no markdown:
{{"dest": "<full destination path>"}}
"""


def _build_torrent_structure(torrent_path: str, is_directory: bool) -> str:
    """Return a short text listing of the torrent's file structure."""
    if not is_directory:
        return ""
    p = Path(torrent_path)
    if not p.exists():
        return ""
    entries = sorted(p.rglob("*"))[:_MAX_TORRENT_ENTRIES]
    lines = ["Directory contents:"]
    for entry in entries:
        rel = entry.relative_to(p)
        prefix = "  [dir] " if entry.is_dir() else "  [file] "
        lines.append(f"{prefix}{rel}")
    total = sum(1 for _ in p.rglob("*"))
    if total > _MAX_TORRENT_ENTRIES:
        lines.append(f"  ... ({_MAX_TORRENT_ENTRIES} of {total} shown)")
    return "\n".join(lines) + "\n"


def _parse_dest(text: str) -> str | None:
    """Extract dest value from LLM JSON response."""
    m = re.search(r'\{[^{}]*"dest"\s*:\s*"([^"]+)"[^{}]*\}', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def name_node(state: CineButlerState) -> dict:
    """Ask LLM to generate the final destination path."""
    config = load_config()
    media_type = state.get("media_type", "unknown")
    is_directory = state.get("is_directory", False)
    torrent_name = state.get("torrent_name", "")
    torrent_path = state.get("torrent_path", "")
    existing_path = state.get("existing_path")

    targets = (
        config.targets.movie if media_type == "movie" else config.targets.tv
    )
    if not targets:
        return {"status": "failed", "message": "No target directories configured"}

    media_info = json.dumps({
        "media_type": media_type,
        "title": state.get("title"),
        "year": state.get("year"),
        "tmdb_id": state.get("tmdb_id"),
        "season": state.get("season"),
        "episodes": state.get("episodes", []),
    }, ensure_ascii=False, indent=2)

    torrent_type = "directory (season pack or collection)" if is_directory else "single file"
    torrent_structure = _build_torrent_structure(torrent_path, is_directory)
    target_dirs = ", ".join(targets)
    existing_str = existing_path if existing_path else "none — create a new folder"
    existing_listing = state.get("existing_listing")
    existing_listing_section = ""
    if existing_listing:
        existing_listing_section = f"Contents of existing folder:\n{existing_listing}\n"

    # Build custom rules section (user-defined, higher priority)
    custom_rules = ""
    if config.naming_rules:
        lines = ["**User-defined rules (HIGHEST PRIORITY — override defaults when conflicting):**\n"]
        for rule in config.naming_rules:
            lines.append(f"- {rule}")
        custom_rules = "\n".join(lines) + "\n\n"

    prompt = NAME_PROMPT.format(
        media_info=media_info,
        torrent_name=torrent_name,
        torrent_type=torrent_type,
        torrent_structure=torrent_structure,
        target_dirs=target_dirs,
        existing_path=existing_str,
        existing_listing_section=existing_listing_section,
        file_naming=config.file_naming,
        custom_rules=custom_rules,
    )
    logger.info("name prompt:\n%s", prompt)

    llm = get_llm_with_fallback()
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
    except Exception as e:
        return {"status": "failed", "message": f"LLM name failed: {e}"}

    text = resp.content if isinstance(resp.content, str) else ""
    logger.info("name response: %s", text)

    dest = _parse_dest(text)
    if not dest:
        return {"status": "failed", "message": f"Could not parse dest from LLM: {text[:300]}"}

    # Warn if dest is not under any configured target
    dest_resolved = Path(dest).resolve()
    resolved_targets = [Path(t).expanduser().resolve() for t in targets]
    if not any(dest_resolved == t or t in dest_resolved.parents for t in resolved_targets):
        logger.warning("LLM dest %s is not under any configured target", dest)

    logger.info("name dest: %s", dest)
    return {"dest": dest}
