# Changelog

## 0.2.3 (2026-03-22)

- Fix `--parent` on `page create`: send fractional index position string (Docmost requires 5-12 char string, not integer)
- Fix emoji crash on all Windows terminals: remove `isatty()` guard, always reconfigure to UTF-8 on Windows
- Fix `--content` escape sequences: `\n` and `\t` now interpreted as actual newline/tab
- Position parameter on `page move` changed from `int` to `str` (fractional index format)

## 0.2.2 (2026-03-22)

- Fix `--parent` on `page create` silently ignored (import endpoint ignores parentPageId; now calls move_page as fallback)
- Fix `--help` crash on Windows (`OSError` from Rich's LegacyWindowsRenderer on cp1252 consoles)
- Fix `page get --meta` crash when page content contains emoji (✅❌⚠️📊)
- Reconfigure stdout/stderr to UTF-8 at startup on Windows interactive terminals

## 0.2.1 (2026-03-22)

- Fix tree view crash on Windows with emoji page icons (cp1252 encoding)
- Fix silent Enterprise endpoint probe leaking error messages on Community edition
- Fix API endpoints discovered during live integration testing:
  - `/spaces/list` → `/spaces`
  - `/comments/list` → `/comments`
  - `/pages/export` format `md` → `markdown`, response is ZIP not JSON
  - Auth token extracted from `authToken` cookie (not `token`)
  - Comment content JSON-stringified for API
- Consolidate duplicated code: shared `extract_items`, `extract_id`, `build_body` helpers
- Remove 6 dead stub files (-84 lines)
- Add `post_raw()` to DocmostClient for binary/probe responses
- Fix double file read in page import
- Add Claude Code skill (`/docmost`) for wiki interaction
- Prepare for PyPI: py.typed marker, CHANGELOG, dependency upper bounds, classifiers

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
