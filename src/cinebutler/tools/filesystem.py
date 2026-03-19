"""Filesystem tools: mv/cp, disk space, folder creation, targeted search."""

import re
import shutil
import subprocess
from pathlib import Path


def get_disk_free_bytes(path: str | Path) -> int:
    """Get free space in bytes for the filesystem containing path."""
    stat = shutil.disk_usage(Path(path).resolve())
    return stat.free


def ensure_dir(path: str | Path) -> Path:
    """Create directory if not exists. Return Path."""
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def move_file_or_dir(src: str | Path, dst: str | Path) -> None:
    """Move file or directory using mv command."""
    src_p = Path(src).resolve()
    dst_p = Path(dst).resolve()
    if not src_p.exists():
        raise FileNotFoundError(f"Source does not exist: {src_p}")
    subprocess.run(
        ["mv", "--", str(src_p), str(dst_p)],
        check=True,
        capture_output=True,
    )


def copy_file_or_dir(src: str | Path, dst: str | Path) -> None:
    """Copy file or directory to dst. Directory uses copytree; file uses copy2."""
    src_p = Path(src).resolve()
    dst_p = Path(dst).resolve()
    if not src_p.exists():
        raise FileNotFoundError(f"Source does not exist: {src_p}")
    if src_p.is_dir():
        shutil.copytree(src_p, dst_p)
    else:
        shutil.copy2(src_p, dst_p)


def select_target_with_space(
    targets: list[str],
    required_bytes: int,
) -> str | None:
    """
    Pick target directory with enough free space.
    When multiple qualify: prefer the one with LEAST free space (balanced usage).
    Returns the chosen path or None if none have enough space.
    """
    candidates: list[tuple[str, int]] = []
    for t in targets:
        p = Path(t).expanduser().resolve()
        if not p.exists():
            continue
        free = get_disk_free_bytes(p)
        if free >= required_bytes:
            candidates.append((str(p), free))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]


def search_existing_folder(targets: list[str], candidate_names: list[str]) -> str | None:
    """
    Search for an existing media folder matching any of the candidate names.

    Only checks for specific names — does NOT list full directory contents,
    so the LLM never sees unrelated entries on disk.

    Matching strategy per target directory:
    1. Exact match: target/name
    2. Substring match: any folder whose name contains the candidate (case-insensitive)

    Returns the matched folder path (absolute), or None.
    """
    for target in targets:
        base = Path(target).expanduser().resolve()
        if not base.is_dir():
            continue
        for name in candidate_names:
            name = name.strip()
            if not name:
                continue
            # Exact match
            exact = base / name
            if exact.is_dir():
                return str(exact)
            # Case-insensitive substring match
            name_lower = name.lower()
            for entry in base.iterdir():
                if entry.is_dir() and name_lower in entry.name.lower():
                    return str(entry)
    return None


_CN_ORDINALS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def _extract_season_number(folder_name: str) -> int | None:
    """Extract season number from folder name. Supports S01/Season 2/第二季 formats."""
    m = re.search(r"[Ss]eason\s*(\d{1,2})", folder_name, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"[Ss](\d{1,2})\b", folder_name)
    if m:
        return int(m.group(1))
    m = re.search(r"第(\d{1,2})季", folder_name)
    if m:
        return int(m.group(1))
    m = re.search(r"第([一二三四五六七八九十]+)季", folder_name)
    if m and m.group(1) in _CN_ORDINALS:
        return _CN_ORDINALS[m.group(1)]
    return None


def find_existing_season_folder(show_dir: str | Path, season_num: int) -> str | None:
    """
    Find an existing season folder inside a show directory by season number.
    Returns the folder name (not full path), or None.
    """
    p = Path(show_dir).expanduser().resolve()
    if not p.exists():
        return None
    for subdir in p.iterdir():
        if subdir.is_dir() and _extract_season_number(subdir.name) == season_num:
            return subdir.name
    return None


def get_size_bytes(path: str | Path) -> int:
    """Get total size of file or directory in bytes."""
    p = Path(path)
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
