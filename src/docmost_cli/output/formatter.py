"""Output dispatch: stdout/stderr separation for all command types."""

import json
import sys
from typing import Any, NoReturn

from rich.console import Console

__all__ = [
    "print_content",
    "print_content_with_meta",
    "print_error",
    "print_key_value",
    "print_result",
    "print_table",
]

_err_console = Console(stderr=True)


def print_content(content: str) -> None:
    """Print content (Markdown) directly to stdout."""
    sys.stdout.write(content)


def print_content_with_meta(content: str, meta: dict[str, Any]) -> None:
    """Print YAML frontmatter + Markdown content to stdout."""
    lines = ["---"]
    for key, value in meta.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    sys.stdout.write("\n".join(lines))
    sys.stdout.write(content)


def print_key_value(data: dict[str, Any], key_style: str = "bold") -> None:
    """Print key-value pairs for single-item info display.

    Args:
        data: Dictionary of key-value pairs to display.
        key_style: Rich style string for keys column.
    """
    from rich.table import Table

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style=key_style)
    table.add_column()
    for key, value in data.items():
        if value is not None and value != "":
            table.add_row(str(key), str(value))

    console = Console()
    console.print(table)


def print_table(rows: list[dict[str, Any]], columns: list[str], json_mode: bool = False) -> None:
    """Print as rich table or JSON array depending on mode."""
    if json_mode:
        filtered = [{col: row.get(col) for col in columns} for row in rows]
        sys.stdout.write(json.dumps(filtered, indent=2, default=str) + "\n")
        return

    from rich.table import Table

    table = Table()
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*(str(row.get(col, "")) for col in columns))

    console = Console()
    console.print(table)


def print_result(resource_id: str, message: str) -> None:
    """Print resource ID to stdout, confirmation to stderr."""
    sys.stdout.write(resource_id + "\n")
    _err_console.print(message)


def print_error(message: str, exit_code: int = 1) -> NoReturn:
    """Print error to stderr and exit with given code."""
    _err_console.print(f"[red]Error:[/red] {message}")
    raise SystemExit(exit_code)
