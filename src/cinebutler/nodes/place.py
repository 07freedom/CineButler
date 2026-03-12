"""Select target directory and perform mv or cp."""

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


def place_node(state: CineButlerState) -> dict:
    """Pick target dir (respecting space), then mv or cp per FILE_OP_MODE."""
    config = load_config()
    file_op_mode = config.file_op_mode  # "cp" or "mv"
    media_type = state.get("media_type", "unknown")
    torrent_path = state.get("torrent_path", "")
    new_name = state.get("new_name", "")
    new_file_name = state.get("new_file_name")
    new_season_folder = state.get("new_season_folder")
    is_directory = state.get("is_directory", False)

    if media_type == "adult":
        rule = config.placement_rules.adult
        if getattr(rule, "action", "skip") == "skip":
            return {"status": "skipped", "message": "Adult content skipped by rule"}
        targets = getattr(rule, "targets", []) or []
    elif media_type == "movie":
        rule = config.placement_rules.movie
        targets = rule.targets or []
    elif media_type == "tv":
        rule = config.placement_rules.tv
        targets = rule.targets or []
    else:
        return {"status": "failed", "message": f"Cannot place media_type={media_type}"}

    if not targets:
        return {"status": "failed", "message": "No target directories configured"}

    try:
        size = get_size_bytes(torrent_path) if torrent_path else 0
    except OSError:
        return {"status": "failed", "message": f"Cannot get size: {torrent_path}"}

    target_base = select_target_with_space(targets, size)
    if not target_base:
        return {
            "status": "failed",
            "message": f"None of the target directories have enough space (need ~{size / (1024**3):.1f} GB)",
            "target_dir": targets[0],
        }

    src = Path(torrent_path)
    if not src.exists():
        return {"status": "failed", "message": f"Source does not exist: {torrent_path}"}

    dest_dir = Path(target_base)
    try:
        if media_type == "movie" and not is_directory and new_file_name:
            # Single file movie: wrap in folder
            wrap_dir = ensure_dir(dest_dir / new_name)
            final_dest = wrap_dir / new_file_name
        elif media_type == "tv" and not is_directory and new_season_folder and new_file_name:
            # Single file TV: Show/Season XX/file
            season_dir = ensure_dir(dest_dir / new_name / new_season_folder)
            final_dest = season_dir / new_file_name
        else:
            # Directory: mv whole thing
            final_dest = dest_dir / new_name
        if file_op_mode == "mv":
            move_file_or_dir(src, final_dest)
        else:
            copy_file_or_dir(src, final_dest)
    except Exception as e:
        return {
            "status": "failed",
            "message": str(e),
            "target_dir": target_base,
        }

    op_verb = "Moved" if file_op_mode == "mv" else "Copied"
    return {
        "status": "success",
        "message": f"{op_verb} successfully",
        "target_dir": target_base,
        "final_path": str(final_dest),
    }
