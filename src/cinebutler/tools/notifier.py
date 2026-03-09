"""Feishu notification via OpenClaw."""

import os
import subprocess
from pathlib import Path


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
        return False
    node_exe = Path(node_bin) / "node"
    openclaw = Path(node_bin) / "openclaw"
    if not node_exe.exists() or not openclaw.exists():
        return False
    env = {
        "PATH": f"{node_bin}:{os.environ.get('PATH', '')}",
        "HOME": str(Path.home()),
    }
    try:
        subprocess.run(
            [str(node_exe), str(openclaw), "message", "send", "--channel", "feishu", "--target", target, "--message", message],
            env={**os.environ, **env},
            capture_output=True,
            timeout=30,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
