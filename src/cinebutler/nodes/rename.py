"""Generate Infuse-compliant names for movies and TV."""

import re
from pathlib import Path

from cinebutler.models import CineButlerState


def _sanitize(s: str) -> str:
    """Replace invalid filesystem chars with spaces."""
    return re.sub(r'[<>:"/\\|?*]', " ", s).strip()


def _safe_title(title: str) -> str:
    """Safe title for filename."""
    return _sanitize(title) or "Unknown"


def rename_node(state: CineButlerState) -> dict:
    """Generate Infuse-compliant folder and file names."""
    media_type = state.get("media_type", "unknown")
    title = _safe_title(state.get("title", "Unknown"))
    year = state.get("year")
    season = state.get("season")
    episodes = state.get("episodes", [])
    tmdb_id = state.get("tmdb_id")
    is_directory = state.get("is_directory", False)
    torrent_name = state.get("torrent_name", "")
    torrent_path = state.get("torrent_path", "")

    year_suffix = f" ({year})" if year else ""
    base_name = f"{title}{year_suffix}"
    tmdb_suffix = f" {{tmdb-{tmdb_id}}}" if tmdb_id else ""

    new_season_folder: str | None = None
    if media_type == "movie":
        if is_directory:
            new_name = base_name
            new_file_name = None  # Keep inner structure
        else:
            ext = Path(torrent_name).suffix or ".mkv"
            new_name = base_name
            new_file_name = f"{base_name}{tmdb_suffix}{ext}".strip()
    elif media_type == "tv":
        if is_directory:
            new_name = base_name
            new_file_name = None
            new_season_folder = None
        else:
            season_num = season or 1
            season_str = f"S{season_num:02d}"
            ep_str = f"E{episodes[0]:02d}" if episodes else "E01"
            ext = Path(torrent_name).suffix or ".mkv"
            new_name = base_name
            new_season_folder = f"Season {season_num:02d}"
            new_file_name = f"{title}.{season_str}{ep_str}{tmdb_suffix}{ext}".strip()
    else:
        new_name = torrent_name
        new_file_name = None
        new_season_folder = None

    return {
        "new_name": new_name,
        "new_file_name": new_file_name,
        "new_season_folder": new_season_folder,
    }
