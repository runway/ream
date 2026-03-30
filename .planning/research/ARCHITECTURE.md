# Architecture Research

**Domain:** Python library package — XLSX-to-REAM converter
**Researched:** 2026-03-30
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entry Layer                               │
├──────────────────────────┬──────────────────────────────────────┤
│  ream/                   │                                      │
│  __init__.py             │  ream/__main__.py                    │
│  (public API surface)    │  (CLI entrypoint: python -m ream)    │
│                          │                                      │
│  xlsx_to_ream()          │  ream/cli.py                         │
│  bytes_to_ream()         │  (argparse wiring, flag→options)     │
│  file_to_ream()          │                                      │
│  ReamOptions             │                                      │
└──────────┬───────────────┴──────────────┬───────────────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Core Conversion Layer                        │
│  ream/_converter.py                                               │
│  (all conversion logic, private — mirrors src/converters.py)      │
│                                                                   │
│  _xlsx_to_ream_impl(workbook, options) → str                      │
│  _ream_scalar(), _needs_ream_quoting(), _ream_quote(), etc.       │
└──────────────────────────────────┬───────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                      I/O Adapters Layer                           │
│  ream/_io.py                                                      │
│  (file path / bytes / stream → openpyxl Workbook)                 │
│                                                                   │
│  _load_from_path(path) → Workbook                                 │
│  _load_from_bytes(data) → Workbook                                │
│  _load_from_stream(stream) → Workbook                             │
└──────────────────────────────────┬───────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                        openpyxl                                   │
│  (sole external dependency for package core)                      │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                   Research / Eval (NOT in package)                │
│  src/converters.py        (legacy — benchmark scripts use this)   │
│  run_eval.py              (evaluation harness)                    │
│  scoring.py               (scoring logic)                         │
│  requirements.txt         (research deps: pandas, openai, etc.)   │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `ream/__init__.py` | Define public API surface: what users import | Re-exports from internal modules; sets `__all__` |
| `ream/_converter.py` | All REAM conversion logic (private) | Pure functions operating on openpyxl Workbook |
| `ream/_io.py` | Normalize inputs (path/bytes/stream → Workbook) | Thin wrappers that call `openpyxl.load_workbook` |
| `ream/cli.py` | Argument parsing and output routing | `argparse` wiring; maps flags to `ReamOptions` |
| `ream/__main__.py` | Enable `python -m ream` invocation | Single line: `from ream.cli import main; main()` |
| `ream/_options.py` | `ReamOptions` dataclass definition | `@dataclass` with typed fields and documented defaults |
| `src/converters.py` | Legacy research converter (must not break) | Untouched; benchmark scripts depend on it |

## Recommended Project Structure

```
ream/                          # installable package (src layout: lives alongside src/)
├── __init__.py                # public API — exports xlsx_to_ream, bytes_to_ream, file_to_ream, ReamOptions
├── __main__.py                # enables python -m ream
├── _options.py                # ReamOptions dataclass
├── _io.py                     # input adapters (path / bytes / stream → Workbook)
├── _converter.py              # all REAM conversion logic (private)
└── cli.py                     # argparse entrypoint, stdout/file output

src/                           # existing research code — unchanged
├── converters.py              # legacy converters (benchmark scripts import from here)
├── run_eval.py
├── scoring.py
└── ...

tests/                         # test suite (TDD — written before implementation)
├── test_api.py                # public API contract: xlsx_to_ream, bytes_to_ream, file_to_ream
├── test_options.py            # ReamOptions defaults and flag behavior
├── test_cli.py                # CLI flags, stdout output, file output, error handling
└── fixtures/                  # small XLSX files for determinism tests

pyproject.toml                 # package metadata, build system, console_scripts
requirements.txt               # research deps (pandas, openai, etc.) — unchanged
```

### Structure Rationale

- **`ream/` at project root (not under `src/`):** The repo already uses `src/` for research scripts. Placing the new package at `ream/` keeps it visually distinct from research code and avoids the confusing naming collision of `src/ream/` next to `src/converters.py`. This is a pragmatic flat-ish layout — acceptable because there is no risk of accidentally importing an uninstalled package (the package name `ream` does not shadow any stdlib module, and `pip install -e .` is always used in development).
- **`_` prefix on internal modules:** `_converter.py`, `_io.py`, `_options.py` — underscore prefix is the Python convention for "private, not part of public API." Users who import `from ream._converter import ...` are doing so at their own risk.
- **`cli.py` without underscore:** CLI is a first-class deliverable. Keeping it non-underscored signals it's a supported module for those who want to call `main()` programmatically.
- **`tests/` separate from package:** Tests do not ship with the package. pytest discovers them automatically.
- **`src/converters.py` untouched:** Backward compatibility constraint from PROJECT.md. Benchmark scripts continue to `from converters import ...` or `import converters` via their own path setup.

## Architectural Patterns

### Pattern 1: Thin Public API over Private Core

**What:** `__init__.py` exposes three user-facing functions that each accept different input types and delegate to `_io.py` + `_converter.py`. The public functions are wrappers, not logic containers.

**When to use:** Always — for a library package. Keeps internal refactoring invisible to callers.

**Trade-offs:** Slightly more indirection; enormous benefit for API stability.

**Example:**
```python
# ream/__init__.py
from ream._options import ReamOptions
from ream._io import _load_from_path, _load_from_bytes, _load_from_stream
from ream._converter import _xlsx_to_ream_impl

__all__ = ["xlsx_to_ream", "bytes_to_ream", "file_to_ream", "ReamOptions"]

def xlsx_to_ream(path: str, options: ReamOptions | None = None) -> str:
    wb = _load_from_path(path)
    return _xlsx_to_ream_impl(wb, options or ReamOptions())

def bytes_to_ream(data: bytes, options: ReamOptions | None = None) -> str:
    wb = _load_from_bytes(data)
    return _xlsx_to_ream_impl(wb, options or ReamOptions())

def file_to_ream(stream, options: ReamOptions | None = None) -> str:
    wb = _load_from_stream(stream)
    return _xlsx_to_ream_impl(wb, options or ReamOptions())
```

### Pattern 2: Options as a Dataclass (not ad-hoc kwargs)

**What:** All conversion settings live in a single `ReamOptions` dataclass with explicit defaults. Public functions accept `options: ReamOptions | None = None`.

**When to use:** When there are 3+ boolean/numeric options that may grow over time.

**Trade-offs:** Slightly more verbose for callers than keyword args; far more extensible and introspectable. Prevents the "boolean blindness" anti-pattern.

**Example:**
```python
# ream/_options.py
from dataclasses import dataclass, field

@dataclass
class ReamOptions:
    max_rows_per_sheet: int = 500
    force_col_selectors: bool = False
    collapse_rows: bool = False
```

Caller usage:
```python
from ream import xlsx_to_ream, ReamOptions

text = xlsx_to_ream("report.xlsx", ReamOptions(collapse_rows=True))
```

### Pattern 3: CLI maps flags → ReamOptions, delegates to library

**What:** `cli.py` is responsible only for arg parsing and output routing. It constructs a `ReamOptions` from flags and calls `xlsx_to_ream()`. No conversion logic in CLI.

**When to use:** Always — keeps CLI testable independently, and keeps library usable without CLI.

**Trade-offs:** None meaningful at this scale.

**Example:**
```python
# ream/cli.py
import argparse
import sys
from ream import xlsx_to_ream, ReamOptions

def main():
    parser = argparse.ArgumentParser(description="Convert XLSX to REAM format")
    parser.add_argument("input", help="Path to .xlsx file")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument("--max-rows", type=int, default=500)
    parser.add_argument("--force-col-selectors", action="store_true")
    parser.add_argument("--collapse-rows", action="store_true")
    args = parser.parse_args()

    options = ReamOptions(
        max_rows_per_sheet=args.max_rows,
        force_col_selectors=args.force_col_selectors,
        collapse_rows=args.collapse_rows,
    )
    result = xlsx_to_ream(args.input, options)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        sys.stdout.write(result)
```

## Data Flow

### Path-based API call

```
xlsx_to_ream("report.xlsx", ReamOptions(collapse_rows=True))
    ↓
ream/__init__.py: xlsx_to_ream()
    ↓
ream/_io.py: _load_from_path("report.xlsx")
    ↓
openpyxl.load_workbook("report.xlsx", data_only=True) → Workbook
    ↓
ream/_converter.py: _xlsx_to_ream_impl(workbook, options)
    ↓  (iterates sheets → rows → cells)
    ↓  applies quoting rules, col selectors, row collapse
    ↓
str (REAM text, "#!REAM 11\n#!SHEET ...\n...")
    ↓
returned to caller
```

### CLI flow

```
$ ream report.xlsx --collapse-rows -o out.ream
    ↓
ream/__main__.py → cli.main()
    ↓
argparse.parse_args() → args namespace
    ↓
ReamOptions(collapse_rows=True, ...)
    ↓
xlsx_to_ream(args.input, options)   [same path as Python API above]
    ↓
write to file or sys.stdout.write()
```

### Bytes / stream flow

```
bytes_to_ream(data, options)  OR  file_to_ream(stream, options)
    ↓
_load_from_bytes(data)           _load_from_stream(stream)
    ↓                                ↓
io.BytesIO(data) →              (passed directly)
openpyxl.load_workbook(BytesIO) openpyxl.load_workbook(stream)
    ↓                                ↓
              _xlsx_to_ream_impl(workbook, options)
                        ↓
                     str result
```

### Key Data Flows

1. **Input normalization:** Every public function normalizes its input type to an openpyxl `Workbook` before touching conversion logic. This means `_xlsx_to_ream_impl` only ever receives a `Workbook` — no path or bytes handling inside the converter.
2. **Options propagation:** `ReamOptions` is constructed once (at the API boundary or CLI boundary) and passed through. Internal helpers receive specific fields only — they do not receive the full options object to avoid hidden coupling.

## Suggested Build Order

Build in this order — each component depends only on what was built before it:

| Step | Component | Depends On | Notes |
|------|-----------|------------|-------|
| 1 | `ream/_options.py` | nothing | Pure dataclass, no imports |
| 2 | `ream/_converter.py` | `_options.py` | Port logic from `src/converters.py`; tests first |
| 3 | `ream/_io.py` | openpyxl | Thin wrappers; trivial but needed before public API |
| 4 | `ream/__init__.py` | all of above | Wire up public functions |
| 5 | `ream/cli.py` + `__main__.py` | `__init__.py` | Arg parsing layer |
| 6 | `pyproject.toml` | package exists | console_scripts, metadata |
| 7 | `tests/` | everything | TDD: tests are written per-step above, not all at the end |

## Anti-Patterns

### Anti-Pattern 1: Conversion logic in `__init__.py`

**What people do:** Dump all implementation directly in `__init__.py` to avoid "extra files."

**Why it's wrong:** `__init__.py` is executed on every `import ream`, making it slow to import. Mixing public API declaration with implementation logic makes refactoring fragile. It is hard to test internal helpers in isolation.

**Do this instead:** Keep `__init__.py` as a pure re-export surface. All logic lives in `_converter.py`.

### Anti-Pattern 2: Exposing openpyxl types in the public API

**What people do:** Return or accept `openpyxl.Workbook` objects in public functions, or raise `openpyxl.utils.exceptions.InvalidFileException` directly.

**Why it's wrong:** Leaks implementation details. Callers become coupled to openpyxl. If the dependency changes, the public API breaks.

**Do this instead:** Catch openpyxl exceptions at the `_io.py` boundary and re-raise as `ValueError` or a custom `ReamError` with a clear message. Never let openpyxl types cross the public API boundary.

### Anti-Pattern 3: Putting research deps in the package

**What people do:** List pandas, openai, tqdm in `pyproject.toml` `[project] dependencies` because they are in `requirements.txt`.

**Why it's wrong:** Anyone who installs the package gets 200MB+ of data-science dependencies for a format converter. Violates the "minimal dependency footprint" constraint from PROJECT.md.

**Do this instead:** `pyproject.toml` lists only `openpyxl>=3.1.0` as a dependency. `requirements.txt` remains for research/eval scripts only. Optionally add a `[project.optional-dependencies] research = [...]` section if needed.

### Anti-Pattern 4: Deleting or moving `src/converters.py`

**What people do:** Clean up the old file once the new package exists.

**Why it's wrong:** Existing benchmark scripts (`run_eval.py`, `scoring.py`, etc.) import from `src/converters.py` directly. Breaking them breaks the research environment.

**Do this instead:** Leave `src/converters.py` exactly as-is. The new `ream/` package is additive. If consolidation is wanted later, that is a separate deliberate decision.

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `__init__.py` ↔ `_io.py` | Direct function call | `_io` functions are pure: input → Workbook |
| `__init__.py` ↔ `_converter.py` | Direct function call | `_converter` functions are pure: Workbook + options → str |
| `cli.py` ↔ `__init__.py` | Imports public API only | CLI must not import from `_converter` directly |
| `ream/` ↔ `src/converters.py` | None | Explicit non-relationship; they coexist, do not share code |
| `pyproject.toml` ↔ `ream/cli.py` | `[project.scripts]` entry | `ream = "ream.cli:main"` wires the `ream` command |

### pyproject.toml Skeleton

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ream"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["openpyxl>=3.1.0"]

[project.scripts]
ream = "ream.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["ream"]
```

Key: `packages = ["ream"]` tells Hatch to package only the `ream/` directory, not `src/`.

## Sources

- [src layout vs flat layout — Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Writing your pyproject.toml — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Packaging Python Projects — Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [How to Manage Python Projects With pyproject.toml — Real Python](https://realpython.com/python-pyproject-toml/)

---
*Architecture research for: ream Python package (XLSX-to-REAM converter)*
*Researched: 2026-03-30*
