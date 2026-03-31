# Ream Python Package

## What This Is

A reusable, installable Python package for converting XLSX workbooks into the REAM text format — a UTF-8, line-oriented, token-efficient representation designed for LLM spreadsheet comprehension. The package exposes a small, stable public API for REAM conversion from file paths, bytes, and file-like objects, plus a CLI entrypoint. It is platform-agnostic and application-agnostic.

## Core Value

Any Python application can `pip install ream` and convert XLSX workbooks to REAM text with a single function call — no research tooling, no vendor lock-in, no unnecessary dependencies.

## Requirements

### Validated

- [x] Installable Python package with `pyproject.toml` and `pip install -e .` — Validated in Phase 1: Scaffold
- [x] Public API: `xlsx_to_ream(path)`, `bytes_to_ream(data)`, `file_to_ream(stream)` — Validated in Phase 2: Core API
- [x] `ReamOptions` dataclass for export settings (max_rows_per_sheet, force_col_selectors, collapse_rows) — Validated in Phase 2: Core API
- [x] TDD: full test suite covering public API contract, options, error handling — Validated in Phase 2: Core API (36 tests)
- [x] Deterministic output for the same workbook input — Validated in Phase 2: Core API
- [x] Clean package boundary: `ream_xlsx/` package directory, research/eval code stays separate — Validated in Phase 1: Scaffold
- [x] Minimal dependency footprint (openpyxl only for package core) — Validated in Phase 1: Scaffold
- [x] CLI entrypoint: `python -m ream_xlsx` and `ream-xlsx` command — Validated in Phase 3: CLI (49 tests)
- [x] CLI supports stdout output, optional output file, key REAM options as flags — Validated in Phase 3: CLI
- [x] TDD: CLI and end-to-end tests — Validated in Phase 3: CLI (13 CLI tests)

### Active

- [ ] Complete developer documentation (install, quickstart, API reference, CLI usage, examples)

### Out of Scope

- Other converters (CSV, Markdown, JSON, HTML, XML, etc.) — internal/research only, not part of public API
- PyPI publishing — package should be publishable but actual release is a separate step
- Benchmark/eval tooling rewrite — existing scripts should keep working but are not part of the package
- GUI or web interface — CLI and Python API only

## Context

- The repo is currently a standalone research/evaluation project for LLM spreadsheet comprehension benchmarks
- Core conversion logic exists in `src/converters.py` with `xlsx_to_ream(filepath, max_rows_per_sheet, force_col_selectors, collapse_rows)`
- The REAM format has two wire versions: #!REAM 9 (no row collapse) and #!REAM 11 (with row-span compaction)
- Existing converters use openpyxl for XLSX reading; pandas is used only by the pandas converter (not needed for REAM)
- No existing tests — evaluation scripts serve as validation but are not unit tests
- 15 converter functions exist in `src/converters.py`; only REAM-related ones become public API
- License: MIT (Copyright 2026 Siqi Chen, Runway Financial)

## Constraints

- **Package name**: `ream` — import as `from ream import xlsx_to_ream`
- **Dependencies**: Only openpyxl required for the package; research deps stay in requirements.txt
- **Backward compat**: Existing `src/converters.py` must keep working for benchmark scripts
- **TDD**: Tests written before implementation for each public API behavior
- **Deliverable**: A pull request with all changes

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| REAM-only public API | Keep surface small, other converters are research tools | — Pending |
| Package name `ream` | Simple, matches the format name | — Pending |
| openpyxl as sole package dependency | Minimal footprint; pandas/openai are research-only | — Pending |
| `ReamOptions` dataclass over ad-hoc booleans | Clean API, documented defaults, extensible | — Pending |

---
*Last updated: 2026-03-31 after Phase 3 (CLI) completion*
