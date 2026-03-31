# Requirements: ream-xlsx

**Defined:** 2026-03-30
**Core Value:** Any Python application can `pip install ream-xlsx` and convert XLSX workbooks to REAM text with a single function call

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Packaging

- [x] **PKG-01**: Package installable with `pip install -e .` via `pyproject.toml` with hatchling backend
- [x] **PKG-02**: Package importable as `import ream_xlsx` with `__all__` explicit exports
- [x] **PKG-03**: `py.typed` marker present and included in built wheels
- [x] **PKG-04**: Only runtime dependency is openpyxl
- [x] **PKG-05**: Python >= 3.10 required

### Public API

- [x] **API-01**: `xlsx_to_ream(path, options)` converts XLSX file path to REAM string
- [x] **API-02**: `bytes_to_ream(data, options)` converts XLSX bytes to REAM string
- [x] **API-03**: `file_to_ream(stream, options)` converts file-like object to REAM string
- [x] **API-04**: All path-based functions accept `str | Path`
- [x] **API-05**: `ReamOptions` frozen dataclass with `max_rows_per_sheet`, `force_col_selectors`, `collapse_rows`
- [x] **API-06**: Default options produce deterministic output for the same workbook

### Exceptions

- [x] **ERR-01**: `ReamError` base exception for all package errors
- [x] **ERR-02**: `InvalidWorkbookError` raised for non-XLSX or corrupted files
- [x] **ERR-03**: `ConversionError` raised for failures during conversion

### CLI

- [ ] **CLI-01**: `ream-xlsx input.xlsx` command works via `[project.scripts]` entrypoint
- [ ] **CLI-02**: `python -m ream_xlsx input.xlsx` works via `__main__.py`
- [ ] **CLI-03**: Output to stdout by default
- [ ] **CLI-04**: `-o FILE` flag writes output to file instead of stdout
- [ ] **CLI-05**: `--max-rows`, `--force-col-selectors`, `--collapse-rows` flags map to `ReamOptions`
- [ ] **CLI-06**: Exit code 1 + stderr message on invalid input

### Testing

- [x] **TST-01**: Tests for package importability and `__all__` exports
- [x] **TST-02**: Tests for path-based conversion producing valid REAM output
- [x] **TST-03**: Tests for bytes-based conversion matching path-based output
- [x] **TST-04**: Tests for file-like conversion matching path-based output
- [x] **TST-05**: Tests for `ReamOptions` defaults and custom values
- [x] **TST-06**: Tests for deterministic output (same input twice → same output)
- [ ] **TST-07**: Tests for CLI success cases and output correctness
- [ ] **TST-08**: Tests for error handling (missing file, invalid XLSX, empty workbook)
- [x] **TST-09**: Regression tests for any bugs discovered during packaging

### Documentation

- [ ] **DOC-01**: README with installation, quickstart, and copy-pasteable examples
- [ ] **DOC-02**: Public API reference with all functions, options, and exceptions
- [ ] **DOC-03**: CLI usage documentation with all flags
- [ ] **DOC-04**: Developer docs: package layout, public vs internal, running tests, extending
- [ ] **DOC-05**: Error behavior documentation

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Extended Options

- **OPT-01**: `--sheet` CLI flag for single-sheet extraction
- **OPT-02**: Version introspection via `ream_xlsx.__version__`
- **OPT-03**: `read_only` mode exposure as `ReamOptions` field for large workbooks

### Additional Converters

- **CONV-01**: Separate packages for other format converters (CSV, JSON, Markdown)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Other converters (CSV, JSON, Markdown, HTML, XML) as public API | Research tools only; multiplies maintenance surface |
| Async/asyncio support | openpyxl is synchronous; callers can use `asyncio.to_thread()` |
| Streaming/incremental output | REAM format requires multi-pass decisions (row collapse, col selectors) |
| PyPI auto-publishing CI | Infrastructure concern, not a package feature |
| Plugin/extension system | Premature generalization; format is spec-defined |
| Pandas/numpy integration | Adds 400MB+ dependency; document manual workaround instead |
| GUI or web interface | CLI and Python API only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PKG-01 | Phase 1 | Complete |
| PKG-02 | Phase 1 | Complete |
| PKG-03 | Phase 1 | Complete |
| PKG-04 | Phase 1 | Complete |
| PKG-05 | Phase 1 | Complete |
| API-01 | Phase 2 | Complete |
| API-02 | Phase 2 | Complete |
| API-03 | Phase 2 | Complete |
| API-04 | Phase 2 | Complete |
| API-05 | Phase 2 | Complete |
| API-06 | Phase 2 | Complete |
| ERR-01 | Phase 2 | Complete |
| ERR-02 | Phase 2 | Complete |
| ERR-03 | Phase 2 | Complete |
| CLI-01 | Phase 3 | Pending |
| CLI-02 | Phase 3 | Pending |
| CLI-03 | Phase 3 | Pending |
| CLI-04 | Phase 3 | Pending |
| CLI-05 | Phase 3 | Pending |
| CLI-06 | Phase 3 | Pending |
| TST-01 | Phase 1 | Complete |
| TST-02 | Phase 2 | Complete |
| TST-03 | Phase 2 | Complete |
| TST-04 | Phase 2 | Complete |
| TST-05 | Phase 2 | Complete |
| TST-06 | Phase 2 | Complete |
| TST-07 | Phase 3 | Pending |
| TST-08 | Phase 3 | Pending |
| TST-09 | Phase 2 | Complete |
| DOC-01 | Phase 4 | Pending |
| DOC-02 | Phase 4 | Pending |
| DOC-03 | Phase 4 | Pending |
| DOC-04 | Phase 4 | Pending |
| DOC-05 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 34 total
- Mapped to phases: 34
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 after roadmap creation*
