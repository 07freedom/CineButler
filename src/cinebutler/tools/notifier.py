"""Send notification via OpenClaw (channel-configurable)."""

import logging
import os
import pwd
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def _real_home() -> str:
    """Get real home directory from passwd, ignoring HOME env var.

    Transmission daemon sets HOME incorrectly, so we read from passwd directly.
    """
    return pwd.getpwuid(os.getuid()).pw_dir


def send_notification(
    channel: str,
    target: str,
    message: str,
    node_bin: str,
) -> bool:
    """
    Send a message via OpenClaw.

    Args:
        channel: OpenClaw channel name (e.g. "feishu", "telegram")
        target:  Channel-specific target ID (user ID, chat ID, etc.)
        message: Message text to send
        node_bin: Path to directory containing node and openclaw binaries

    Returns:
        True on success, False on failure.
    """
    if not target:
        logger.warning("send_notification: empty target, skipped")
        return False

    node_exe = (Path(node_bin) / "node").expanduser()
    openclaw = (Path(node_bin) / "openclaw").expanduser()

    if not node_exe.exists():
        logger.warning("node not found at %s", node_exe)
        return False
    if not openclaw.exists():
        logger.warning("openclaw not found at %s", openclaw)
        return False

    home = _real_home()
    logger.info("send_notification: channel=%s HOME=%s node_bin=%s", channel, home, node_bin)

    env = {
        **os.environ,
        "PATH": f"{node_bin}:{os.environ.get('PATH', '')}",
        "HOME": home,
    }
    try:
        result = subprocess.run(
            [str(node_exe), str(openclaw), "message", "send",
             "--channel", channel, "--target", target, "--message", message],
            env=env,
            capture_output=True,
            timeout=120,
            check=True,
        )
        logger.debug("openclaw stdout: %s", result.stdout.decode(errors="replace"))
        return True
    except subprocess.CalledProcessError as e:
        logger.warning("openclaw failed (rc=%d): %s", e.returncode, e.stderr.decode(errors="replace"))
        return False
    except subprocess.TimeoutExpired:
        logger.warning("openclaw timed out after 120s")
        return False
    except FileNotFoundError as e:
        logger.warning("openclaw FileNotFoundError: %s", e)
        return False
