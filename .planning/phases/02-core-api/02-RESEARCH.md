# Phase 2: Core API - Research

**Researched:** 2026-03-30
**Domain:** Python library API implementation — porting XLSX-to-REAM conversion logic, typed options dataclass, exception hierarchy, TDD test suite
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Porting strategy**
- Copy and refactor the core logic from `src/converters.py` into `ream_xlsx/` as internal module(s)
- `src/converters.py` must remain untouched (locked decision from project setup) — no imports from it
- Helper functions (`_ream_scalar`, `_ream_quote`, `_needs_ream_quoting`, `_cell_value_str`) come along with the core logic
- Internal modules are private (prefixed with `_` or kept out of `__all__`)

**ReamOptions design**
- Frozen dataclass with default values matching current `src/converters.py` behavior:
  - `max_rows_per_sheet: int = 500`
  - `force_col_selectors: bool = False`
  - `collapse_rows: bool = False`
- All three public functions accept `options: ReamOptions | None = None` — `None` means use defaults

**Wire version control**
- Auto-derived from `collapse_rows`: version 11 if `collapse_rows=True`, version 9 otherwise
- Not user-controllable — this matches current `src/converters.py` behavior exactly
- Version header always appears in output (`#!REAM 9` or `#!REAM 11`)

**Error handling**
- `InvalidWorkbookError`: raised for missing files, non-XLSX files, corrupted/unreadable payloads, password-protected files
- `ConversionError`: raised for failures during conversion (e.g., openpyxl internal errors during cell reading)
- Both are subclasses of `ReamError`
- Error messages should be human-readable and include the cause

**Entry point routing**
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | `xlsx_to_ream(path, options)` converts XLSX file path to REAM string | Path-based entry point; `_load_from_path` wraps `openpyxl.load_workbook` then calls shared impl |
| API-02 | `bytes_to_ream(data, options)` converts XLSX bytes to REAM string | `io.BytesIO(data)` wraps bytes; same shared impl |
| API-03 | `file_to_ream(stream, options)` converts file-like object to REAM string | Stream passed directly to `openpyxl.load_workbook`; same shared impl |
| API-04 | All path-based functions accept `str \| Path` | `Path` imported from `pathlib`; convert to `str` before passing to openpyxl or pass directly (openpyxl accepts both) |
| API-05 | `ReamOptions` frozen dataclass with `max_rows_per_sheet`, `force_col_selectors`, `collapse_rows` | `@dataclass(frozen=True)` with typed fields and explicit defaults matching `src/converters.py` |
| API-06 | Default options produce deterministic output for the same workbook | openpyxl row/col iteration is deterministic; dict ordering is guaranteed in Python 3.7+; no random state in conversion logic |
| ERR-01 | `ReamError` base exception for all package errors | Stubbed in `ream_xlsx/__init__.py`; needs docstring and proper inheritance chain |
| ERR-02 | `InvalidWorkbookError` raised for non-XLSX or corrupted files | Catch `FileNotFoundError`, `openpyxl.utils.exceptions.InvalidFileException`, `zipfile.BadZipFile`, and `IsADirectoryError` in `_load_from_*` functions |
| ERR-03 | `ConversionError` raised for failures during conversion | Catch broad `Exception` during `_xlsx_to_ream_impl` and re-raise as `ConversionError` |
| TST-02 | Tests for path-based conversion producing valid REAM output | Create in-memory XLSX with openpyxl in fixture; call `xlsx_to_ream`; assert starts with `#!REAM` |
| TST-03 | Tests for bytes-based conversion matching path-based output | Write fixture XLSX to `BytesIO`; compare `bytes_to_ream` output to `xlsx_to_ream` output byte-for-byte |
| TST-04 | Tests for file-like conversion matching path-based output | Open fixture XLSX as file stream; compare `file_to_ream` output to `xlsx_to_ream` output |
| TST-05 | Tests for `ReamOptions` defaults and custom values | Assert `ReamOptions()` fields match expected defaults; call `xlsx_to_ream` with `ReamOptions(max_rows_per_sheet=1)` and verify truncation |
| TST-06 | Tests for deterministic output (same input twice → same output) | Call `xlsx_to_ream` twice on the same path; assert outputs are identical |
| TST-09 | Regression tests for any bugs discovered during packaging | Placeholder test file; can be empty or contain a smoke test checking basic multi-sheet output format |
</phase_requirements>

---

## Summary

Phase 2 is a well-scoped porting task with no architectural uncertainty. The complete REAM conversion logic already exists in `src/converters.py` (lines 669–805 for the main function, lines 15–95 for helpers). The work is: extract that logic into private internal module(s), wire three public entry points through a shared internal function, implement `ReamOptions` as a frozen dataclass, implement the exception hierarchy, and write tests before implementation (TDD).

The key architectural choice (at Claude's discretion) is whether to split into `_converter.py` + `_options.py` + `_io.py` or use a single `_converter.py`. The prior architecture research recommended the three-file split; that is the right call here — it keeps I/O error handling isolated from conversion logic, makes the module boundaries testable independently, and matches the pattern established by the Phase 1 architecture research.

The error handling boundary is the most nuanced part: openpyxl raises different exception types depending on what goes wrong (`InvalidFileException` for format errors, `zipfile.BadZipFile` for corrupted files, `FileNotFoundError` for missing paths). All of these must be caught at the I/O boundary and re-raised as `InvalidWorkbookError`. Exceptions that escape openpyxl during the actual cell-reading conversion phase should become `ConversionError`.

**Primary recommendation:** Three internal modules (`_options.py`, `_io.py`, `_converter.py`), all imported and re-exported from `ream_xlsx/__init__.py`. Write tests first using in-memory openpyxl workbooks as fixtures (no disk I/O for fixtures). Implement in order: `_options.py` → `_converter.py` → `_io.py` → `__init__.py` wiring.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | >=3.1.0 (already in pyproject.toml) | XLSX reading | Already the sole runtime dep; `load_workbook(data_only=True)` is the correct mode |
| dataclasses | stdlib (Python 3.7+) | `ReamOptions` frozen dataclass | `@dataclass(frozen=True)` is the idiomatic Python way for immutable option structs |
| io.BytesIO | stdlib | Bytes-to-stream adapter for `bytes_to_ream` | Standard way to treat bytes as a file-like object |
| pathlib.Path | stdlib | Accept `str \| Path` for path arguments | Already imported in `ream_xlsx/__init__.py` |
| zipfile | stdlib | Catch `BadZipFile` in error handling | openpyxl xlsx reading uses zipfile internally; corrupted files raise this |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.0.0 (dev dep) | Test runner | All new tests; already configured in pyproject.toml |
| openpyxl.Workbook | same as above | Create in-memory test fixtures | Use `openpyxl.Workbook()` to build minimal XLSX structures for test fixtures without disk I/O |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@dataclass(frozen=True)` | `NamedTuple` | NamedTuple is positional-only; frozen dataclass has named fields with defaults and is more readable |
| `@dataclass(frozen=True)` | attrs / pydantic | Both add dependencies; frozen dataclass is zero-dependency stdlib |
| In-memory openpyxl fixtures | Committing .xlsx files to tests/fixtures/ | Disk fixtures are opaque binary blobs; in-memory creation is readable, maintainable, and dependency-free |

**Installation:** No new packages needed. openpyxl, pytest, ruff, mypy are all already in `pyproject.toml`.

---

## Architecture Patterns

### Recommended Project Structure

```
ream_xlsx/
├── __init__.py          # public API — already exists; needs implementation wiring
├── py.typed             # already exists
├── _options.py          # NEW: ReamOptions frozen dataclass
├── _io.py               # NEW: input adapters (path / bytes / stream → Workbook + error mapping)
└── _converter.py        # NEW: all REAM conversion logic (ported from src/converters.py)

tests/
├── __init__.py          # already exists
├── test_package.py      # already exists (TST-01)
├── test_api.py          # NEW: TST-02, TST-03, TST-04, TST-06 (conversion correctness + determinism)
├── test_options.py      # NEW: TST-05 (ReamOptions fields, defaults, custom values)
└── test_errors.py       # NEW: TST-09 + ERR-02/ERR-03 (error conditions)
```

### Pattern 1: Frozen Dataclass for Options

**What:** `ReamOptions` is a frozen (`@dataclass(frozen=True)`) dataclass. Frozen means instances are immutable after creation — setting a field after construction raises `FrozenInstanceError`. This matches the user decision and prevents accidental mutation of shared options objects.

**When to use:** Any configuration/options struct that should be immutable after creation.

**Example:**
```python
# ream_xlsx/_options.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ReamOptions:
    """Options controlling XLSX-to-REAM conversion behaviour.

    Attributes:
        max_rows_per_sheet: Maximum data rows to emit per sheet before truncation.
            Default 500 matches src/converters.py behaviour.
        force_col_selectors: If True, prefix every cell with its column letter
            (e.g. ``A=Revenue``). Default False uses sparse column prefixes only.
        collapse_rows: If True, vertically merge consecutive rows with identical
            content (wire version #!REAM 11). Default False emits one row per
            record (wire version #!REAM 9).
    """

    max_rows_per_sheet: int = 500
    force_col_selectors: bool = False
    collapse_rows: bool = False
```

### Pattern 2: I/O Adapter Layer with Error Mapping

**What:** `_io.py` contains thin functions that normalize the three input types (path, bytes, stream) into an openpyxl `Workbook`. All openpyxl exceptions are caught here and re-raised as `InvalidWorkbookError`. No conversion logic in this module.

**When to use:** Any time you have multiple input formats funneling into the same processing logic.

**Example:**
```python
# ream_xlsx/_io.py
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import IO

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.workbook.workbook import Workbook

from ream_xlsx._exceptions import InvalidWorkbookError


def _load_from_path(path: str | Path) -> Workbook:
    """Load an openpyxl Workbook from a file path.

    Raises:
        InvalidWorkbookError: If the file does not exist, is not a valid XLSX,
            or cannot be read.
    """
    try:
        return openpyxl.load_workbook(path, data_only=True)
    except FileNotFoundError as exc:
        raise InvalidWorkbookError(f"File not found: {path}") from exc
    except (InvalidFileException, zipfile.BadZipFile) as exc:
        raise InvalidWorkbookError(f"Not a valid XLSX workbook: {path}") from exc
    except Exception as exc:
        raise InvalidWorkbookError(f"Cannot open workbook: {path}: {exc}") from exc


def _load_from_bytes(data: bytes) -> Workbook:
    """Load an openpyxl Workbook from raw XLSX bytes."""
    try:
        return openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    except (InvalidFileException, zipfile.BadZipFile) as exc:
        raise InvalidWorkbookError(f"Bytes do not contain a valid XLSX workbook: {exc}") from exc
    except Exception as exc:
        raise InvalidWorkbookError(f"Cannot parse bytes as XLSX workbook: {exc}") from exc


def _load_from_stream(stream: IO[bytes]) -> Workbook:
    """Load an openpyxl Workbook from a binary file-like object."""
    try:
        return openpyxl.load_workbook(stream, data_only=True)
    except (InvalidFileException, zipfile.BadZipFile) as exc:
        raise InvalidWorkbookError(f"Stream does not contain a valid XLSX workbook: {exc}") from exc
    except Exception as exc:
        raise InvalidWorkbookError(f"Cannot parse stream as XLSX workbook: {exc}") from exc
```

### Pattern 3: Single Internal Conversion Function

**What:** `_converter.py` exposes one function `_xlsx_to_ream_impl(wb, options)` that accepts an openpyxl `Workbook` and a `ReamOptions` and returns the REAM string. All helper functions (`_ream_scalar`, `_ream_quote`, `_needs_ream_quoting`, `_cell_value_str`) are private to this module.

**When to use:** When all three public entry points (path, bytes, stream) must produce identical output — a single implementation guarantees this.

**Example:**
```python
# ream_xlsx/_converter.py  (top structure only)
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from openpyxl.utils import get_column_letter
from openpyxl.workbook.workbook import Workbook

from ream_xlsx._options import ReamOptions


def _cell_value_str(val: Any) -> str: ...   # ported verbatim
def _needs_ream_quoting(s: str) -> bool: ...  # ported verbatim
def _ream_quote(s: str) -> str: ...           # ported verbatim
def _ream_scalar(val: Any) -> str: ...        # ported verbatim


def _xlsx_to_ream_impl(wb: Workbook, options: ReamOptions) -> str:
    """Convert an already-loaded openpyxl Workbook to REAM text.

    This is the single implementation all three public entry points converge on.
    """
    version = "11" if options.collapse_rows else "9"
    lines = [f"#!REAM {version}"]
    # ... ported logic from src/converters.py:685-805
    return "\n".join(lines)
```

### Pattern 4: Public Entry Points as Thin Wrappers

**What:** The three public functions in `ream_xlsx/__init__.py` load the workbook via `_io.py`, then delegate to `_converter.py`. No conversion logic or error handling lives in `__init__.py`.

**Example:**
```python
# ream_xlsx/__init__.py (implementation wiring — replaces NotImplementedError stubs)
from ream_xlsx._options import ReamOptions
from ream_xlsx._io import _load_from_path, _load_from_bytes, _load_from_stream
from ream_xlsx._converter import _xlsx_to_ream_impl
from ream_xlsx._exceptions import ReamError, InvalidWorkbookError, ConversionError


def xlsx_to_ream(path: str | Path, options: ReamOptions | None = None) -> str:
    wb = _load_from_path(path)
    opts = options if options is not None else ReamOptions()
    try:
        return _xlsx_to_ream_impl(wb, opts)
    except (ReamError, NotImplementedError):
        raise
    except Exception as exc:
        raise ConversionError(f"Conversion failed: {exc}") from exc


def bytes_to_ream(data: bytes, options: ReamOptions | None = None) -> str:
    wb = _load_from_bytes(data)
    opts = options if options is not None else ReamOptions()
    try:
        return _xlsx_to_ream_impl(wb, opts)
    except (ReamError, NotImplementedError):
        raise
    except Exception as exc:
        raise ConversionError(f"Conversion failed: {exc}") from exc


def file_to_ream(stream: IO[bytes], options: ReamOptions | None = None) -> str:
    wb = _load_from_stream(stream)
    opts = options if options is not None else ReamOptions()
    try:
        return _xlsx_to_ream_impl(wb, opts)
    except (ReamError, NotImplementedError):
        raise
    except Exception as exc:
        raise ConversionError(f"Conversion failed: {exc}") from exc
```

### Pattern 5: In-Memory XLSX Fixtures for TDD

**What:** Tests create minimal XLSX workbooks in memory using `openpyxl.Workbook()` rather than committing binary `.xlsx` files to the repo. This produces readable, maintainable tests.

**Example:**
```python
# tests/test_api.py
import io
import openpyxl
import pytest
from ream_xlsx import xlsx_to_ream, bytes_to_ream, file_to_ream, ReamOptions


def _make_simple_workbook() -> openpyxl.Workbook:
    """Create a minimal XLSX workbook with one sheet and three rows."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["Name", "Value"])
    ws.append(["Alice", 42])
    ws.append(["Bob", 100])
    return wb


def _workbook_to_bytes(wb: openpyxl.Workbook) -> bytes:
    """Serialize an openpyxl workbook to XLSX bytes."""
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _workbook_to_path(wb: openpyxl.Workbook, tmp_path) -> str:
    """Write an openpyxl workbook to a temp file and return the path."""
    p = tmp_path / "test.xlsx"
    wb.save(str(p))
    return str(p)
```

### Anti-Patterns to Avoid

- **Conversion logic in `__init__.py`:** Keep `__init__.py` as pure wiring. All logic belongs in `_converter.py`.
- **Catching broad Exception at I/O boundary without re-raising as ReamError:** openpyxl can raise unexpected exceptions for edge-case files; always wrap and re-raise to keep callers from seeing openpyxl internals.
- **Passing `ReamOptions` fields individually to helpers:** Pass the full `options` object only to `_xlsx_to_ream_impl`; individual helper functions (`_ream_scalar`, etc.) should receive only the specific values they need to avoid hidden coupling.
- **Using `options.field` with mutable default inside dataclass:** All three fields are `int` and `bool` — immutable — so `@dataclass(frozen=True)` without `field()` is correct here.
- **Importing from `src/converters.py`:** The locked decision forbids this. Copy the helpers verbatim into `_converter.py`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reading XLSX binary format | Custom ZIP parser | `openpyxl.load_workbook` | XLSX is a ZIP of XML; openpyxl handles merged cells, types, encoding, shared strings, etc. |
| Bytes-to-file-object adapter | Custom wrapper class | `io.BytesIO(data)` | stdlib; zero overhead; already accepted by openpyxl |
| Options immutability | Manual `__setattr__` override | `@dataclass(frozen=True)` | stdlib handles all frozen semantics including `__hash__` |
| In-memory workbook for tests | Writing `.xlsx` fixture files | `openpyxl.Workbook()` | Cleaner, no binary blobs in git, fixtures are self-documenting code |

**Key insight:** The heavy lifting (XLSX parsing, cell type normalization) is entirely openpyxl's responsibility. The conversion logic that remains is pure string manipulation — no custom parsing needed.

---

## Common Pitfalls

### Pitfall 1: openpyxl Exception Types at the I/O Boundary

**What goes wrong:** `openpyxl.load_workbook` raises different exception types depending on what failed:
- Missing file path → Python's built-in `FileNotFoundError`
- Non-XLSX file (e.g. `.xls`, `.csv`) → `openpyxl.utils.exceptions.InvalidFileException`
- Corrupted XLSX (truncated ZIP) → `zipfile.BadZipFile` from Python's stdlib `zipfile` module
- Directory passed as path → `IsADirectoryError` (on Unix) or `PermissionError` (on Windows)
- Password-protected file → `openpyxl` raises a generic exception (may vary by version)

**Why it happens:** openpyxl doesn't unify these into a single exception hierarchy; they bubble up from wherever the failure occurred (stdlib, openpyxl internals).

**How to avoid:** Catch all of these at the `_load_from_*` boundary and re-raise as `InvalidWorkbookError`. Catch the broad `Exception` last as a fallback. Always include the original exception message in the `InvalidWorkbookError` message for debuggability.

**Warning signs:** Tests pass for `FileNotFoundError` but a corrupted bytes payload silently raises `BadZipFile` at the caller instead of `InvalidWorkbookError`.

### Pitfall 2: `data_only=True` Required for openpyxl

**What goes wrong:** Omitting `data_only=True` when calling `load_workbook` causes formula cells (e.g., `=SUM(A1:A3)`) to return `None` for their value instead of the computed result. The test workbook may not have formulas, but the spec requires data-only reading.

**Why it happens:** openpyxl defaults to returning formula strings, not computed values, unless `data_only=True` is passed.

**How to avoid:** Always pass `data_only=True` in all three `_load_from_*` functions. This matches what `src/converters.py` line 685 already does.

### Pitfall 3: Frozen Dataclass Cannot Have Mutable Default Field Values

**What goes wrong:** Using a mutable default (list, dict) in a frozen dataclass raises `ValueError: mutable default ... is not allowed: use default_factory`. Not a risk here since all three fields are `int` and `bool`, but worth noting for any future extension.

**How to avoid:** All three `ReamOptions` fields (`max_rows_per_sheet`, `force_col_selectors`, `collapse_rows`) are immutable scalars — direct defaults are fine.

### Pitfall 4: `ruff` and `mypy` Strict Violations When Porting Helpers

**What goes wrong:** `_cell_value_str`, `_ream_scalar` in `src/converters.py` use `Any` from `typing`. Under `mypy --strict`, all `Any` parameters require explicit `from typing import Any` and proper annotations. The helpers use `isinstance(val, (int, float))` which is fine, but `from typing import Any` must be present.

**Why it happens:** `src/converters.py` was research code not subject to mypy strict.

**How to avoid:** When porting helpers to `_converter.py`, add `from __future__ import annotations` at the top, ensure `from typing import Any` is imported, and verify `mypy ream_xlsx` passes after each module addition.

### Pitfall 5: `__init__.py` Currently Has Exception Classes — Must Relocate or Keep

**What goes wrong:** `ream_xlsx/__init__.py` currently defines `ReamError`, `InvalidWorkbookError`, and `ConversionError` directly. If these are moved to a `_exceptions.py` internal module, `__init__.py` must re-export them (they are in `__all__`). Moving them without maintaining the re-export breaks `from ream_xlsx import ReamError`.

**How to avoid:** Two valid approaches:
1. Keep exceptions in `__init__.py` (simpler — no extra module, no circular import risk)
2. Move to `_exceptions.py` and re-export from `__init__.py` (preferred for larger codebases)

For this phase, keeping exceptions in `__init__.py` is acceptable given the small scope. The planner should pick one and be consistent.

### Pitfall 6: `_xlsx_to_ream_impl` Returns Without Trailing Newline

**What goes wrong:** `src/converters.py` line 805 returns `"\n".join(lines)` — no trailing newline. This is the canonical output. Tests that check `result.endswith("\n")` will fail.

**How to avoid:** Port the exact `"\n".join(lines)` idiom. Do not add a trailing newline.

---

## Code Examples

Verified patterns from official sources and the existing `src/converters.py`:

### The Core Conversion Loop (from `src/converters.py:685-805`)

The existing implementation handles:
1. Wire version header (`#!REAM 9` or `#!REAM 11`)
2. Sheet headers (`#!SHEET name`)
3. Headers directive (`#!HEADERS 1:1`)
4. Row iteration with `max_rows_per_sheet` enforcement
5. `collapse_rows` path: horizontal segment merging, then vertical row-span merging
6. `force_col_selectors` path vs. sparse selector path
7. Cell serialization via `_ream_scalar`

The port is nearly verbatim — only the function signature changes (accepts `Workbook` instead of `filepath: str`).

```python
# Source: src/converters.py lines 669-805 (ported interface)
def _xlsx_to_ream_impl(wb: Workbook, options: ReamOptions) -> str:
    version = "11" if options.collapse_rows else "9"
    lines = [f"#!REAM {version}"]

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        safe_name = sheet_name
        if " " in sheet_name or "|" in sheet_name or '"' in sheet_name or "&" in sheet_name:
            safe_name = _ream_quote(sheet_name)
        lines.append(f"#!SHEET {safe_name}")
        # ... (rest of loop ported verbatim, replacing filepath load with wb)
    return "\n".join(lines)
```

### In-Memory XLSX for Tests (openpyxl API)

```python
# Source: openpyxl official docs — https://openpyxl.readthedocs.io/en/stable/tutorial.html
import io
import openpyxl

def _make_workbook_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(["Col1", "Col2"])
    ws.append(["hello", 42])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

### Catching openpyxl Exceptions

```python
# Source: openpyxl docs + Python stdlib zipfile docs
import zipfile
from openpyxl.utils.exceptions import InvalidFileException

try:
    wb = openpyxl.load_workbook(path, data_only=True)
except FileNotFoundError as exc:
    raise InvalidWorkbookError(f"File not found: {path}") from exc
except (InvalidFileException, zipfile.BadZipFile) as exc:
    raise InvalidWorkbookError(f"Not a valid XLSX workbook: {path}") from exc
except Exception as exc:
    raise InvalidWorkbookError(f"Cannot open workbook '{path}': {exc}") from exc
```

### Frozen Dataclass Pattern

```python
# Source: Python docs — https://docs.python.org/3/library/dataclasses.html
from dataclasses import dataclass

@dataclass(frozen=True)
class ReamOptions:
    max_rows_per_sheet: int = 500
    force_col_selectors: bool = False
    collapse_rows: bool = False
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat function with explicit kwargs | `ReamOptions` dataclass | This phase | Options are typed, introspectable, and immutable |
| `filepath: str` only | `path: str \| Path` | This phase (API-04) | Callers can pass `pathlib.Path` objects |
| Raises no exceptions — crashes on bad input | Typed exception hierarchy | This phase (ERR-01/02/03) | Callers can `except InvalidWorkbookError` |
| Single entry point | Three entry points (path/bytes/stream) | This phase (API-01/02/03) | Works with any input source |

---

## Open Questions

1. **Where to define exception classes: `__init__.py` vs. `_exceptions.py`**
   - What we know: Both work. Current stubs are in `__init__.py`.
   - What's unclear: Whether a separate `_exceptions.py` causes circular import if `_io.py` and `_converter.py` both import from it while `__init__.py` also imports from it.
   - Recommendation: Keep exceptions in `__init__.py` for Phase 2 (avoids circular import complexity). If the package grows, extract later.

2. **Whether to add `tests/__init__.py` — it already exists**
   - What we know: `tests/__init__.py` was created in Phase 1.
   - What's unclear: Whether new test files need `from __future__ import annotations` consistently.
   - Recommendation: Follow Phase 1's `test_package.py` style — include `from __future__ import annotations` at the top of every test file.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=8.0.0 |
| Config file | `pyproject.toml` under `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | `xlsx_to_ream(path)` returns REAM string | unit | `pytest tests/test_api.py::test_xlsx_to_ream_returns_ream_string -x` | ❌ Wave 0 |
| API-02 | `bytes_to_ream(data)` returns REAM string | unit | `pytest tests/test_api.py::test_bytes_to_ream_returns_ream_string -x` | ❌ Wave 0 |
| API-03 | `file_to_ream(stream)` returns REAM string | unit | `pytest tests/test_api.py::test_file_to_ream_returns_ream_string -x` | ❌ Wave 0 |
| API-04 | Path arg accepts `str` and `Path` | unit | `pytest tests/test_api.py::test_xlsx_to_ream_accepts_path_object -x` | ❌ Wave 0 |
| API-05 | `ReamOptions()` has correct defaults | unit | `pytest tests/test_options.py::test_ream_options_defaults -x` | ❌ Wave 0 |
| API-05 | `ReamOptions(max_rows_per_sheet=10)` limits rows | unit | `pytest tests/test_options.py::test_max_rows_per_sheet -x` | ❌ Wave 0 |
| API-06 | Same input twice → identical output | unit | `pytest tests/test_api.py::test_output_is_deterministic -x` | ❌ Wave 0 |
| ERR-01 | `ReamError` is base exception | unit | `pytest tests/test_errors.py::test_ream_error_hierarchy -x` | ❌ Wave 0 |
| ERR-02 | Missing file → `InvalidWorkbookError` | unit | `pytest tests/test_errors.py::test_missing_file_raises_invalid_workbook_error -x` | ❌ Wave 0 |
| ERR-02 | Corrupted bytes → `InvalidWorkbookError` | unit | `pytest tests/test_errors.py::test_corrupted_bytes_raises_invalid_workbook_error -x` | ❌ Wave 0 |
| ERR-03 | Both are subclasses of `ReamError` | unit | `pytest tests/test_errors.py::test_error_subclass_hierarchy -x` | ❌ Wave 0 |
| TST-02 | Path conversion returns valid REAM | unit | `pytest tests/test_api.py -k "path" -x` | ❌ Wave 0 |
| TST-03 | Bytes output matches path output | unit | `pytest tests/test_api.py::test_bytes_to_ream_matches_path -x` | ❌ Wave 0 |
| TST-04 | File output matches path output | unit | `pytest tests/test_api.py::test_file_to_ream_matches_path -x` | ❌ Wave 0 |
| TST-05 | Options defaults and custom values | unit | `pytest tests/test_options.py -x` | ❌ Wave 0 |
| TST-06 | Deterministic output | unit | `pytest tests/test_api.py::test_output_is_deterministic -x` | ❌ Wave 0 |
| TST-09 | Regression / smoke | unit | `pytest tests/test_errors.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v && ruff check . && mypy ream_xlsx`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_api.py` — covers API-01, API-02, API-03, API-04, TST-02, TST-03, TST-04, TST-06
- [ ] `tests/test_options.py` — covers API-05, TST-05
- [ ] `tests/test_errors.py` — covers ERR-01, ERR-02, ERR-03, TST-09
- [ ] `ream_xlsx/_options.py` — `ReamOptions` frozen dataclass
- [ ] `ream_xlsx/_io.py` — I/O adapters + error mapping
- [ ] `ream_xlsx/_converter.py` — ported conversion logic

---

## Sources

### Primary (HIGH confidence)

- `src/converters.py` lines 669–805 — the complete REAM conversion logic to port
- `src/converters.py` lines 15–95 — helper functions to port verbatim
- `ream_xlsx/__init__.py` — existing stubs and exception classes to wire up
- `pyproject.toml` — confirmed tool config (ruff line-length=120, mypy strict, pytest testpaths=tests)
- [openpyxl exceptions module — openpyxl 3.1.4 docs](https://openpyxl.readthedocs.io/en/stable/api/openpyxl.utils.exceptions.html) — verified `InvalidFileException` exists
- [Python dataclasses official docs](https://docs.python.org/3/library/dataclasses.html) — `frozen=True` behavior

### Secondary (MEDIUM confidence)

- [openpyxl BadZipFile error handling — Woteq Zone](https://woteq.com/how-to-troubleshoot-common-openpyxl-errors-like-badzipfile-and-valueerror/) — cross-verified that corrupted XLSX raises `zipfile.BadZipFile`
- Prior phase architecture research (`.planning/research/ARCHITECTURE.md`) — three-module split pattern

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are stdlib or already in pyproject.toml; no new dependencies needed
- Architecture: HIGH — locked decisions from CONTEXT.md plus prior architecture research; patterns are well-established
- Error handling: HIGH — openpyxl exception types verified against official docs and community sources
- Pitfalls: HIGH — porting pitfalls derived from direct code inspection of `src/converters.py` and project constraints

**Research date:** 2026-03-30
**Valid until:** 2026-06-30 (stable stdlib + openpyxl; unlikely to change)
