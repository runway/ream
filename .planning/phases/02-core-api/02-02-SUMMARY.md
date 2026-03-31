---
phase: 02-core-api
plan: 02
subsystem: api
tags: [openpyxl, converter, mypy, ruff, pytest, tdd, circular-import]

# Dependency graph
requires:
  - phase: 02-core-api
    plan: 01
    provides: ReamOptions, I/O adapters, exception hierarchy

provides:
  - _converter.py with _xlsx_to_ream_impl(wb, options) porting all REAM logic from src/converters.py
  - _exceptions.py breaking circular import between __init__.py and _io.py
  - Working xlsx_to_ream, bytes_to_ream, file_to_ream public entry points
  - 16 TDD tests covering all 3 entry points, options, determinism, multi-sheet, edge cases

affects: [03-cli, 04-docs, public-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [TDD red-green-refactor, exception module extraction to break circular import, I/O adapter + converter separation]

key-files:
  created:
    - ream_xlsx/_converter.py
    - ream_xlsx/_exceptions.py
    - tests/test_api.py
  modified:
    - ream_xlsx/__init__.py
    - ream_xlsx/_io.py

key-decisions:
  - "Exception classes extracted to _exceptions.py to break circular import: _io.py imports InvalidWorkbookError, __init__.py imports from _io.py -- _exceptions.py breaks the cycle; __init__.py re-exports all three exception classes"
  - "_xlsx_to_ream_impl receives already-loaded Workbook + ReamOptions instead of filepath + kwargs -- clean separation of I/O and conversion concerns"
  - "ConversionError test patches ream_xlsx._xlsx_to_ream_impl (the bound name in __init__.py), not ream_xlsx._converter._xlsx_to_ream_impl"

# Metrics
duration: 3min
completed: 2026-03-31
---

# Phase 02 Plan 02: REAM Converter and Public API Wiring Summary

**REAM conversion logic ported from src/converters.py into _converter.py with _xlsx_to_ream_impl(wb, options); all 3 public entry points wired in __init__.py; 36 tests green, mypy strict and ruff clean**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-31T00:05:58Z
- **Completed:** 2026-03-31T00:09:25Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Ported all REAM conversion helpers (`_cell_value_str`, `_needs_ream_quoting`, `_ream_quote`, `_ream_scalar`) verbatim from `src/converters.py`
- Created `_xlsx_to_ream_impl(wb: Workbook, options: ReamOptions) -> str` with full type annotations, porting the 120-line conversion function to accept a pre-loaded Workbook instead of a filepath
- All three public functions (`xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`) wired in `__init__.py` with proper error wrapping (unexpected exceptions become `ConversionError`)
- 16 TDD tests written before implementation, all green; total suite 36 tests; mypy strict clean; ruff clean

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: API failing tests** - `c4f6cbf` (test)
2. **Task 1 GREEN: _converter.py ported logic** - `bf9c460` (feat)
3. **Task 2: Wire entry points + fix circular import** - `72ba1b0` (feat)

_Note: TDD tasks had RED commit then GREEN commit. Task 2 included auto-fix for circular import deviation._

## Files Created/Modified

- `/Users/thibautdelille/Projects/ream/ream_xlsx/_converter.py` - Core REAM conversion logic with _xlsx_to_ream_impl; 4 helper functions ported verbatim
- `/Users/thibautdelille/Projects/ream/ream_xlsx/_exceptions.py` - Exception hierarchy extracted to break circular import; __init__.py re-exports from here
- `/Users/thibautdelille/Projects/ream/ream_xlsx/__init__.py` - Replaced NotImplementedError stubs with working implementations; imports wired
- `/Users/thibautdelille/Projects/ream/ream_xlsx/_io.py` - Updated to import InvalidWorkbookError from _exceptions.py instead of __init__.py
- `/Users/thibautdelille/Projects/ream/tests/test_api.py` - 16 TDD tests for full public API contract

## Decisions Made

- Exception classes extracted to `_exceptions.py` (auto-deviation, Rule 1 bug fix): the plan said "exception classes stay in __init__.py" but adding `_io.py` imports to `__init__.py` created a circular import. `_exceptions.py` breaks the cycle with no user-visible change -- `__init__.py` still re-exports all three classes.
- `_xlsx_to_ream_impl` receives an already-loaded `Workbook` and `ReamOptions` rather than a filepath + kwargs, achieving clean separation between I/O (handled by `_io.py`) and conversion (handled by `_converter.py`).
- `ConversionError` test mocks `ream_xlsx._xlsx_to_ream_impl` (the name bound in `__init__.py`) rather than `ream_xlsx._converter._xlsx_to_ream_impl` to intercept the call via the public module's namespace.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Circular import broke all tests on wiring**
- **Found during:** Task 2 (wiring __init__.py)
- **Issue:** Adding `from ream_xlsx._io import ...` to `__init__.py` created a circular import: `_io.py` imports `InvalidWorkbookError` from `ream_xlsx` (`__init__.py`), which was not yet initialized
- **Fix:** Created `ream_xlsx/_exceptions.py` with all three exception classes; changed `_io.py` to import from `_exceptions.py`; `__init__.py` now imports and re-exports from `_exceptions.py`
- **Files modified:** `ream_xlsx/_exceptions.py` (new), `ream_xlsx/_io.py`, `ream_xlsx/__init__.py`
- **Commit:** 72ba1b0

**2. [Rule 1 - Bug] Ruff E741 ambiguous variable name `l` in test comprehensions**
- **Found during:** Task 2 REFACTOR (ruff check)
- **Issue:** List comprehensions used `l` as loop variable (ambiguous with `1` and `I`)
- **Fix:** Renamed to `ln` in both occurrences in test_api.py
- **Files modified:** tests/test_api.py
- **Commit:** 72ba1b0

---

**Total deviations:** 2 auto-fixed (both Rule 1 bugs)
**Impact on plan:** The circular import fix required adding _exceptions.py (not in original plan). No scope creep -- exceptions are still importable from ream_xlsx as before.

## Issues Encountered

The `test_conversion_error_on_failure` test initially failed because it patched `ream_xlsx._converter._xlsx_to_ream_impl` instead of `ream_xlsx._xlsx_to_ream_impl`. Once `__init__.py` imports `_xlsx_to_ream_impl` with a direct import (not a lazy lookup), you must patch the name in the importing module's namespace to intercept it.

## Known Stubs

None - all three public functions are fully implemented and return REAM text.

## Next Phase Readiness

- Public API is complete and tested: `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream` all return correct REAM text
- `ReamOptions` (max_rows_per_sheet, collapse_rows, force_col_selectors) all affect output correctly
- Exception hierarchy is consistent: `InvalidWorkbookError` for I/O failures, `ConversionError` for conversion failures
- Phase 03 (CLI) can import directly from `ream_xlsx` -- all 7 exported names available
- All 36 tests green; mypy strict clean; ruff clean

## Self-Check: PASSED

All created files exist on disk. All commits (c4f6cbf, bf9c460, 72ba1b0) verified in git log.

---
*Phase: 02-core-api*
*Completed: 2026-03-31*
