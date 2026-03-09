"""LangGraph workflow for CineButler media organization."""

from typing import Literal

from langgraph.graph import END, StateGraph

from cinebutler.config import load_config
from cinebutler.models import CineButlerState
from cinebutler.nodes.identify import identify_node
from cinebutler.nodes.notify import notify_node
from cinebutler.nodes.place import place_node
from cinebutler.nodes.rename import rename_node
from cinebutler.nodes.parse import parse_node


def _skip_node(state: CineButlerState) -> dict:
    """Set status=skipped for adult content."""
    return {"status": "skipped", "message": "Adult content skipped by rule"}


def _route_after_identify(state: CineButlerState) -> Literal["skip", "rename"]:
    """Route: adult+skip -> skip; else -> rename."""
    config = load_config()
    media_type = state.get("media_type", "")
    if media_type == "adult" and config.placement_rules.adult.action == "skip":
        return "skip"
    return "rename"


def _route_after_place(state: CineButlerState) -> Literal["notify"]:
    """Always go to notify after place."""
    return "notify"


def create_workflow() -> StateGraph:
    """Build and compile the CineButler workflow."""
    graph = StateGraph(CineButlerState)

    graph.add_node("parse", parse_node)
    graph.add_node("identify", identify_node)
    graph.add_node("skip", _skip_node)
    graph.add_node("rename", rename_node)
    graph.add_node("place", place_node)
    graph.add_node("notify", notify_node)

    graph.set_entry_point("parse")
    graph.add_edge("parse", "identify")
    graph.add_conditional_edges("identify", _route_after_identify)
    graph.add_edge("skip", "notify")
    graph.add_edge("rename", "place")
    graph.add_edge("place", "notify")
    graph.add_edge("notify", END)

    return graph.compile()


def run_workflow(
    torrent_name: str,
    torrent_dir: str,
    torrent_bytes: int = 0,
) -> dict:
    """Run workflow with Transmission env vars. Returns final state."""
    if not torrent_dir.endswith("/"):
        torrent_dir = f"{torrent_dir}/"
    torrent_path = f"{torrent_dir}{torrent_name}"

    initial: CineButlerState = {
        "torrent_name": torrent_name,
        "torrent_dir": torrent_dir,
        "torrent_path": torrent_path,
        "torrent_size": torrent_bytes,
    }

    app = create_workflow()
    final = app.invoke(initial)
    return dict(final)
