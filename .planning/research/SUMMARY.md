# Project Research Summary

**Project:** ream — XLSX to REAM converter
**Domain:** Python library package (file-format conversion for LLM consumption)
**Researched:** 2026-03-30
**Confidence:** HIGH

## Executive Summary

The `ream` package is a focused Python library that converts XLSX workbooks into REAM format — a token-efficient text encoding designed for LLM consumption. Experts build this class of package by enforcing a strict separation between the installable public API and the research/evaluation code that lives alongside it in the same repo. The core pattern is thin public functions (accepting path, bytes, or stream) delegating to private conversion logic, with all user-facing options expressed through a single typed dataclass. The package must ship with full type annotations, a `py.typed` marker, a CLI entrypoint, and only `openpyxl` as a runtime dependency.

The recommended approach is: scaffold `pyproject.toml` first (with hatchling as build backend, Python `>=3.10`, `openpyxl` as the sole runtime dep), then build the package in strict dependency order — `ReamOptions` dataclass first, conversion logic second, I/O adapters third, public `__init__.py` fourth, CLI last. Tests are written per step (TDD). The development toolchain is uv + ruff + mypy (strict) + pytest with coverage. Documentation uses mkdocs-material with mkdocstrings for API reference generated from docstrings.

The primary risks are not technical but structural: the PyPI package name `ream` is already taken (must be resolved before any release), the flat repo layout creates import-shadowing traps during testing, and lifting conversion logic out of `src/converters.py` into the new package risks silently breaking existing benchmark scripts. All three risks are preventable if addressed in Phase 1 before any implementation code is written. The conversion logic itself is well-understood and already implemented in `src/converters.py` — the core work is packaging, API surface design, and test coverage, not algorithm development.

## Key Findings

### Recommended Stack

The stack is tightly constrained by the "minimal dependency footprint" requirement and the existing codebase. Python `>=3.10` is the floor (required by hatchling 1.29, pytest 9, and the `X | Y` union type syntax already in use). The build backend is hatchling — PEP 621-compliant, zero custom config for pure-Python packages, and actively maintained. uv is the developer-facing dependency manager and build frontend (10-100x faster than pip). The sole runtime dependency is openpyxl `>=3.1.5`. Click `>=8.3.1` is the CLI framework, chosen over argparse for ergonomics given the flag complexity, and over Typer because Typer adds Pydantic as a transitive dependency (incompatible with minimal-footprint goal). Dev tooling is ruff (linting + formatting, replaces flake8/black/isort), mypy in strict mode, pytest `>=9.0.2` with pytest-cov, and mkdocs-material with mkdocstrings for docs.

**Core technologies:**
- Python `>=3.10`: Runtime — floor set by build toolchain and type syntax in use
- hatchling `>=1.29.0`: Build backend — PEP 621-compliant, stable, no setup.py needed
- openpyxl `>=3.1.5`: XLSX reading — already in use; only runtime dep; no pandas
- Click `>=8.3.1`: CLI framework — mature, decorator-based, minimal deps vs Typer
- uv: Dependency manager + build frontend — 10-100x faster than pip
- ruff `>=0.15.8`: Linting + formatting — replaces flake8, black, isort in one tool
- mypy `>=1.19.1`: Static type checking — strict mode on `ream/` package directory
- pytest `>=9.0.2` + pytest-cov: Testing — de-facto standard; required for TDD mandate
- mkdocs-material `>=9.7.2` + mkdocstrings: Docs — Markdown-first, API reference from docstrings

### Expected Features

The public API surface is small and well-defined. The three input-type variants (`xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`) all share the same `ReamOptions` dataclass and delegate to common private conversion logic. The CLI mirrors the Python API. Type annotations and `py.typed` are required from day one — retrofitting is painful and breaks adopters' type checks.

**Must have (table stakes):**
- `xlsx_to_ream(path, options)` — primary entry point; covers 90% of callers
- `bytes_to_ream(data, options)` — required for web and pipeline use cases
- `file_to_ream(stream, options)` — required for pipe/stream use cases
- `ReamOptions` frozen dataclass — stable, typed options API all three converters share
- `ReamError`, `InvalidWorkbookError`, `ConversionError` — clean exception surface; no leaking openpyxl internals
- `ream` CLI + `python -m ream` — stdout-by-default, `-o FILE` flag, key option flags
- Full type annotations + `py.typed` marker — needed from day one
- `pyproject.toml` with `[project.scripts]` — modern packaging; `pip install -e .` must work
- Deterministic output — same input always produces same output (verified in tests)

**Should have (competitive):**
- `pathlib.Path` acceptance in all signatures — modern Python ergonomic expectation
- `max_rows_per_sheet` truncation marker in output — prevents silent LLM context blowup
- `__all__` explicit export list — communicates public surface, makes `from ream import *` safe
- `collapse_rows` and `force_col_selectors` flags as first-class `ReamOptions` fields
- Version introspection (`ream.__version__`)

**Defer (v2+):**
- Additional format converters (CSV, JSON, Markdown) as separate packages if demand materializes
- `--sheet` CLI flag for single-sheet extraction
- Performance profiling and `read_only` flag exposure as `ReamOptions` field
- Async support (document `asyncio.to_thread` pattern in README instead)

### Architecture Approach

The package uses a four-layer architecture: a thin public API in `__init__.py` re-exporting from private submodules; an I/O adapter layer in `_io.py` that normalizes path/bytes/stream inputs into openpyxl `Workbook` objects; a private conversion core in `_converter.py` containing all REAM logic; and a CLI layer in `cli.py` that maps argparse flags to `ReamOptions` and delegates to the public API. The `ream/` package directory sits at the project root (not under `src/`) to stay visually distinct from the existing `src/` research scripts. The `src/converters.py` file is left entirely untouched — the new package is purely additive.

**Major components:**
1. `ream/__init__.py` — Public API surface; re-exports only; sets `__all__`
2. `ream/_options.py` — `ReamOptions` frozen dataclass; no imports from package
3. `ream/_io.py` — Input normalization (path/bytes/stream → openpyxl Workbook)
4. `ream/_converter.py` — All REAM conversion logic (private); pure functions on Workbook
5. `ream/cli.py` — Argument parsing and output routing; delegates to public API
6. `ream/__main__.py` — Single line enabling `python -m ream`
7. `tests/` — TDD test suite; never ships with package
8. `src/converters.py` — Unchanged legacy research file; explicit non-relationship with package

### Critical Pitfalls

1. **PyPI name collision** — The name `ream` is already taken on PyPI (chmlee/ream-python). Resolve before writing any import paths or documentation. Either register a placeholder `0.0.1` release to claim the name, or decide on an alternate name (`ream-converter`) before any code is written. A name change late in development touches every import statement, README example, and CLI doc.

2. **Flat layout import shadowing** — Running `pytest` from the repo root without `pip install -e .` first means tests run against the raw source tree, not the installed package. Enforce `pip install -e .` as a prerequisite in CI and local setup. Consider `--import-mode=importlib` in pytest config. The ARCHITECTURE.md notes a pragmatic flat layout is acceptable here (package name doesn't shadow stdlib), but the install step must be enforced.

3. **Breaking benchmark scripts during restructuring** — `src/converters.py` is imported by benchmark scripts that have no tests. Keep it intact. The new `ream/` package is additive. If logic is ported, leave `src/converters.py` as a thin shim re-exporting from `ream`.

4. **Leaking internal API via `__init__.py`** — Importing everything for convenience accidentally exposes private helpers as the public API. Define `__all__` in `__init__.py` before writing tests — tests should only import from `__all__`, which enforces the boundary.

5. **CLI entrypoint divergence** — Both `ream` (console_scripts) and `python -m ream` must invoke the same `main()` function with zero arguments. Wire `__main__.py` to `cli.main()` and verify both paths in CI smoke tests.

6. **Missing files in distributed wheel** — `py.typed` and other non-`.py` files may be absent from the built wheel even when they exist in source. Inspect wheel contents after building and add a CI step that installs the wheel in a fresh venv and runs the full test suite.

## Implications for Roadmap

Based on combined research, the work naturally decomposes into four phases ordered by strict dependency — each phase requires only what the previous phase delivered.

### Phase 1: Package Scaffolding and Name Resolution

**Rationale:** Name collision and layout decisions must be locked before any code is written — changing them later touches every import path, README example, and CI config. This phase has zero implementation risk and unblocks all subsequent phases.

**Delivers:** A buildable, installable skeleton. `pip install -e .` works. `ream --help` fails gracefully. No import shadowing. `src/converters.py` untouched.

**Addresses:** `pyproject.toml` packaging (table stakes), `py.typed` marker, Python version range

**Avoids:** PyPI name collision (Pitfall 1), flat layout import shadowing (Pitfall 2), wrong `python_requires` (Pitfall 6)

**Key tasks:**
- Verify/claim PyPI name or decide on alternate name
- Write `pyproject.toml` with hatchling backend, `requires-python = ">=3.10"`, `openpyxl>=3.1.5` only
- Create `ream/` directory with `__init__.py`, `__main__.py`, `py.typed` stubs
- Configure ruff, mypy strict, pytest in `pyproject.toml`
- Set up CI matrix (Python 3.10, 3.11, 3.12, 3.13)
- Confirm `src/converters.py` and benchmark scripts still work

### Phase 2: Core Conversion API

**Rationale:** The conversion logic already exists in `src/converters.py`. This phase ports it to the package structure with a clean public API, full type annotations, and test coverage. `ReamOptions` must be stable before any variant or CLI can be built.

**Delivers:** A fully tested, typed, importable Python API: `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`, `ReamOptions`, and the `ReamError` exception hierarchy.

**Addresses:** All P1 table-stakes API features; deterministic output guarantee; `pathlib.Path` acceptance; `__all__` explicit exports

**Avoids:** Leaking internal API (Pitfall 4), breaking benchmark scripts (Pitfall 3)

**Key tasks:**
- Write `_options.py` (`ReamOptions` dataclass with typed defaults)
- Port conversion logic from `src/converters.py` to `_converter.py` (TDD — tests first)
- Write `_io.py` input adapters (path/bytes/stream → Workbook)
- Write public `__init__.py` with explicit `__all__`
- Define `ReamError` exception hierarchy in `exceptions.py`
- Verify `src/converters.py` shim works (re-exports from `ream` if needed)

### Phase 3: CLI Entrypoint

**Rationale:** CLI depends on a stable `ReamOptions` and the complete public API from Phase 2. Building CLI before the library API is stable leads to rework as option fields change.

**Delivers:** Working `ream` command and `python -m ream` with stdout-by-default, `-o FILE`, `--max-rows`, `--force-col-selectors`, `--collapse-rows` flags.

**Addresses:** CLI (table stakes), stdout-by-default convention, Unix pipeline compatibility

**Avoids:** CLI entrypoint divergence (Pitfall 5)

**Key tasks:**
- Write `cli.py` with Click argument parsing mapping flags to `ReamOptions`
- Write `__main__.py` as single-line delegator to `cli.main()`
- Wire `[project.scripts] ream = "ream.cli:main"` in `pyproject.toml`
- Add CI smoke tests for both `ream --help` and `python -m ream --help`
- Test `ReamError` → exit code 1 + stderr message conversion

### Phase 4: Documentation and Release Validation

**Rationale:** Documentation and wheel validation are the last gate before the package is usable by others. Wheel validation catches packaging bugs that are invisible in editable installs.

**Delivers:** Complete MkDocs-Material site (quickstart, API reference, CLI usage, examples), built wheel verified in clean venv, CHANGELOG, version set to `0.1.0`.

**Addresses:** README quickstart + API reference (table stakes), `ream.__version__` introspection

**Avoids:** Missing files in distributed wheel (Pitfall 7)

**Key tasks:**
- Set up mkdocs-material with mkdocstrings for API reference from docstrings
- Write quickstart, CLI usage, and examples pages
- Build wheel (`uv build`) and inspect contents (`python -m zipfile -l dist/ream-*.whl`)
- CI step: install wheel in fresh venv, run full test suite against installed package (not editable)
- Write CHANGELOG, confirm `ream.__version__` is accessible

### Phase Ordering Rationale

- **Scaffolding before code** because PyPI name and package layout decisions are irreversible without full rework of import paths and documentation. One hour of name research in Phase 1 saves days of renaming later.
- **Options before API before CLI** because each layer is a strict dependency of the next. `ReamOptions` is the shared language between all three input variants and the CLI flag parser.
- **CLI after API** because CLI is a thin adapter over the public API. Any instability in `ReamOptions` fields requires CLI rework.
- **Docs and wheel validation last** because documentation can only be written once the API is stable, and wheel validation is a final correctness check before release.

### Research Flags

Phases with standard, well-documented patterns (skip research-phase):
- **Phase 1:** PEP 621/hatchling packaging is well-documented; uv workflow is standard. PyPI name check is a one-time manual step, not a research problem.
- **Phase 2:** Conversion logic is already implemented in `src/converters.py`. Porting to package structure follows established Python library patterns. TDD with pytest is standard.
- **Phase 3:** Click CLI patterns are thoroughly documented. The `console_scripts` wiring is standard pyproject.toml.
- **Phase 4:** mkdocs-material + mkdocstrings setup is well-documented. Wheel validation is a known CI pattern.

No phases require `/gsd:research-phase` — all patterns are standard and well-sourced.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified against PyPI (March 2026); official docs consulted for all tools |
| Features | HIGH | Derived from direct analysis of analogous packages (openpyxl, PyYAML, python-markdown); official PEP 561 and PyPA guides |
| Architecture | HIGH | Follows Python Packaging User Guide official recommendations; src layout vs flat layout documented |
| Pitfalls | HIGH | Critical pitfalls verified against official Python Packaging User Guide, pytest docs, and live PyPI state |

**Overall confidence:** HIGH

### Gaps to Address

- **PyPI name ownership:** The `ream` name on PyPI is claimed (chmlee/ream-python, 51 weekly downloads, inactive). Whether to claim it via PyPI dispute resolution, publish a placeholder immediately, or use an alternate name must be decided by the project owner before Phase 1 can complete. This is a business/legal decision, not a technical one.
- **Internal-only vs. PyPI publishing:** PROJECT.md says the package must be "publishable" but release is a separate step. Confirm whether PyPI publishing is actually required or if the package is Runway Financial internal-only — this affects the name urgency and the need for `[project.urls]` metadata.
- **`src/converters.py` exact import surface:** The pitfalls research recommends a shim approach if logic is moved, but the exact set of symbols benchmark scripts import from `converters.py` needs a quick audit before Phase 2 begins to size the shim correctly.

## Sources

### Primary (HIGH confidence)
- PyPI: pytest, hatchling, Click, mypy, ruff, pytest-cov, mkdocs-material, mkdocstrings, openpyxl — versions verified March 2026
- Python Packaging User Guide — https://packaging.python.org/ (src layout, pyproject.toml, entry points, MANIFEST.in)
- PEP 561 `py.typed` marker — https://peps.python.org/pep-0561/
- pytest Good Integration Practices — https://docs.pytest.org/en/stable/explanation/goodpractices.html
- Astral uv docs — https://docs.astral.sh/uv/concepts/build-backend/
- Python typing distribution spec — https://typing.python.org/en/latest/spec/distributing.html
- mkdocs-material end-of-feature note — https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/

### Secondary (MEDIUM confidence)
- Python Build Backends 2025 (uv_build vs Hatchling vs Poetry) — https://medium.com/@dynamicy/python-build-backends-in-2025-what-to-use-and-why-uv-build-vs-hatchling-vs-poetry-core-94dd6b92248f
- State of Python Packaging 2026 — https://learn.repoforge.io/posts/the-state-of-python-packaging-in-2026/
- Click vs argparse comparison (2025) — https://dasroot.net/posts/2025/12/building-cli-tools-python-click-typer-argparse/
- Python exception hierarchy best practices — https://jacobpadilla.com/articles/custom-python-exceptions
- Snyk Advisor: ream PyPI package — https://snyk.io/advisor/python/ream (name conflict confirmed)
- chmlee/ream-python — https://github.com/chmlee/ream-python (conflicting package)

---
*Research completed: 2026-03-30*
*Ready for roadmap: yes*
