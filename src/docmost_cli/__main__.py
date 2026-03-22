"""Entry point for `python -m docmost_cli`."""

import sys

# Fix Windows console encoding: enable UTF-8 so Rich box-drawing chars
# and emoji content don't crash with cp1252. This runs before cli/main.py
# is imported. See also _ensure_utf8_stdio() in cli/main.py (for the
# pyproject scripts entry point which bypasses __main__.py).
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from docmost_cli.cli.main import app

app()
