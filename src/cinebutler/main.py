"""CLI entry for CineButler - run from Transmission hook or manually."""

import os
import sys


def main() -> None:
    """Run workflow with Transmission env vars or CLI args."""
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
            sys.exit(0)
        if status == "skipped":
            sys.exit(0)
        sys.exit(1)
    except Exception as e:
        print(f"CineButler error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
