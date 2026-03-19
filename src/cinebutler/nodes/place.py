"""Execute mv or cp to the LLM-determined destination."""

import logging
from pathlib import Path

from cinebutler.config import load_config
from cinebutler.models import CineButlerState
from cinebutler.tools.filesystem import (
    copy_file_or_dir,
    ensure_dir,
    get_size_bytes,
    move_file_or_dir,
    select_target_with_space,
)

logger = logging.getLogger(__name__)


def _find_duplicates(src: Path, dest: Path) -> list[str]:
    """Return list of filenames that already exist at destination."""
    duplicates = []
    if src.is_dir():
        for child in src.iterdir():
            if child.is_file() and (dest / child.name).exists():
                duplicates.append(child.name)
    else:
        if dest.exists() and dest.is_file():
            duplicates.append(dest.name)
    return duplicates


def place_node(state: CineButlerState) -> dict:
    """Move or copy torrent to the destination decided by name_node."""
    config = load_config()
    media_type = state.get("media_type", "unknown")
    torrent_path = state.get("torrent_path", "")
    dest = state.get("dest", "")

    # Read action from config (mv | cp | skip)
    action = getattr(config.actions, media_type, "skip")

    if not dest:
        return {"status": "failed", "message": "No destination path from name node"}

    src = Path(torrent_path)
    if not src.exists():
        return {"status": "failed", "message": f"Source does not exist: {torrent_path}"}

    dest_path = Path(dest)

    # Duplicate detection
    duplicates = _find_duplicates(src, dest_path if src.is_dir() else dest_path)
    if duplicates:
        on_dup = config.actions.on_duplicate
        dup_list = ", ".join(duplicates)
        if on_dup == "skip":
            logger.warning("duplicate files found, skipping: %s", dup_list)
            return {
                "status": "duplicate",
                "message": f"Duplicate files already exist: {dup_list}",
                "final_path": dest,
                "target_dir": str(dest_path.parent),
            }
        else:
            logger.info("duplicate files found, overwriting: %s", dup_list)

    # Disk space check
    try:
        size = get_size_bytes(torrent_path)
    except OSError:
        size = 0

    targets = (
        config.targets.movie if media_type == "movie" else config.targets.tv
    )
    if targets and not select_target_with_space(targets, size):
        return {
            "status": "failed",
            "message": f"No target directory has enough space (need ~{size / (1024**3):.1f} GB)",
            "target_dir": targets[0] if targets else "",
        }

    try:
        ensure_dir(dest_path.parent if not src.is_dir() else dest_path)
        if src.is_dir() and dest_path.exists() and dest_path.is_dir():
            # Destination directory exists: move/copy contents of src into it
            for child in src.iterdir():
                child_dest = dest_path / child.name
                if action == "mv":
                    move_file_or_dir(child, child_dest)
                else:
                    copy_file_or_dir(child, child_dest)
        else:
            if action == "mv":
                move_file_or_dir(src, dest_path)
            else:
                copy_file_or_dir(src, dest_path)
    except Exception as e:
        return {"status": "failed", "message": str(e), "target_dir": str(dest_path.parent)}

    op_verb = "Moved" if action == "mv" else "Copied"
    logger.info("%s %s -> %s", op_verb, torrent_path, dest)
    return {
        "status": "success",
        "message": f"{op_verb} successfully",
        "target_dir": str(dest_path.parent),
        "final_path": dest,
    }
