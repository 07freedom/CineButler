"""Match node: search for existing media folder using TMDB-provided titles.

Pure code, no LLM. Uses targeted search (no full directory listing).
"""

import logging
from pathlib import Path

from cinebutler.config import load_config
from cinebutler.models import CineButlerState
from cinebutler.tools.filesystem import search_existing_folder

logger = logging.getLogger("cinebutler.match")

_MAX_LISTING_ENTRIES = 50


def _list_directory(path: str) -> str | None:
    """List immediate children of a directory. Returns a text listing or None."""
    p = Path(path)
    if not p.is_dir():
        return None
    entries = sorted(p.iterdir(), key=lambda e: e.name)[:_MAX_LISTING_ENTRIES]
    if not entries:
        return None
    lines = []
    for entry in entries:
        prefix = "[dir]  " if entry.is_dir() else "[file] "
        lines.append(f"  {prefix}{entry.name}")
    total = sum(1 for _ in p.iterdir())
    if total > _MAX_LISTING_ENTRIES:
        lines.append(f"  ... ({_MAX_LISTING_ENTRIES} of {total} shown)")
    return "\n".join(lines)


def match_node(state: CineButlerState) -> dict:
    """Search for an existing folder matching the identified media title."""
    config = load_config()
    media_type = state.get("media_type", "unknown")

    targets = (
        config.targets.movie if media_type == "movie" else config.targets.tv
    )
    candidate_names: list[str] = state.get("all_titles") or []
    title = state.get("title", "")
    if title and title not in candidate_names:
        candidate_names = [title] + candidate_names

    existing = search_existing_folder(targets, candidate_names)
    existing_listing = None
    if existing:
        logger.info("found existing folder: %s", existing)
        existing_listing = _list_directory(existing)
        if existing_listing:
            logger.info("folder contents:\n%s", existing_listing)
    else:
        logger.info("no existing folder found for %r", title)

    return {"existing_path": existing, "existing_listing": existing_listing}
