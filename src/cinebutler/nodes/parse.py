"""Parse torrent filename to extract candidate title, year, SXXEXX pattern."""

import re
from pathlib import Path

from cinebutler.models import CineButlerState


# S01E01, S1E1, 1x01, s01e01, etc.
EPISODE_PATTERN = re.compile(
    r"[Ss](\d{1,3})[Ee](\d{1,3})|[Ss]eason\s*(\d{1,3})\s*[Ee]pisode\s*(\d{1,3})|(\d{1,2})[xX](\d{1,3})",
    re.IGNORECASE,
)
# Year in parentheses: (1994), (2024)
YEAR_PATTERN = re.compile(r"\((\d{4})\)")
# Common separators and junk to strip
JUNK = re.compile(r"[.\[\]()\-_\s]+")


def _extract_episodes(text: str) -> tuple[int | None, list[int]]:
    """Extract season and episode numbers. Returns (season, [ep1, ep2, ...])."""
    season: int | None = None
    episodes: list[int] = []
    for m in EPISODE_PATTERN.finditer(text):
        g = m.groups()
        if g[0] is not None and g[1] is not None:
            s, e = int(g[0]), int(g[1])
        elif g[2] is not None and g[3] is not None:
            s, e = int(g[2]), int(g[3])
        elif g[4] is not None and g[5] is not None:
            s, e = int(g[4]), int(g[5])
        else:
            continue
        if season is None:
            season = s
        elif season != s:
            continue
        if e not in episodes:
            episodes.append(e)
    if episodes:
        episodes.sort()
    return (season, episodes)


def _extract_year(text: str) -> int | None:
    """Extract year from (YYYY) pattern."""
    m = YEAR_PATTERN.search(text)
    return int(m.group(1)) if m else None


def _guess_title(text: str, year: int | None, season: int | None) -> str:
    """Guess title by stripping known patterns and junk."""
    s = text
    # Remove S01E01-style
    s = EPISODE_PATTERN.sub(" ", s)
    # Remove (YYYY)
    if year:
        s = s.replace(f"({year})", " ")
    s = JUNK.sub(" ", s)
    s = " ".join(s.split()).strip()
    return s[:200] if s else "Unknown"


def parse_node(state: CineButlerState) -> dict:
    """Parse torrent name and path, populate initial identification hints."""
    name = state.get("torrent_name", "")
    path_str = state.get("torrent_path", "")
    torrent_dir = state.get("torrent_dir", "")
    torrent_size = state.get("torrent_size", 0)
    if not path_str and torrent_dir and name:
        path_str = f"{torrent_dir.rstrip('/')}/{name}"

    is_directory = False
    if path_str:
        p = Path(path_str)
        if p.exists():
            is_directory = p.is_dir()
        else:
            # Infer: video extension -> file; else folder
            video_ext = {".mkv", ".mp4", ".avi", ".mov", ".webm", ".m4v", ".wmv"}
            is_directory = p.suffix.lower() not in video_ext and "/" not in name

    year = _extract_year(name)
    season, episodes = _extract_episodes(name)
    title_hint = _guess_title(name, year, season)

    return {
        "torrent_name": name,
        "torrent_path": path_str,
        "torrent_size": torrent_size,
        "is_directory": is_directory,
        "title": title_hint,
        "year": year,
        "season": season,
        "episodes": episodes,
    }
