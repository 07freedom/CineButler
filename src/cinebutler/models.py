"""Data models and Workflow State for CineButler."""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class CineButlerState(TypedDict, total=False):
    """State carried through the LangGraph workflow."""

    # From Transmission
    torrent_name: str
    torrent_dir: str
    torrent_path: str
    torrent_size: int
    is_directory: bool

    # Identified media info
    media_type: str  # movie | tv | adult | unknown
    tmdb_id: int | None
    title: str
    year: int | None
    season: int | None
    episodes: list[int]

    # Placement
    target_dir: str
    new_name: str
    new_file_name: str | None
    new_season_folder: str | None
    final_path: str

    # Status
    status: str  # success | failed | skipped
    message: str

    # LLM messages
    messages: Annotated[list, add_messages]
