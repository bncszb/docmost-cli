# Changelog

## 0.2.0 (2026-03-22)

- Retry with exponential backoff for transient errors (429, 5xx)
- `--verbose` HTTP debug logging (request/response to stderr)
- Page duplicate, copy, children, history, export, import commands
- Tree view (`--tree`) for page listing
- Workspace info/members, user me, attachment search commands
- Pagination auto-follow with safety guard (max 1000 iterations)
- ProseMirror-to-Markdown converter (all block nodes and marks)
- Claude Code skill (`/docmost`) for wiki interaction
- Comprehensive README with command reference
- MIT LICENSE file
- Session cache file permissions (0600)
- 175 tests, 0 lint errors

## 0.1.0 (2026-03-22)

- Initial release
- Project scaffolding with typer CLI framework
- Configuration system with TOML profiles and environment variable overrides
- HTTP client with API key (Enterprise) and session (Community) auth auto-detection
- Page CRUD: create (via import endpoint), read, update, delete, move
- Space list, create, update
- Comment list, create, update (ProseMirror JSON wrapping)
- Full-text search with space filtering
- Output helpers enforcing stdout/stderr separation
- Edition-agnostic design (Community + Enterprise)
- 50 tests with pytest + pytest-httpx
