"""Send Feishu notification for success/failure/skip."""

import logging

from cinebutler.config import load_config
from cinebutler.models import CineButlerState
from cinebutler.tools.notifier import send_feishu

logger = logging.getLogger(__name__)


def _build_message(state: CineButlerState) -> str:
    """Build notification message from state."""
    status = state.get("status", "unknown")
    name = state.get("torrent_name", "未知")
    msg_line = state.get("message", "")
    final_path = state.get("final_path", "")
    target_dir = state.get("target_dir", "")

    if status == "success":
        return f"""✅ CineButler 整理完成
📌 作品：{name}
📁 目标：{final_path}"""
    elif status == "skipped":
        return f"""⏭ CineButler 已跳过
📌 作品：{name}
💬 原因：{msg_line}"""
    else:
        return f"""❌ CineButler 整理失败
📌 作品：{name}
💬 原因：{msg_line}
📁 目标目录：{target_dir or 'N/A'}"""


def notify_node(state: CineButlerState) -> dict:
    """Send Feishu notification based on workflow result."""
    config = load_config()
    target = config.notification.feishu_target
    node_bin = config.notification.node_bin
    if not target:
        logger.info("feishu_target not configured, skip notification")
        return {}
    msg = _build_message(state)
    ok = send_feishu(target, msg, node_bin)
    if ok:
        logger.info("feishu notification sent to %s", target)
    else:
        logger.warning("feishu notification FAILED (target=%s, node_bin=%s)", target, node_bin)
    return {}
