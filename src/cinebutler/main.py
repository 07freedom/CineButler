"""CLI entry for CineButler - run from Transmission hook or manually."""

import logging
import os
import sys


def _setup_logging() -> None:
    """Configure logging: INFO to stderr so hook script captures it in log file."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(name)s] %(levelname)s %(message)s",
        stream=sys.stderr,
    )


def main() -> None:
    """Run workflow with Transmission env vars or CLI args."""
    _setup_logging()
    name = os.environ.get("TR_TORRENT_NAME") or os.environ.get("TORRENT_NAME", "")
    directory = os.environ.get("TR_TORRENT_DIR") or os.environ.get("TORRENT_DIR", "")
    bytes_dl = int(os.environ.get("TR_TORRENT_BYTES_DOWNLOADED", "0") or "0")

    if len(sys.argv) >= 2:
        name = sys.argv[1]
    if len(sys.argv) >= 3:
        directory = sys.argv[2]
    if len(sys.argv) >= 4:
        try:
            bytes_dl = int(sys.argv[3])
        except ValueError:
            pass

    if not name or not directory:
        print("Usage: cinebutler [TORRENT_NAME TORRENT_DIR [BYTES]]", file=sys.stderr)
        print("  Or set TR_TORRENT_NAME, TR_TORRENT_DIR, TR_TORRENT_BYTES_DOWNLOADED", file=sys.stderr)
        sys.exit(1)

    from cinebutler.workflow import run_workflow

    try:
        result = run_workflow(torrent_name=name, torrent_dir=directory, torrent_bytes=bytes_dl)
        status = result.get("status", "unknown")
        if status == "success":
            print(f"CineButler: {result.get('message', 'Done')} -> {result.get('final_path', '')}")
            sys.exit(0)
        if status == "skipped":
            print(f"CineButler skipped: {result.get('message', '')}")
            sys.exit(0)
        print(f"CineButler failed: [{status}] {result.get('message', 'no message')}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"CineButler error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
