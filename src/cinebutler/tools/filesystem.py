"""Filesystem tools: mv/cp, disk space, folder creation."""

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
    Pick target directory with enough space.
    When multiple have space: prefer the one with LEAST free space (per plan).
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
    # Sort by free space ascending - pick the one with least free (but still enough)
    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]


def get_size_bytes(path: str | Path) -> int:
    """Get total size of file or directory in bytes."""
    p = Path(path)
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
