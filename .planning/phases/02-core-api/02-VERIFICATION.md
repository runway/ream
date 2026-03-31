---
phase: 02-core-api
verified: 2026-03-30T00:00:00Z
status: passed
score: 13/13 must-haves verified
re_verification: false
gaps: []
human_verification: []
---

# Phase 2: Core API Verification Report

**Phase Goal:** Any Python caller can convert an XLSX file, bytes payload, or file stream to REAM text with typed options and clean exceptions
**Verified:** 2026-03-30
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                          | Status     | Evidence                                                                                         |
|----|-----------------------------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------------------|
| 1  | `ReamOptions()` returns frozen dataclass with max_rows_per_sheet=500, force_col_selectors=False, collapse_rows=False | VERIFIED | `_options.py` lines 8-14: `@dataclass(frozen=True)`, fields with correct defaults; test_options.py::test_ream_options_defaults PASSED |
| 2  | `ReamOptions` fields cannot be mutated after creation (FrozenInstanceError)                   | VERIFIED   | test_options.py::test_ream_options_is_frozen raises `dataclasses.FrozenInstanceError` — PASSED  |
| 3  | `ReamOptions(max_rows_per_sheet=10)` is accepted and stores the custom value                  | VERIFIED   | test_options.py::test_ream_options_custom_values and test_ream_options_partial_override — PASSED |
| 4  | `InvalidWorkbookError` and `ConversionError` are subclasses of `ReamError`                   | VERIFIED   | `_exceptions.py` lines 11-20: class hierarchy correct; test_errors.py::test_error_subclass_hierarchy PASSED |
| 5  | Loading a missing file path raises `InvalidWorkbookError`                                    | VERIFIED   | `_io.py` lines 33-34: `FileNotFoundError` caught and re-raised; test_errors.py::test_missing_file_raises_invalid_workbook_error PASSED |
| 6  | Loading corrupted bytes raises `InvalidWorkbookError`                                        | VERIFIED   | `_io.py` lines 39-40 + stream handler: `BadZipFile` caught; test_errors.py::test_corrupted_bytes_raises_invalid_workbook_error PASSED |
| 7  | Loading a non-XLSX file raises `InvalidWorkbookError`                                        | VERIFIED   | `_io.py` lines 37-38: `InvalidFileException` caught; test_errors.py::test_corrupted_stream_raises_invalid_workbook_error PASSED |
| 8  | `xlsx_to_ream('workbook.xlsx')` returns a non-empty string starting with `#!REAM`            | VERIFIED   | `__init__.py` lines 38-45: calls `_load_from_path` + `_xlsx_to_ream_impl`; test_api.py::test_xlsx_to_ream_returns_ream_string PASSED |
| 9  | `bytes_to_ream(data)` produces output identical to `xlsx_to_ream` for the same workbook      | VERIFIED   | test_api.py::test_bytes_to_ream_matches_path PASSED                                             |
| 10 | `file_to_ream(stream)` produces output identical to `xlsx_to_ream` for the same workbook     | VERIFIED   | test_api.py::test_file_to_ream_matches_path PASSED                                              |
| 11 | `xlsx_to_ream` accepts both `str` and `pathlib.Path` arguments                               | VERIFIED   | `__init__.py` line 24: `path: str \| Path`; `_io.py` line 30: `path = Path(path)`; test_api.py::test_xlsx_to_ream_accepts_path_object PASSED |
| 12 | Calling `xlsx_to_ream` twice on the same file returns byte-for-byte identical output         | VERIFIED   | test_api.py::test_output_is_deterministic PASSED                                                |
| 13 | `ReamOptions` fields (max_rows, collapse_rows, force_col_selectors) all affect output        | VERIFIED   | test_api.py::test_max_rows_per_sheet, test_collapse_rows_version, test_force_col_selectors — all PASSED |

**Score:** 13/13 truths verified

### Required Artifacts

| Artifact                     | Expected                                          | Status   | Details                                                                                                           |
|------------------------------|---------------------------------------------------|----------|-------------------------------------------------------------------------------------------------------------------|
| `ream_xlsx/_options.py`      | ReamOptions frozen dataclass with 3 typed fields  | VERIFIED | 15 lines; `@dataclass(frozen=True)` present; correct fields and defaults                                         |
| `ream_xlsx/_io.py`           | I/O adapters: _load_from_path, _load_from_bytes, _load_from_stream | VERIFIED | 80 lines; all three functions defined; all use `data_only=True`; comprehensive error mapping to `InvalidWorkbookError` |
| `ream_xlsx/_converter.py`    | Core REAM conversion logic with `_xlsx_to_ream_impl` | VERIFIED | 224 lines (>80 min); `_xlsx_to_ream_impl` present; 4 helpers ported verbatim from `src/converters.py`          |
| `ream_xlsx/_exceptions.py`   | Exception hierarchy (deviation from plan: extracted to break circular import) | VERIFIED | 21 lines; `ReamError`, `InvalidWorkbookError`, `ConversionError` all defined; `__init__.py` re-exports all three |
| `ream_xlsx/__init__.py`      | Public entry points wired to _io + _converter     | VERIFIED | 94 lines; exports `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`, `ReamOptions`, all 3 exception classes; `__all__` contains all 7 names |
| `tests/test_options.py`      | Tests for ReamOptions defaults and custom values  | VERIFIED | 48 lines (>20 min); 5 tests covering defaults, custom values, immutability, partial override, not-None check     |
| `tests/test_errors.py`       | Tests for exception hierarchy and error conditions | VERIFIED | 151 lines (>40 min); 10 tests covering hierarchy, missing file, directory, corrupted bytes/stream, valid loads, data_only mode |
| `tests/test_api.py`          | Tests for all 3 entry points, determinism, options effects | VERIFIED | 248 lines (>80 min); 16 tests covering all success criteria                                                      |

### Key Link Verification

| From                          | To                            | Via                                          | Status   | Details                                                                              |
|-------------------------------|-------------------------------|----------------------------------------------|----------|--------------------------------------------------------------------------------------|
| `ream_xlsx/_io.py`            | `ream_xlsx/_exceptions.py`    | imports `InvalidWorkbookError`               | VERIFIED | `_io.py:14`: `from ream_xlsx._exceptions import InvalidWorkbookError` (plan said `__init__.py` but `_exceptions.py` is the correct fix for circular import) |
| `ream_xlsx/__init__.py`       | `ream_xlsx/_options.py`       | re-exports `ReamOptions`                     | VERIFIED | `__init__.py:11`: `from ream_xlsx._options import ReamOptions`                      |
| `ream_xlsx/__init__.py`       | `ream_xlsx/_converter.py`     | imports `_xlsx_to_ream_impl`                 | VERIFIED | `__init__.py:8`: `from ream_xlsx._converter import _xlsx_to_ream_impl`              |
| `ream_xlsx/__init__.py`       | `ream_xlsx/_io.py`            | imports `_load_from_path, _load_from_bytes, _load_from_stream` | VERIFIED | `__init__.py:10`: `from ream_xlsx._io import _load_from_bytes, _load_from_path, _load_from_stream` |
| `ream_xlsx/_converter.py`     | `ream_xlsx/_options.py`       | imports `ReamOptions`                        | VERIFIED | `_converter.py:12`: `from ream_xlsx._options import ReamOptions`                    |
| `ream_xlsx/__init__.py`       | `ream_xlsx/_exceptions.py`    | re-exports all 3 exception classes           | VERIFIED | `__init__.py:9`: `from ream_xlsx._exceptions import ConversionError, InvalidWorkbookError, ReamError` |

### Data-Flow Trace (Level 4)

| Artifact              | Data Variable | Source                         | Produces Real Data | Status   |
|-----------------------|---------------|--------------------------------|--------------------|----------|
| `__init__.py` (xlsx_to_ream) | `return` string | `_xlsx_to_ream_impl(wb, opts)` where `wb = _load_from_path(path)` | Yes — openpyxl reads real XLSX cells; `_xlsx_to_ream_impl` iterates `ws` rows and emits REAM text | FLOWING  |
| `__init__.py` (bytes_to_ream) | `return` string | `_xlsx_to_ream_impl(wb, opts)` where `wb = _load_from_bytes(data)` | Yes — same converter, real bytes deserialized | FLOWING  |
| `__init__.py` (file_to_ream)  | `return` string | `_xlsx_to_ream_impl(wb, opts)` where `wb = _load_from_stream(stream)` | Yes — same converter, real stream deserialized | FLOWING  |

All three public entry points flow real data from openpyxl workbook cells through `_xlsx_to_ream_impl` to REAM output. No hardcoded or stubbed returns.

### Behavioral Spot-Checks

| Behavior                              | Command                                                   | Result              | Status |
|---------------------------------------|-----------------------------------------------------------|---------------------|--------|
| All 36 tests pass                     | `.venv/bin/pytest tests/ -v`                              | 36 passed in 0.15s  | PASS   |
| ruff lint passes                      | `.venv/bin/ruff check .`                                  | All checks passed   | PASS   |
| mypy strict passes on 5 source files  | `.venv/bin/mypy ream_xlsx`                                | Success: no issues found in 5 source files | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description                                                                 | Status    | Evidence                                                                             |
|-------------|-------------|-----------------------------------------------------------------------------|-----------|--------------------------------------------------------------------------------------|
| API-01      | 02-02       | `xlsx_to_ream(path, options)` converts XLSX file path to REAM string        | SATISFIED | `__init__.py:24-45`; test_api.py::test_xlsx_to_ream_returns_ream_string PASSED       |
| API-02      | 02-02       | `bytes_to_ream(data, options)` converts XLSX bytes to REAM string           | SATISFIED | `__init__.py:48-69`; test_api.py::test_bytes_to_ream_returns_ream_string PASSED      |
| API-03      | 02-02       | `file_to_ream(stream, options)` converts file-like object to REAM string    | SATISFIED | `__init__.py:72-93`; test_api.py::test_file_to_ream_returns_ream_string PASSED       |
| API-04      | 02-02       | All path-based functions accept `str \| Path`                               | SATISFIED | `__init__.py:24`: `path: str \| Path`; `_io.py:30`: `path = Path(path)`; test_api.py::test_xlsx_to_ream_accepts_path_object PASSED |
| API-05      | 02-01       | `ReamOptions` frozen dataclass with `max_rows_per_sheet`, `force_col_selectors`, `collapse_rows` | SATISFIED | `_options.py:8-14`; test_options.py all 5 tests PASSED |
| API-06      | 02-02       | Default options produce deterministic output for the same workbook          | SATISFIED | test_api.py::test_output_is_deterministic PASSED                                     |
| ERR-01      | 02-01       | `ReamError` base exception for all package errors                           | SATISFIED | `_exceptions.py:11`; `__init__.py:9` re-exports; test_errors.py::test_ream_error_hierarchy PASSED |
| ERR-02      | 02-01       | `InvalidWorkbookError` raised for non-XLSX or corrupted files               | SATISFIED | `_io.py:33-42` and `_io.py:74-79`; 4 error tests in test_errors.py PASSED           |
| ERR-03      | 02-01       | `ConversionError` raised for failures during conversion                     | SATISFIED | `__init__.py:44-45` wraps unexpected exceptions; test_api.py::test_conversion_error_on_failure PASSED |
| TST-02      | 02-02       | Tests for path-based conversion producing valid REAM output                 | SATISFIED | test_api.py::test_xlsx_to_ream_returns_ream_string, test_xlsx_to_ream_contains_sheet_header, test_xlsx_to_ream_contains_headers_directive, test_xlsx_to_ream_contains_data_rows — all PASSED |
| TST-03      | 02-02       | Tests for bytes-based conversion matching path-based output                 | SATISFIED | test_api.py::test_bytes_to_ream_matches_path PASSED                                  |
| TST-04      | 02-02       | Tests for file-like conversion matching path-based output                   | SATISFIED | test_api.py::test_file_to_ream_matches_path PASSED                                   |
| TST-05      | 02-01       | Tests for `ReamOptions` defaults and custom values                          | SATISFIED | tests/test_options.py: 5 tests PASSED                                                |
| TST-06      | 02-02       | Tests for deterministic output (same input twice → same output)             | SATISFIED | test_api.py::test_output_is_deterministic PASSED                                     |
| TST-09      | 02-01       | Regression tests for any bugs discovered during packaging                   | SATISFIED | test_errors.py::test_load_uses_data_only (data_only=True regression), test_errors.py::test_directory_path_raises_invalid_workbook_error PASSED |

**All 15 Phase 2 requirements: SATISFIED**

No orphaned requirements detected. All requirement IDs from both PLAN frontmatters account for all Phase 2 requirements listed in ROADMAP.md.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No TODO/FIXME comments, placeholder stubs, hardcoded empty returns, or console-log-only implementations found in any Phase 2 source files.

**Notable structural deviation (not a defect):** Plan 02-01 specified exception classes in `__init__.py`; Plan 02-02 auto-extracted them to `_exceptions.py` to break a circular import. This is an improvement — `__init__.py` re-exports all three names so the public interface is identical. `_io.py` now imports from `_exceptions.py` (line 14) rather than from `__init__.py` as Plan 02-01's key_link pattern specified. The functional outcome is equivalent.

### Human Verification Required

None. All observable behaviors are verified programmatically via the 36-test suite and static analysis.

### Gaps Summary

No gaps. All 13 must-have truths are verified, all 8 artifacts exist and are substantive and wired, all key links are confirmed, all 15 requirement IDs are satisfied, and the full test suite (36 tests) passes with ruff and mypy strict both clean.

---

_Verified: 2026-03-30_
_Verifier: Claude (gsd-verifier)_
