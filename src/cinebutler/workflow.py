"""LangGraph workflow for CineButler media organization."""

from typing import Literal

from langgraph.graph import END, StateGraph

from cinebutler.models import CineButlerState
from cinebutler.nodes.classify import classify_node
from cinebutler.nodes.match import match_node
from cinebutler.nodes.name import name_node
from cinebutler.nodes.notify import notify_node
from cinebutler.nodes.place import place_node


def _skip_node(state: CineButlerState) -> dict:
    """Mark content as skipped (adult or unknown with skip action)."""
    return {"status": "skipped", "message": f"Skipped: action=skip for media_type={state.get('media_type')}"}


def _route_after_classify(state: CineButlerState) -> Literal["skip", "match"]:
    """Route based on action determined in classify node."""
    action = state.get("action", "skip")
    return "skip" if action == "skip" else "match"


def create_workflow() -> StateGraph:
    """Build and compile the CineButler workflow."""
    graph = StateGraph(CineButlerState)

    graph.add_node("classify", classify_node)
    graph.add_node("skip", _skip_node)
    graph.add_node("match", match_node)
    graph.add_node("name", name_node)
    graph.add_node("place", place_node)
    graph.add_node("notify", notify_node)

    graph.set_entry_point("classify")
    graph.add_conditional_edges("classify", _route_after_classify)
    graph.add_edge("skip", "notify")
    graph.add_edge("match", "name")
    graph.add_edge("name", "place")
    graph.add_edge("place", "notify")
    graph.add_edge("notify", END)

    return graph.compile()


def run_workflow(
    torrent_name: str,
    torrent_dir: str,
    torrent_bytes: int = 0,
) -> dict:
    """Run the CineButler workflow. Returns final state."""
    if not torrent_dir.endswith("/"):
        torrent_dir = f"{torrent_dir}/"

    initial: CineButlerState = {
        "torrent_name": torrent_name,
        "torrent_dir": torrent_dir,
        "torrent_path": f"{torrent_dir}{torrent_name}",
        "torrent_size": torrent_bytes,
    }

    app = create_workflow()
    final = app.invoke(initial)
    return dict(final)
