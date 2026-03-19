"""Tests for CineButler workflow nodes and tools."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cinebutler.nodes.notify import _build_message, notify_node
from cinebutler.tools.filesystem import (
    find_existing_season_folder,
    search_existing_folder,
    select_target_with_space,
)


# --- notify_node ---


def _make_notif_config(channel="feishu", target="ou_test"):
    cfg = MagicMock()
    cfg.notification.channel = channel
    cfg.notification.target = target
    cfg.notification.node_bin = "/usr/bin"
    return cfg


def test_notify_skips_when_channel_none():
    """channel='none' should skip without calling send_notification."""
    cfg = _make_notif_config(channel="none")
    with patch("cinebutler.nodes.notify.load_config", return_value=cfg), \
         patch("cinebutler.nodes.notify.send_notification") as mock_send:
        result = notify_node({"status": "success", "torrent_name": "test.mkv"})
    mock_send.assert_not_called()
    assert result == {}


def test_notify_skips_when_target_empty():
    """Empty target should skip without calling send_notification."""
    cfg = _make_notif_config(channel="feishu", target="")
    with patch("cinebutler.nodes.notify.load_config", return_value=cfg), \
         patch("cinebutler.nodes.notify.send_notification") as mock_send:
        result = notify_node({"status": "success", "torrent_name": "test.mkv"})
    mock_send.assert_not_called()
    assert result == {}


def test_notify_sends_when_configured():
    """Valid channel+target should call send_notification."""
    cfg = _make_notif_config(channel="feishu", target="ou_xxx")
    with patch("cinebutler.nodes.notify.load_config", return_value=cfg), \
         patch("cinebutler.nodes.notify.send_notification", return_value=True) as mock_send:
        notify_node({"status": "success", "torrent_name": "test.mkv", "final_path": "/media/test.mkv"})
    mock_send.assert_called_once()


# --- _build_message ---


def test_build_message_success():
    msg = _build_message({"status": "success", "torrent_name": "foo.mkv", "final_path": "/media/foo.mkv"})
    assert "✅" in msg
    assert "foo.mkv" in msg


def test_build_message_duplicate():
    msg = _build_message({"status": "duplicate", "torrent_name": "foo.mkv", "message": "foo.mkv exists"})
    assert "⚠️" in msg
    assert "duplicate" in msg


def test_build_message_skipped():
    msg = _build_message({"status": "skipped", "torrent_name": "foo.mkv", "message": "action=skip"})
    assert "⏭" in msg


def test_build_message_failed():
    msg = _build_message({"status": "failed", "torrent_name": "foo.mkv", "message": "No space"})
    assert "❌" in msg


# --- select_target_with_space ---


def test_select_target_prefers_least_free():
    with tempfile.TemporaryDirectory() as d:
        p1 = Path(d) / "t1"
        p2 = Path(d) / "t2"
        p1.mkdir()
        p2.mkdir()
        chosen = select_target_with_space([str(p1), str(p2)], required_bytes=1)
        assert chosen in (str(p1), str(p2))


def test_select_target_returns_none_insufficient_space():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t"
        p.mkdir()
        assert select_target_with_space([str(p)], required_bytes=10**20) is None


def test_select_target_skips_nonexistent():
    assert select_target_with_space(["/nonexistent/xyz"], required_bytes=1) is None


# --- search_existing_folder ---


def test_search_existing_folder_exact_match():
    with tempfile.TemporaryDirectory() as d:
        show = Path(d) / "Breaking Bad"
        show.mkdir()
        result = search_existing_folder([d], ["Breaking Bad"])
        assert result == str(show)


def test_search_existing_folder_substring_match():
    with tempfile.TemporaryDirectory() as d:
        show = Path(d) / "Breaking Bad (2008)"
        show.mkdir()
        result = search_existing_folder([d], ["Breaking Bad"])
        assert result == str(show)


def test_search_existing_folder_returns_none_when_missing():
    with tempfile.TemporaryDirectory() as d:
        result = search_existing_folder([d], ["Nonexistent Show"])
        assert result is None


# --- find_existing_season_folder ---


def test_find_existing_season_folder_s01():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "S01").mkdir()
        (Path(d) / "S02").mkdir()
        assert find_existing_season_folder(d, 1) == "S01"
        assert find_existing_season_folder(d, 2) == "S02"


def test_find_existing_season_folder_season_word():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "Season 03").mkdir()
        assert find_existing_season_folder(d, 3) == "Season 03"


def test_find_existing_season_folder_chinese():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "第二季").mkdir()
        assert find_existing_season_folder(d, 2) == "第二季"


def test_find_existing_season_folder_missing():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "S01").mkdir()
        assert find_existing_season_folder(d, 5) is None
