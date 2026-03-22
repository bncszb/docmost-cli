"""Push local changes to Docmost server."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.console import Console

from docmost_cli.sync.diff import ChangeType, SyncDiff

if TYPE_CHECKING:
    from pathlib import Path

    from docmost_cli.api.client import DocmostClient

__all__ = ["PushResult", "push_space"]

_err = Console(stderr=True)


@dataclass
class PushResult:
    """Result of a push operation."""

    created: int = 0
    updated: int = 0
    moved: int = 0
    deleted: int = 0
    unchanged: int = 0
    id_remaps: dict[str, str] = field(default_factory=dict)  # old_id -> new_id


def push_space(
    client: DocmostClient,
    space_slug: str,
    dir_path: Path,
    *,
    dry_run: bool = False,
    delete: bool = False,
) -> PushResult:
    """Push local changes to Docmost server.

    Algorithm:
    1. Resolve space, load manifest, compute diff
    2. Display change summary
    3. If dry_run, return without executing
    4. Execute: create new -> update existing -> move -> delete
    5. Update manifest and frontmatter files

    Args:
        client: Authenticated Docmost client.
        space_slug: Space slug identifier.
        dir_path: Directory containing synced files.
        dry_run: If True, show plan without executing changes.
        delete: If True, delete server pages not found locally.

    Returns:
        PushResult with counts and any ID remaps.
    """
    from docmost_cli.api.pages import (
        create_page_via_import,
        delete_page,
        move_page,
        update_page_meta,
    )
    from docmost_cli.api.pagination import extract_id
    from docmost_cli.api.spaces import resolve_space_id
    from docmost_cli.output.formatter import print_error
    from docmost_cli.sync.diff import compute_diff
    from docmost_cli.sync.frontmatter import write_sync_file
    from docmost_cli.sync.manifest import (
        build_page_entry,
        compute_content_hash,
        load_manifest,
        save_manifest,
    )

    space_id = resolve_space_id(client, space_slug)

    manifest = load_manifest(dir_path)
    if manifest is None:
        print_error(f"No manifest found in '{dir_path}'. Run 'sync pull' first.")

    diff = compute_diff(manifest, dir_path)
    result = PushResult(unchanged=diff.unchanged)

    if not diff.has_changes:
        _err.print("No changes to push.")
        return result

    # Display summary
    _print_summary(diff)

    if dry_run:
        _print_dry_run(diff)
        return result

    # --- Execute changes ---

    enterprise: bool | None = None  # Cached edition detection
    id_remap: dict[str, str] = {}  # old_id -> new_id

    # Phase A: Create new pages (topological order)
    existing_ids = set(manifest.get("pages", {}).keys())
    sorted_new = _topological_sort(diff.new, existing_ids)

    for change in sorted_new:
        meta = change.local_meta or {}
        body = change.local_body or ""
        title = meta.get("title", "Untitled")
        parent_id = meta.get("parent_id", "").strip() or None
        icon = meta.get("icon", "").strip()

        # Resolve parent_id through remap table
        if parent_id and parent_id in id_remap:
            parent_id = id_remap[parent_id]

        _err.print(f"  Creating: {title}")
        new_result = create_page_via_import(client, space_id=space_id, title=title, content=body)
        new_id = extract_id(new_result)

        if parent_id:
            move_page(client, page_id=new_id, parent_page_id=parent_id, position="aaaaa")
        if icon:
            update_page_meta(client, page_id=new_id, icon=icon)

        # Write ID back to frontmatter
        meta["id"] = new_id
        write_sync_file(dir_path / change.filename, meta, body)

        # Update manifest
        content_hash = compute_content_hash(body)
        manifest["pages"][new_id] = build_page_entry(
            title=title,
            filename=change.filename,
            parent_id=parent_id,
            icon=icon,
            content_hash=content_hash,
        )
        existing_ids.add(new_id)
        result.created += 1

    # Phase B: Update modified pages
    for change in diff.modified:
        meta = change.local_meta or {}
        body = change.local_body or ""
        page_id = change.page_id
        title = meta.get("title", "")
        parent_id = meta.get("parent_id", "").strip() or None
        icon = meta.get("icon", "").strip()

        has_content_change = ChangeType.CONTENT_CHANGED in change.changes
        has_meta_change = bool(change.changes & {ChangeType.TITLE_CHANGED, ChangeType.ICON_CHANGED})

        # Content update
        if has_content_change:
            if enterprise is None:
                # Probe Enterprise endpoint
                enterprise = _try_enterprise_update(client, page_id, body)
                if enterprise:
                    _err.print(f"  Updated (Enterprise): {title}")
                else:
                    # Fall back to community: create-then-delete
                    _err.print(f"  Replacing (Community): {title}")
                    new_id = _community_update(
                        client,
                        space_id=space_id,
                        old_page_id=page_id,
                        title=title,
                        content=body,
                        parent_id=parent_id,
                        icon=icon,
                    )
                    id_remap[page_id] = new_id
                    meta["id"] = new_id
                    write_sync_file(dir_path / change.filename, meta, body)
                    manifest["pages"].pop(page_id, None)
                    page_id = new_id
            elif enterprise:
                _try_enterprise_update(client, page_id, body)
                _err.print(f"  Updated: {title}")
            else:
                _err.print(f"  Replacing: {title}")
                new_id = _community_update(
                    client,
                    space_id=space_id,
                    old_page_id=page_id,
                    title=title,
                    content=body,
                    parent_id=parent_id,
                    icon=icon,
                )
                id_remap[page_id] = new_id
                meta["id"] = new_id
                write_sync_file(dir_path / change.filename, meta, body)
                manifest["pages"].pop(page_id, None)
                page_id = new_id

        # Meta update (title/icon) - skip if community update already recreated the page
        if has_meta_change and not (has_content_change and not enterprise):
            _err.print(f"  Metadata: {title}")
            update_page_meta(
                client,
                page_id=page_id,
                title=title if ChangeType.TITLE_CHANGED in change.changes else None,
                icon=icon if ChangeType.ICON_CHANGED in change.changes else None,
            )

        # Update manifest entry
        content_hash = compute_content_hash(body)
        manifest["pages"][page_id] = build_page_entry(
            title=title,
            filename=change.filename,
            parent_id=parent_id,
            icon=icon,
            content_hash=content_hash,
        )
        result.updated += 1

    # Phase B2: Move pages (that weren't already handled as part of modified)
    modified_ids = {c.page_id for c in diff.modified}
    for change in diff.moved:
        if change.page_id in modified_ids:
            # Already handled as part of content/meta update
            continue

        meta = change.local_meta or {}
        page_id = change.page_id
        parent_id = meta.get("parent_id", "").strip() or None
        title = meta.get("title", page_id)

        # Check remap
        if page_id in id_remap:
            page_id = id_remap[page_id]
        if parent_id and parent_id in id_remap:
            parent_id = id_remap[parent_id]

        _err.print(f"  Moving: {title}")
        move_page(client, page_id=page_id, parent_page_id=parent_id, position="aaaaa")

        # Update manifest
        if page_id in manifest["pages"]:
            manifest["pages"][page_id]["parent_id"] = parent_id
        result.moved += 1

    # Phase C: Deletions
    if diff.deleted:
        if delete:
            for change in diff.deleted:
                entry = change.manifest_entry or {}
                _err.print(f"  Deleting: {entry.get('title', change.page_id)}")
                delete_page(client, change.page_id)
                manifest["pages"].pop(change.page_id, None)
                result.deleted += 1
        else:
            _err.print(
                f"  [yellow]{len(diff.deleted)} page(s) on server not found locally. "
                "Use --delete to remove.[/yellow]"
            )

    # Save ID remaps
    result.id_remaps = id_remap
    if id_remap:
        _err.print(
            f"[yellow]Community edition: {len(id_remap)} page(s) got new IDs. "
            "Internal wiki links may need updating.[/yellow]"
        )

    # Save manifest
    save_manifest(dir_path, manifest)

    _err.print(
        f"Pushed to '{space_slug}': "
        f"{result.created} created, {result.updated} updated, "
        f"{result.moved} moved, {result.deleted} deleted"
    )
    return result


def _try_enterprise_update(client: DocmostClient, page_id: str, content: str) -> bool:
    """Try Enterprise content update endpoint.

    Uses post_raw with raise_on_error=False to silently probe whether
    the Enterprise-only /pages/content/update endpoint is available.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.
        content: Markdown content.

    Returns:
        True if the endpoint succeeded, False otherwise.
    """
    response = client.post_raw(
        "/pages/content/update",
        json={"pageId": page_id, "content": content, "format": "markdown"},
        raise_on_error=False,
    )
    return response.is_success


def _community_update(
    client: DocmostClient,
    *,
    space_id: str,
    old_page_id: str,
    title: str,
    content: str,
    parent_id: str | None,
    icon: str,
) -> str:
    """Safe content update for Community edition: create new, then delete old.

    Creates a new page with the updated content, moves it to the correct
    parent, sets icon, then deletes the old page. The old page is only
    deleted after the new one is confirmed created.

    Args:
        client: Authenticated Docmost client.
        space_id: Space UUID.
        old_page_id: ID of the page to replace.
        title: Page title.
        content: Markdown content.
        parent_id: Parent page ID, or None for root.
        icon: Page icon string.

    Returns:
        New page ID.
    """
    from docmost_cli.api.pages import (
        create_page_via_import,
        delete_page,
        move_page,
        update_page_meta,
    )
    from docmost_cli.api.pagination import extract_id

    # 1. Create new page
    result = create_page_via_import(client, space_id=space_id, title=title, content=content)
    new_id = extract_id(result)

    # 2. Move to correct parent
    if parent_id:
        move_page(client, page_id=new_id, parent_page_id=parent_id, position="aaaaa")

    # 3. Set icon
    if icon:
        update_page_meta(client, page_id=new_id, icon=icon)

    # 4. Delete old page (safe: new page already exists)
    delete_page(client, old_page_id)

    return new_id


def _topological_sort(new_changes: list, existing_ids: set[str]) -> list:
    """Sort new pages so parents are created before children.

    Pages with no parent or whose parent already exists on the server
    are placed first. Pages whose parent is also new are placed after
    their parent. Handles circular/broken references gracefully by
    appending remaining pages after max iterations.

    Args:
        new_changes: List of PageChange with NEW type.
        existing_ids: Set of page IDs already on the server.

    Returns:
        Sorted list of PageChange.
    """
    result = []
    remaining = list(new_changes)
    resolved = set(existing_ids)

    max_iterations = len(remaining) + 1
    for _ in range(max_iterations):
        if not remaining:
            break
        next_remaining = []
        for change in remaining:
            meta = change.local_meta or {}
            parent_id = meta.get("parent_id", "").strip() or None
            if parent_id is None or parent_id in resolved:
                result.append(change)
            else:
                next_remaining.append(change)
        if len(next_remaining) == len(remaining):
            # No progress -- circular or broken parent reference -- add remaining
            result.extend(next_remaining)
            break
        remaining = next_remaining

    return result


def _print_summary(diff: SyncDiff) -> None:
    """Print change summary to stderr.

    Args:
        diff: The computed SyncDiff.
    """

    lines: list[str] = []
    if diff.new:
        lines.append(f"  Create:    {len(diff.new)} page(s)")
    if diff.modified:
        lines.append(f"  Update:    {len(diff.modified)} page(s)")
    if diff.moved:
        move_only = [c for c in diff.moved if c not in diff.modified]
        if move_only:
            lines.append(f"  Move:      {len(move_only)} page(s)")
    if diff.deleted:
        lines.append(f"  Delete:    {len(diff.deleted)} page(s)")
    lines.append(f"  Unchanged: {diff.unchanged} page(s)")
    _err.print("Push plan:")
    for line in lines:
        _err.print(line)


def _print_dry_run(diff: SyncDiff) -> None:
    """Print detailed plan to stdout for scripting.

    Args:
        diff: The computed SyncDiff.
    """
    import sys

    for change in diff.new:
        meta = change.local_meta or {}
        sys.stdout.write(f"CREATE {change.filename} ({meta.get('title', '?')})\n")
    for change in diff.modified:
        types = ", ".join(c.value for c in change.changes if c != ChangeType.MOVED)
        sys.stdout.write(f"UPDATE {change.filename} ({types})\n")
    for change in diff.moved:
        if change not in diff.modified:
            meta = change.local_meta or {}
            sys.stdout.write(
                f"MOVE   {change.filename} -> parent:{meta.get('parent_id', 'root')}\n"
            )
    for change in diff.deleted:
        entry = change.manifest_entry or {}
        sys.stdout.write(f"DELETE {entry.get('filename', '?')} ({entry.get('title', '?')})\n")
