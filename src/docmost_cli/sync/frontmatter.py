"""YAML frontmatter parser/serializer for sync files.

Hand-rolled for flat key-value strings only — no PyYAML dependency.
Compatible with the format produced by output/formatter.py:print_content_with_meta.
"""

from pathlib import Path

__all__ = [
    "parse_frontmatter",
    "read_sync_file",
    "serialize_frontmatter",
    "write_sync_file",
]

# Fixed ordering for known sync fields, ensuring consistent diffs.
_FIELD_ORDER = ("id", "title", "parent_id", "icon")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter from text.

    Splits on ``---`` delimiters.  Parses flat ``key: value`` pairs.
    Values are stripped.  Keys are stripped.

    Args:
        text: Full file content (frontmatter + body).

    Returns:
        Tuple of (metadata dict, body string).
        If no frontmatter found, returns (empty dict, original text).

    Rules:
        - First line must be ``---`` (stripped).
        - Frontmatter ends at next ``---`` line.
        - Each line in frontmatter is ``key: value`` (split on first ``:`` only).
        - Lines without ``:`` are skipped.
        - Empty values are stored as empty string.
        - Body is everything after the closing ``---``, with one leading newline
          stripped (if present).
    """
    # Normalise Windows line endings so splitting is consistent.
    normalised = text.replace("\r\n", "\n")

    lines = normalised.split("\n")

    # First line must be '---'
    if not lines or lines[0].strip() != "---":
        return {}, text

    # Find closing '---'
    closing_idx: int | None = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break

    if closing_idx is None:
        # No closing delimiter — treat entire text as body.
        return {}, text

    # Parse key: value pairs between the delimiters.
    metadata: dict[str, str] = {}
    for line in lines[1:closing_idx]:
        colon_pos = line.find(":")
        if colon_pos == -1:
            continue
        key = line[:colon_pos].strip()
        value = line[colon_pos + 1 :].strip()
        if key:
            metadata[key] = value

    # Body is everything after the closing '---'.
    # Strip exactly one leading newline (the newline right after '---').
    body = "\n".join(lines[closing_idx + 1 :])
    if body.startswith("\n"):
        body = body[1:]

    return metadata, body


def serialize_frontmatter(metadata: dict[str, str], body: str) -> str:
    """Combine metadata dict and body into frontmatter + markdown string.

    Output format::

        ---
        key1: value1
        key2: value2
        ---

        body content here

    An empty line separates the closing ``---`` from the body.
    Known sync fields (id, title, parent_id, icon) appear first in a fixed
    order; any remaining keys follow in insertion order.

    Args:
        metadata: Flat key-value metadata.
        body: Markdown body content.

    Returns:
        Combined string with YAML frontmatter header.
    """
    lines: list[str] = ["---"]

    # Emit known fields in fixed order first.
    seen: set[str] = set()
    for key in _FIELD_ORDER:
        if key in metadata:
            lines.append(f"{key}: {metadata[key]}")
            seen.add(key)

    # Emit remaining fields in insertion order.
    for key, value in metadata.items():
        if key not in seen:
            lines.append(f"{key}: {value}")

    lines.append("---")
    lines.append("")  # blank separator line between closing --- and body
    lines.append("")  # ensures trailing \n after the blank line
    return "\n".join(lines) + body


def read_sync_file(path: Path) -> tuple[dict[str, str], str]:
    """Read a sync ``.md`` file, returning parsed frontmatter and body.

    Args:
        path: Path to the markdown file.

    Returns:
        Tuple of (metadata dict, body markdown string).

    Raises:
        FileNotFoundError: If *path* does not exist.
    """
    content = path.read_text(encoding="utf-8")
    return parse_frontmatter(content)


def write_sync_file(path: Path, metadata: dict[str, str], body: str) -> None:
    """Write a sync ``.md`` file with frontmatter.

    Creates parent directories if needed.  Writes with UTF-8 encoding.

    Args:
        path: Destination file path.
        metadata: Flat key-value metadata for the frontmatter header.
        body: Markdown body content.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_frontmatter(metadata, body), encoding="utf-8")
