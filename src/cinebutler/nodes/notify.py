"""Send notification for workflow result via OpenClaw."""

import logging

from cinebutler.config import load_config
from cinebutler.models import CineButlerState
from cinebutler.tools.notifier import send_notification

logger = logging.getLogger(__name__)


def _build_message(state: CineButlerState) -> str:
    """Build notification message from workflow state."""
    status = state.get("status", "unknown")
    name = state.get("torrent_name", "Unknown")
    reason = state.get("message", "")
    final_path = state.get("final_path", "")
    target_dir = state.get("target_dir", "")

    if status == "success":
        return (
            f"✅ CineButler: organized successfully\n"
            f"📌 {name}\n"
            f"📁 {final_path}"
        )
    elif status == "duplicate":
        return (
            f"⚠️ CineButler: duplicate file skipped\n"
            f"📌 {name}\n"
            f"💬 {reason}\n"
            f"📁 {final_path or target_dir}"
        )
    elif status == "skipped":
        return (
            f"⏭ CineButler: skipped\n"
            f"📌 {name}\n"
            f"💬 {reason}"
        )
    else:
        return (
            f"❌ CineButler: failed\n"
            f"📌 {name}\n"
            f"💬 {reason}\n"
            f"📁 {target_dir or 'N/A'}"
        )


def notify_node(state: CineButlerState) -> dict:
    """Send notification via OpenClaw based on workflow result."""
    config = load_config()
    notif = config.notification

    if notif.channel == "none":
        logger.info("notification channel is 'none', skipping")
        return {}

    if not notif.target:
        logger.info("notification target not configured, skipping")
        return {}

    msg = _build_message(state)
    ok = send_notification(notif.channel, notif.target, msg, notif.node_bin)

    if ok:
        logger.info("notification sent via %s to %s", notif.channel, notif.target)
    else:
        logger.warning("notification FAILED (channel=%s target=%s)", notif.channel, notif.target)

    return {}
