"""Entry point for `python -m docmost_cli`."""

import sys

# Fix Windows console encoding: enable UTF-8 for interactive terminals
# so Rich box-drawing chars and emoji content don't crash with cp1252.
# Only when interactive (preserves pipe/redirect behavior).
if sys.platform == "win32" and sys.stdout.isatty():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from docmost_cli.cli.main import app

app()
