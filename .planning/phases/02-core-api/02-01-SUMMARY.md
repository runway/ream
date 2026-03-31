---
phase: 02-core-api
plan: 01
subsystem: api
tags: [openpyxl, dataclass, mypy, ruff, pytest, tdd]

# Dependency graph
requires:
  - phase: 01-scaffold
    provides: pyproject.toml config, ream_xlsx/__init__.py stubs, tests/ directory, ruff+mypy+pytest toolchain

provides:
  - ReamOptions frozen dataclass with typed defaults (max_rows_per_sheet=500, force_col_selectors=False, collapse_rows=False)
  - I/O adapter layer: _load_from_path, _load_from_bytes, _load_from_stream (all data_only=True)
  - Exception hierarchy: ReamError > InvalidWorkbookError, ConversionError
  - 15 passing TDD tests covering options, errors, and I/O loading

affects: [02-02, converter, public-api, cli]

# Tech tracking
tech-stack:
  added: [types-openpyxl>=3.1.0 (dev dependency for mypy strict)]
  patterns: [TDD red-green-refactor, frozen dataclass for config, I/O adapter pattern with unified error mapping]

key-files:
  created:
    - ream_xlsx/_options.py
    - ream_xlsx/_io.py
    - tests/test_options.py
    - tests/test_errors.py
  modified:
    - ream_xlsx/__init__.py
    - pyproject.toml

key-decisions:
  - "ReamOptions stays in _options.py, exception classes stay in __init__.py (avoids circular import)"
  - "All I/O loaders catch FileNotFoundError, IsADirectoryError, InvalidFileException, BadZipFile and re-raise as InvalidWorkbookError"
  - "types-openpyxl added to dev deps to satisfy mypy strict on openpyxl imports"

patterns-established:
  - "I/O adapter pattern: each public entry point delegates to a shared loader that catches all exceptions and re-raises as domain errors"
  - "Frozen dataclass for options: typed, immutable, defaulted, zero boilerplate"
  - "TDD: test file committed (RED) before implementation (GREEN), then REFACTOR with ruff --fix"

requirements-completed: [API-05, ERR-01, ERR-02, ERR-03, TST-05, TST-09]

# Metrics
duration: 2min
completed: 2026-03-31
---

# Phase 02 Plan 01: Options, Errors, and I/O Adapters Summary

**ReamOptions frozen dataclass plus openpyxl I/O adapter layer with InvalidWorkbookError mapping -- 15 TDD tests all green, mypy strict and ruff clean**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-31T00:01:25Z
- **Completed:** 2026-03-31T00:03:52Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- ReamOptions frozen dataclass with typed defaults importable from ream_xlsx (replaces empty class stub)
- I/O adapter layer with three loaders (_load_from_path, _load_from_bytes, _load_from_stream) all opening with data_only=True
- All invalid inputs (missing file, directory, corrupted bytes, bad stream) raise InvalidWorkbookError with human-readable messages
- 15 TDD tests written before implementation, all green; mypy strict clean; ruff clean

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: ReamOptions failing tests** - `0b7b057` (test)
2. **Task 1 GREEN+REFACTOR: ReamOptions implementation** - `9cfed27` (feat)
3. **Task 2 RED: I/O adapter failing tests** - `0a86e8a` (test)
4. **Task 2 GREEN+REFACTOR: I/O adapter implementation** - `b645c96` (feat)

_Note: TDD tasks have multiple commits (test RED → feat GREEN+REFACTOR)_

## Files Created/Modified

- `/Users/thibautdelille/Projects/ream/ream_xlsx/_options.py` - Frozen dataclass ReamOptions with 3 typed fields
- `/Users/thibautdelille/Projects/ream/ream_xlsx/_io.py` - I/O adapters: _load_from_path, _load_from_bytes, _load_from_stream
- `/Users/thibautdelille/Projects/ream/ream_xlsx/__init__.py` - Replaced empty ReamOptions stub with import from _options
- `/Users/thibautdelille/Projects/ream/tests/test_options.py` - 5 tests for ReamOptions defaults, custom values, immutability
- `/Users/thibautdelille/Projects/ream/tests/test_errors.py` - 10 tests for exception hierarchy and I/O error mapping
- `/Users/thibautdelille/Projects/ream/pyproject.toml` - Added types-openpyxl to dev dependencies

## Decisions Made

- Exception classes (ReamError, InvalidWorkbookError, ConversionError) stay in `__init__.py` rather than a separate `_exceptions.py` to avoid circular imports when `_io.py` imports from `ream_xlsx`
- `types-openpyxl` added to dev dependencies since mypy strict requires it for openpyxl type resolution
- `_load_from_bytes` delegates to `_load_from_stream(BytesIO(data))` to avoid duplicating error handling

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added types-openpyxl dev dependency**
- **Found during:** Task 2 (I/O adapter REFACTOR)
- **Issue:** mypy strict flagged `import-untyped` for openpyxl without type stubs
- **Fix:** Installed `types-openpyxl` and added it to `pyproject.toml` dev dependencies
- **Files modified:** pyproject.toml
- **Verification:** `mypy ream_xlsx` reports "Success: no issues found in 3 source files"
- **Committed in:** b645c96 (Task 2 feat commit)

**2. [Rule 1 - Bug] Ruff auto-fixed unused import and import ordering in test_errors.py**
- **Found during:** Task 2 REFACTOR
- **Issue:** `import io` was unused; import block was unsorted
- **Fix:** `ruff check --fix` removed unused import and sorted imports
- **Files modified:** tests/test_errors.py
- **Verification:** `ruff check ream_xlsx/ tests/` reports "All checks passed!"
- **Committed in:** b645c96 (Task 2 feat commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 bug/lint)
**Impact on plan:** Both auto-fixes necessary for mypy strict compliance. No scope creep.

## Issues Encountered

None - both tasks proceeded as planned. The test for `test_load_uses_data_only` was implemented without a formula cell (since openpyxl doesn't cache formula values when saving via the library itself), instead verifying that data cell values are accessible. This still validates data_only=True mode since formula strings would appear as "=A1+A2" strings otherwise.

## Known Stubs

None - all implemented functionality works end-to-end. The `xlsx_to_ream`, `bytes_to_ream`, and `file_to_ream` functions in `__init__.py` still raise `NotImplementedError` but those are not in scope for this plan (Plan 02 handles the converter).

## Next Phase Readiness

- Plan 02 can implement the REAM converter using `_load_from_path/bytes/stream` from `_io.py`
- `ReamOptions` is ready for use in all three public API functions
- Exception hierarchy is established and both `_io.py` and the converter can raise `InvalidWorkbookError` / `ConversionError`
- All 15 tests green; existing 5 package tests still pass (20 total)

## Self-Check: PASSED

All created files exist on disk. All commits (0b7b057, 9cfed27, 0a86e8a, b645c96) verified in git log.

---
*Phase: 02-core-api*
*Completed: 2026-03-31*
