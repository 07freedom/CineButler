"""Feishu notification via OpenClaw."""

import logging
import os
import pwd
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def _real_home() -> str:
    """Get real home dir from passwd, ignoring HOME env var (Transmission daemon sets it wrong)."""
    return pwd.getpwuid(os.getuid()).pw_dir


def send_feishu(
    target: str,
    message: str,
    node_bin: str = "/home/tth/.nvm/versions/node/v22.17.0/bin",
) -> bool:
    """
    Send message to Feishu via OpenClaw.
    Returns True on success, False on failure.
    """
    if not target:
        logger.warning("send_feishu: empty target, skipped")
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
    logger.info("send_feishu: HOME=%s, node_bin=%s", home, node_bin)
    env = {
        "PATH": f"{node_bin}:{os.environ.get('PATH', '')}",
        "HOME": home,
    }
    try:
        result = subprocess.run(
            [str(node_exe), str(openclaw), "message", "send", "--channel", "feishu", "--target", target, "--message", message],
            env={**os.environ, **env},
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
        logger.warning("openclaw timed out after 60s")
        return False
    except FileNotFoundError as e:
        logger.warning("openclaw FileNotFoundError: %s", e)
        return False
