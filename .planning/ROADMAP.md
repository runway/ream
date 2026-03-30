# Roadmap: ream-xlsx

## Overview

Transform the existing `src/converters.py` research script into an installable, tested, documented Python package (`ream-xlsx`, imported as `ream_xlsx`) that any Python application can `pip install` to convert XLSX workbooks to REAM text. Four phases deliver in strict dependency order: scaffold the package structure first, implement the public API second, add the CLI third, and complete documentation last. TDD is enforced throughout — tests are written before implementation in each phase.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Scaffold** - Package skeleton installable with `pip install -e .`; dev toolchain configured; no implementation code yet
- [ ] **Phase 2: Core API** - Public `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`, `ReamOptions`, and exception hierarchy fully implemented and tested
- [ ] **Phase 3: CLI** - `ream-xlsx` command and `python -m ream_xlsx` working with all flags, tested end-to-end
- [ ] **Phase 4: Documentation** - Complete README, API reference, CLI usage, and developer docs; wheel validated; PR ready

## Phase Details

### Phase 1: Scaffold
**Goal**: The package exists as a buildable, importable skeleton with dev toolchain configured
**Depends on**: Nothing (first phase)
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04, PKG-05, TST-01
**Success Criteria** (what must be TRUE):
  1. `pip install -e .` succeeds and `import ream_xlsx` works in a fresh environment
  2. `ream_xlsx.__all__` is defined and importable with zero `ImportError`
  3. `py.typed` marker is present and the package passes `mypy --strict` with no source to check
  4. `pytest` discovers the test suite and `TST-01` importability test passes
  5. `ruff check` and `ruff format --check` pass on the empty package
**Plans**: TBD

### Phase 2: Core API
**Goal**: Any Python caller can convert an XLSX file, bytes payload, or file stream to REAM text with typed options and clean exceptions
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06, ERR-01, ERR-02, ERR-03, TST-02, TST-03, TST-04, TST-05, TST-06, TST-09
**Success Criteria** (what must be TRUE):
  1. `from ream_xlsx import xlsx_to_ream; result = xlsx_to_ream("workbook.xlsx")` returns a non-empty REAM string
  2. `bytes_to_ream(data)` and `file_to_ream(stream)` produce output identical to `xlsx_to_ream` for the same workbook
  3. `ReamOptions(max_rows_per_sheet=10)` is accepted by all three functions and limits output rows accordingly
  4. Calling `xlsx_to_ream` twice on the same file returns byte-for-byte identical output
  5. Passing a missing file path raises `InvalidWorkbookError`; a corrupted payload raises `ConversionError`; both are subclasses of `ReamError`
**Plans**: TBD

### Phase 3: CLI
**Goal**: Users can invoke the converter from the shell via `ream-xlsx` or `python -m ream_xlsx` with all option flags
**Depends on**: Phase 2
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-06, TST-07, TST-08
**Success Criteria** (what must be TRUE):
  1. `ream-xlsx input.xlsx` prints valid REAM text to stdout and exits 0
  2. `ream-xlsx input.xlsx -o out.txt` writes output to `out.txt` and prints nothing to stdout
  3. `ream-xlsx input.xlsx --max-rows 5 --collapse-rows --force-col-selectors` all apply their respective `ReamOptions` fields
  4. `python -m ream_xlsx input.xlsx` produces identical output to `ream-xlsx input.xlsx`
  5. `ream-xlsx missing.xlsx` exits with code 1 and writes a human-readable error message to stderr
**Plans**: TBD

### Phase 4: Documentation
**Goal**: Any developer can install, use, and extend the package without asking questions; built wheel passes full test suite in a clean environment
**Depends on**: Phase 3
**Requirements**: DOC-01, DOC-02, DOC-03, DOC-04, DOC-05
**Success Criteria** (what must be TRUE):
  1. README quickstart section contains copy-pasteable install + usage example that works verbatim
  2. API reference documents all public functions, `ReamOptions` fields, and exceptions with their types and defaults
  3. CLI usage section documents every flag with its effect and an example invocation
  4. Developer docs explain package layout, how to run tests, and how to distinguish public from internal modules
  5. Built wheel installed in a clean venv passes the full `pytest` suite without the editable install
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffold | 0/TBD | Not started | - |
| 2. Core API | 0/TBD | Not started | - |
| 3. CLI | 0/TBD | Not started | - |
| 4. Documentation | 0/TBD | Not started | - |
