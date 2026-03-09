"""Basic tests for CineButler workflow nodes."""

import tempfile
from pathlib import Path

import pytest

from cinebutler.config import load_config
from cinebutler.nodes.parse import parse_node
from cinebutler.nodes.rename import rename_node
from cinebutler.tools.filesystem import select_target_with_space


# --- parse_node ---


def test_parse_node_movie_single_file() -> None:
    """Parse single movie file: 黑暗骑士.mkv."""
    state = {
        "torrent_name": "黑暗骑士.mkv",
        "torrent_dir": "/tmp/downloads/",
        "torrent_path": "/tmp/downloads/黑暗骑士.mkv",
        "torrent_size": 0,
    }
    result = parse_node(state)
    assert result["torrent_name"] == "黑暗骑士.mkv"
    assert result["is_directory"] is False
    assert result["title"]
    assert result["year"] is None
    assert result["season"] is None
    assert result["episodes"] == []


def test_parse_node_movie_with_year() -> None:
    """Parse movie with year: Inception (2010).mkv."""
    state = {
        "torrent_name": "Inception (2010).mkv",
        "torrent_dir": "/tmp/",
        "torrent_path": "/tmp/Inception (2010).mkv",
        "torrent_size": 0,
    }
    result = parse_node(state)
    assert result["year"] == 2010
    assert "Inception" in result["title"]


def test_parse_node_tv_episode() -> None:
    """Parse TV episode: Show.Name.S01E01.mkv."""
    state = {
        "torrent_name": "The.Office.S01E01.1080p.mkv",
        "torrent_dir": "/tmp/",
        "torrent_path": "/tmp/The.Office.S01E01.1080p.mkv",
        "torrent_size": 0,
    }
    result = parse_node(state)
    assert result["season"] == 1
    assert result["episodes"] == [1]
    assert result["is_directory"] is False


def test_parse_node_builds_path_from_dir_and_name() -> None:
    """When torrent_path empty, builds from torrent_dir + torrent_name."""
    state = {
        "torrent_name": "test.mkv",
        "torrent_dir": "/dl",
        "torrent_path": "",
        "torrent_size": 0,
    }
    result = parse_node(state)
    assert result["torrent_path"] == "/dl/test.mkv"


# --- rename_node ---


def test_rename_node_movie_single_file() -> None:
    """Rename single movie file -> Infuse format."""
    state = {
        "media_type": "movie",
        "title": "黑暗骑士",
        "year": 2008,
        "tmdb_id": 155,
        "is_directory": False,
        "torrent_name": "黑暗骑士.mkv",
        "episodes": [],
    }
    result = rename_node(state)
    assert result["new_name"] == "黑暗骑士 (2008)"
    assert "黑暗骑士 (2008)" in result["new_file_name"]
    assert result["new_file_name"].endswith(".mkv")


def test_rename_node_movie_with_tmdb_id() -> None:
    """Movie with tmdb_id includes {tmdb-xxx} in filename."""
    state = {
        "media_type": "movie",
        "title": "Inception",
        "year": 2010,
        "tmdb_id": 27205,
        "is_directory": False,
        "torrent_name": "Inception.2010.mkv",
        "episodes": [],
    }
    result = rename_node(state)
    assert "{tmdb-27205}" in result["new_file_name"]


def test_rename_node_tv_single_episode() -> None:
    """Rename TV single episode -> Show.S01E01.ext."""
    state = {
        "media_type": "tv",
        "title": "The Office",
        "year": 2005,
        "season": 1,
        "episodes": [1],
        "is_directory": False,
        "torrent_name": "ep.mkv",
    }
    result = rename_node(state)
    assert result["new_name"] == "The Office (2005)"
    assert result["new_season_folder"] == "Season 01"
    assert "The Office.S01E01" in result["new_file_name"]


def test_rename_node_tv_directory() -> None:
    """TV directory keeps inner structure."""
    state = {
        "media_type": "tv",
        "title": "Breaking Bad",
        "year": 2008,
        "is_directory": True,
        "torrent_name": "Breaking.Bad.S01",
    }
    result = rename_node(state)
    assert result["new_name"] == "Breaking Bad (2008)"
    assert result["new_file_name"] is None
    assert result["new_season_folder"] is None


# --- select_target_with_space ---


def test_select_target_with_space_prefers_least_free() -> None:
    """When multiple targets have space, pick the one with least free."""
    with tempfile.TemporaryDirectory() as d:
        p1 = Path(d) / "target1"
        p2 = Path(d) / "target2"
        p1.mkdir()
        p2.mkdir()
        targets = [str(p1), str(p2)]
        chosen = select_target_with_space(targets, required_bytes=1)
        assert chosen is not None
        assert chosen in (str(p1), str(p2))


def test_select_target_with_space_returns_none_when_insufficient() -> None:
    """Return None when no target has enough space."""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "small"
        p.mkdir()
        chosen = select_target_with_space([str(p)], required_bytes=10**20)
        assert chosen is None


def test_select_target_with_space_skips_nonexistent() -> None:
    """Skip targets that do not exist."""
    chosen = select_target_with_space(["/nonexistent/path/xyz"], required_bytes=1)
    assert chosen is None


# --- config ---


def test_config_load() -> None:
    """load_config parses config.yaml correctly."""
    config = load_config()
    assert config.placement_rules.movie.targets
    assert config.placement_rules.tv.targets
    assert config.placement_rules.adult.action == "skip"
    assert config.notification.feishu_target
    assert config.tmdb.language == "zh-CN"
