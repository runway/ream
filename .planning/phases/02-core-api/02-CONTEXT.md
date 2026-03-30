# Phase 2: Core API - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`, `ReamOptions` dataclass, and exception hierarchy (`ReamError`, `InvalidWorkbookError`, `ConversionError`). Replace the `NotImplementedError` stubs in `ream_xlsx/__init__.py` with working implementations. All three entry points must produce identical output for the same workbook. TDD: tests written before implementation.

</domain>

<decisions>
## Implementation Decisions

### Porting strategy
- Copy and refactor the core logic from `src/converters.py` into `ream_xlsx/` as internal module(s)
- `src/converters.py` must remain untouched (locked decision from project setup) — no imports from it
- Helper functions (`_ream_scalar`, `_ream_quote`, `_needs_ream_quoting`, `_cell_value_str`) come along with the core logic
- Internal modules are private (prefixed with `_` or kept out of `__all__`)

### ReamOptions design
- Frozen dataclass with default values matching current `src/converters.py` behavior:
  - `max_rows_per_sheet: int = 500`
  - `force_col_selectors: bool = False`
  - `collapse_rows: bool = False`
- All three public functions accept `options: ReamOptions | None = None` — `None` means use defaults

### Wire version control
- Auto-derived from `collapse_rows`: version 11 if `collapse_rows=True`, version 9 otherwise
- Not user-controllable — this matches current `src/converters.py` behavior exactly
- Version header always appears in output (`#!REAM 9` or `#!REAM 11`)

### Error handling
- `InvalidWorkbookError`: raised for missing files, non-XLSX files, corrupted/unreadable payloads, password-protected files
- `ConversionError`: raised for failures during conversion (e.g., openpyxl internal errors during cell reading)
- Both are subclasses of `ReamError`
- Error messages should be human-readable and include the cause

### Entry point routing
- `xlsx_to_ream(path)` opens the file and delegates to shared internal conversion logic
- `bytes_to_ream(data)` wraps bytes in `BytesIO` and delegates to the same logic
- `file_to_ream(stream)` passes the stream directly to the same logic
- All three converge on a single internal function that takes an openpyxl Workbook

### Claude's Discretion
- Internal module structure (single `_converter.py` vs multiple internal modules)
- How to structure the shared conversion function
- Test file organization (single file vs multiple)
- Test fixture strategy for XLSX files (create in-memory with openpyxl in tests)
- Exact error message wording

</decisions>

<specifics>
## Specific Ideas

- Output must be byte-for-byte identical when the same workbook is passed to any of the three entry points
- Output must be deterministic: same input twice → same output (API-06)
- The existing `src/converters.py` has ~140 lines of core logic plus ~90 lines of helpers — straightforward to port

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/converters.py:669-805`: `xlsx_to_ream()` — the complete conversion logic to port
- `src/converters.py:15-30`: `_cell_value_str()` — cell value stringification
- `src/converters.py:33-57`: `_needs_ream_quoting()` — quoting rules
- `src/converters.py:60-63`: `_ream_quote()` — string escaping
- `src/converters.py:66-95`: `_ream_scalar()` — cell to REAM scalar conversion
- `ream_xlsx/__init__.py`: Already has typed stubs for all public API names

### Established Patterns
- Phase 1 established: all config in `pyproject.toml`, tests in `tests/`, ruff + mypy strict
- Exception hierarchy already stubbed in `__init__.py`
- `ReamOptions` class exists but is empty — needs frozen dataclass implementation

### Integration Points
- `ream_xlsx/__init__.py` re-exports everything — internal modules feed into it
- `tests/test_package.py` already tests importability — new tests add behavior coverage
- openpyxl is the sole dependency for reading XLSX files

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-core-api*
*Context gathered: 2026-03-30*
