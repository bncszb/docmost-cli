"""Entry point for `python -m docmost_cli`."""

import sys

# Fix Windows console encoding: enable UTF-8 so Rich box-drawing chars
# and emoji content don't crash with cp1252. Applied unconditionally
# on Windows (not just isatty) because Git Bash/MSYS2/Claude Code CLI
# report isatty=False but still need UTF-8.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from docmost_cli.cli.main import app

app()
