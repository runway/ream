# Phase 1: Scaffold - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the `ream_xlsx` package skeleton: `pyproject.toml` with hatchling backend, package directory structure, dev toolchain (ruff, mypy strict, pytest), `py.typed` marker, and an importability test. No implementation code — just the installable, lintable, testable shell.

</domain>

<decisions>
## Implementation Decisions

### Package layout
- Flat layout: `ream_xlsx/` at project root (not inside `src/`)
- Existing `src/` directory stays untouched — it holds research scripts, not part of the package
- This avoids confusion between `src/converters.py` (research) and the new package

### Public API stubs
- `__init__.py` defines `__all__` with the planned public names: `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`, `ReamOptions`, `ReamError`, `InvalidWorkbookError`, `ConversionError`
- All names stub as `raise NotImplementedError` or empty classes — enough to import without error
- Phase 2 replaces stubs with real implementations

### Dev toolchain config
- All tool config lives in `pyproject.toml` (no separate `.ruff.toml`, `mypy.ini`, etc.)
- ruff: standard rules, line length 120
- mypy: strict mode enabled
- pytest: test directory `tests/`

### Versioning
- Static version string in `pyproject.toml` — simplest approach for v1
- No dynamic versioning or git-tag-based versioning yet

### Claude's Discretion
- Exact ruff rule selections beyond defaults
- pytest configuration details (markers, fixtures)
- `__init__.py` stub implementation style
- Whether to include a `py.typed` marker as empty file or with content

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/converters.py`: Contains the `xlsx_to_ream()` function (line 669) that Phase 2 will port — not touched in Phase 1
- `requirements.txt`: Lists research dependencies (openpyxl, pandas, openai, etc.) — package only needs openpyxl

### Established Patterns
- No existing package structure — this phase creates it from scratch
- Research code uses loose scripts in `src/` with no `__init__.py`

### Integration Points
- `pyproject.toml` must declare openpyxl as the sole runtime dependency
- `pyproject.toml` must declare Click as a dependency (for Phase 3 CLI entrypoint)
- Dev dependencies: ruff, mypy, pytest (in optional `[dev]` group)
- `[project.scripts]` entrypoint `ream-xlsx` for Phase 3 CLI

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-scaffold*
*Context gathered: 2026-03-30*
