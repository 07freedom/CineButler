"""Data models and workflow state for CineButler."""

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

    # Classified media info (from classify node)
    media_type: str       # movie | tv | adult | unknown
    tmdb_id: int | None
    title: str
    year: int | None
    season: int | None
    episodes: list[int]
    all_titles: list[str]  # all known titles from TMDB (for match search)

    # Action determined from config after classification
    action: str            # mv | cp | skip

    # Match result (from match node)
    existing_path: str | None  # found existing media folder, or None
    existing_listing: str | None  # directory listing of existing_path

    # Placement
    dest: str              # LLM-determined final destination path (full path)
    target_dir: str
    final_path: str

    # Status
    status: str            # success | failed | skipped
    message: str

    # LLM messages
    messages: Annotated[list, add_messages]
