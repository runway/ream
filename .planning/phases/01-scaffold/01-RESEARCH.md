# Phase 1: Scaffold - Research

**Researched:** 2026-03-30
**Domain:** Python package scaffolding — hatchling, ruff, mypy strict, pytest
**Confidence:** HIGH

## Summary

Phase 1 creates the `ream_xlsx` package skeleton from scratch: a `pyproject.toml` with hatchling build backend, a flat-layout package directory at the project root, dev toolchain (ruff, mypy strict, pytest) configured entirely in `pyproject.toml`, a `py.typed` marker (empty file per PEP 561), and a `tests/` directory with a single importability test. No implementation code ships in this phase — only the installable, lintable, testable shell.

The primary challenge is hatchling's package auto-discovery: with a flat layout and an existing `src/` directory containing research scripts (not the package), explicit `[tool.hatch.build.targets.wheel] packages = ["ream_xlsx"]` configuration is required to prevent hatchling from accidentally picking up `src/` as a package. This is the single most important pitfall for this phase.

All decisions are locked by CONTEXT.md. Ruff rule selection, pytest details, and stub style are at Claude's discretion and are prescribed below.

**Primary recommendation:** Use `[tool.hatch.build.targets.wheel] packages = ["ream_xlsx"]` explicitly to prevent hatchling from discovering the research `src/` directory as a package.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Package layout**
- Flat layout: `ream_xlsx/` at project root (not inside `src/`)
- Existing `src/` directory stays untouched — it holds research scripts, not part of the package
- This avoids confusion between `src/converters.py` (research) and the new package

**Public API stubs**
- `__init__.py` defines `__all__` with the planned public names: `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`, `ReamOptions`, `ReamError`, `InvalidWorkbookError`, `ConversionError`
- All names stub as `raise NotImplementedError` or empty classes — enough to import without error
- Phase 2 replaces stubs with real implementations

**Dev toolchain config**
- All tool config lives in `pyproject.toml` (no separate `.ruff.toml`, `mypy.ini`, etc.)
- ruff: standard rules, line length 120
- mypy: strict mode enabled
- pytest: test directory `tests/`

**Versioning**
- Static version string in `pyproject.toml` — simplest approach for v1
- No dynamic versioning or git-tag-based versioning yet

### Claude's Discretion
- Exact ruff rule selections beyond defaults
- pytest configuration details (markers, fixtures)
- `__init__.py` stub implementation style
- Whether to include a `py.typed` marker as empty file or with content

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PKG-01 | Package installable with `pip install -e .` via `pyproject.toml` with hatchling backend | Hatchling `[build-system]` + `[project]` tables; editable installs work natively |
| PKG-02 | Package importable as `import ream_xlsx` with `__all__` explicit exports | Flat layout `ream_xlsx/__init__.py` with `__all__` list; hatchling `packages = ["ream_xlsx"]` |
| PKG-03 | `py.typed` marker present and included in built wheels | Empty `ream_xlsx/py.typed` file per PEP 561; hatchling `artifacts` ensures inclusion |
| PKG-04 | Only runtime dependency is openpyxl | `dependencies = ["openpyxl>=3.1.0"]` in `[project]`; Click in optional or already listed |
| PKG-05 | Python >= 3.10 required | `requires-python = ">=3.10"` in `[project]` |
| TST-01 | Tests for package importability and `__all__` exports | `tests/test_package.py` imports `ream_xlsx` and checks `__all__` contents |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| hatchling | latest (1.x) | Build backend for `pyproject.toml` | PyPA-endorsed modern backend; no setup.py; fast |
| ruff | >=0.4.0 | Linter + formatter (replaces flake8, black, isort) | 10-100x faster than alternatives; single tool for lint+format |
| mypy | >=1.9.0 | Static type checker | Gold standard for Python type checking |
| pytest | >=8.0.0 | Test runner | Industry standard; rich plugin ecosystem |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openpyxl | >=3.1.0 | Runtime XLSX parsing | Only runtime dep; already confirmed in requirements |
| click | >=8.1.0 | CLI framework (Phase 3) | Declared in pyproject.toml now per CONTEXT.md; imported only in Phase 3 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| hatchling | setuptools | setuptools requires `setup.py` or more complex config; hatchling is cleaner for new packages |
| ruff | flake8 + black + isort | Three tools vs one; ruff is strictly faster and simpler |
| pytest | unittest | pytest has better assertion introspection and fixture support |

**Installation (dev environment):**
```bash
pip install -e ".[dev]"
```

---

## Architecture Patterns

### Recommended Project Structure
```
ream_xlsx/           # Package directory (flat layout, at project root)
├── __init__.py      # Public API stubs + __all__
└── py.typed         # Empty PEP 561 marker file

tests/
├── __init__.py      # Empty, makes tests a package
└── test_package.py  # TST-01: importability + __all__ check

pyproject.toml       # All project metadata + tool config (single source of truth)
```

Note: `src/` directory remains untouched — it holds research scripts unrelated to the package.

### Pattern 1: pyproject.toml Complete Structure

**What:** Single-file configuration for build, metadata, and all dev tools.
**When to use:** Always — CONTEXT.md locks this approach.

```toml
# Source: https://hatch.pypa.io/latest/config/metadata/
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ream-xlsx"
version = "0.1.0"
description = "Convert XLSX workbooks to REAM text format"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
    { name = "Siqi Chen, Runway Financial" },
]
dependencies = [
    "openpyxl>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.4.0",
    "mypy>=1.9.0",
]

[project.scripts]
ream-xlsx = "ream_xlsx._cli:main"

# CRITICAL: explicit packages prevents hatchling from discovering src/ as a package
[tool.hatch.build.targets.wheel]
packages = ["ream_xlsx"]

[tool.hatch.build.targets.sdist]
include = [
    "ream_xlsx/",
    "tests/",
    "README.md",
    "LICENSE",
    "pyproject.toml",
]

[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "B", "I"]
# E4/E7/E9/F = pyflakes + essential pycodestyle
# B = flake8-bugbear (common Python gotchas)
# I = isort (import ordering)
ignore = []
fixable = ["ALL"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"

[tool.mypy]
strict = true
python_version = "3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Pattern 2: `__init__.py` Stub Style

**What:** All public names defined in `__all__`, each raising `NotImplementedError` or defined as empty class. Importable with zero errors, replaced in Phase 2.
**When to use:** Phase 1 scaffold only.

```python
# Source: CONTEXT.md decisions + PEP 561 / typing best practices
"""ream_xlsx — Convert XLSX workbooks to REAM text format."""

from __future__ import annotations

__all__ = [
    "xlsx_to_ream",
    "bytes_to_ream",
    "file_to_ream",
    "ReamOptions",
    "ReamError",
    "InvalidWorkbookError",
    "ConversionError",
]


class ReamError(Exception):
    """Base exception for all ream_xlsx errors."""


class InvalidWorkbookError(ReamError):
    """Raised for non-XLSX or corrupted files."""


class ConversionError(ReamError):
    """Raised for failures during conversion."""


class ReamOptions:
    """Options controlling REAM conversion output."""


def xlsx_to_ream(path: object, options: object = None) -> str:  # type: ignore[assignment]
    raise NotImplementedError


def bytes_to_ream(data: object, options: object = None) -> str:  # type: ignore[assignment]
    raise NotImplementedError


def file_to_ream(stream: object, options: object = None) -> str:  # type: ignore[assignment]
    raise NotImplementedError
```

Note on mypy strict: stub functions need type annotations that satisfy mypy strict. The pattern above uses `object` + `# type: ignore[assignment]` but a cleaner approach is to use proper signatures with `Any` or typed stubs. See Pitfall 2 below.

### Pattern 3: Importability Test (TST-01)

```python
# tests/test_package.py
"""TST-01: Verify package importability and __all__ exports."""

import ream_xlsx


_EXPECTED_EXPORTS = {
    "xlsx_to_ream",
    "bytes_to_ream",
    "file_to_ream",
    "ReamOptions",
    "ReamError",
    "InvalidWorkbookError",
    "ConversionError",
}


def test_package_importable() -> None:
    """Package imports without error."""
    import importlib
    importlib.import_module("ream_xlsx")


def test_all_defined() -> None:
    """__all__ is defined on the package."""
    assert hasattr(ream_xlsx, "__all__")


def test_all_exports_present() -> None:
    """All names in __all__ are importable from the package."""
    assert set(ream_xlsx.__all__) == _EXPECTED_EXPORTS


def test_all_names_importable() -> None:
    """Every name in __all__ can be imported without ImportError."""
    for name in ream_xlsx.__all__:
        assert hasattr(ream_xlsx, name), f"{name} not found in ream_xlsx"
```

### Anti-Patterns to Avoid

- **Omitting `packages = ["ream_xlsx"]` in hatchling config:** Hatchling auto-discovers packages and will find `src/` (which contains research scripts). Always be explicit.
- **Putting config in separate `.ruff.toml` or `mypy.ini`:** CONTEXT.md locks all config in `pyproject.toml`.
- **Empty `__all__ = []`:** The names must be present and importable (TST-01 checks this). Use stub functions/classes.
- **`from __future__ import annotations` without mypy strict handling:** In strict mode, all function arguments and return types must be annotated. Stub functions need at least `-> str` return type.
- **Not creating `tests/__init__.py`:** Without it, pytest may have import resolution issues with flat layout packages.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Linting + formatting | Custom pre-commit scripts | ruff | ruff handles 900+ rules and formatting atomically |
| Type checking | Runtime assertions | mypy strict | Catches bugs at analysis time, not at runtime |
| Test discovery | Manual test runner scripts | pytest | pytest auto-discovers, has rich fixtures and output |
| Build metadata | `setup.py` or `MANIFEST.in` | `pyproject.toml` + hatchling | PEP 517/518/621 standard; no imperative code needed |
| Version management | `__version__ = "..."` in multiple places | Single `version = "0.1.0"` in `pyproject.toml` | Single source of truth for static versioning |

**Key insight:** Every tool in this stack reads from `pyproject.toml`. Zero additional config files are needed.

---

## Common Pitfalls

### Pitfall 1: Hatchling Discovers `src/` as a Package
**What goes wrong:** Running `pip install -e .` or `python -m build` silently includes the research scripts in `src/` as a package named `src`. Imports may appear to work but the wheel contains wrong files.
**Why it happens:** Hatchling's auto-discovery finds any directory with Python files at the project root. Both `ream_xlsx/` and `src/` qualify.
**How to avoid:** Always specify `[tool.hatch.build.targets.wheel] packages = ["ream_xlsx"]` explicitly.
**Warning signs:** `pip show ream-xlsx` lists unexpected files; `import src` does not fail after install.

### Pitfall 2: mypy Strict Rejects Stub Functions
**What goes wrong:** `mypy --strict` fails on stub functions because they lack proper annotations. `raise NotImplementedError` with no return type annotation violates `--disallow-untyped-defs`.
**Why it happens:** `strict = true` enables `--disallow-untyped-defs` and `--disallow-incomplete-defs`.
**How to avoid:** Annotate all stub functions with proper signatures even in Phase 1. Use actual return types (`-> str`) and typed parameters. The full typed signatures from Phase 2 should be stubbed here with correct types.
**Example fix:**
```python
from pathlib import Path
from typing import Union

def xlsx_to_ream(path: Union[str, Path], options: "ReamOptions | None" = None) -> str:
    raise NotImplementedError
```

### Pitfall 3: `py.typed` Not Included in Wheel
**What goes wrong:** `pip install ream-xlsx` succeeds but mypy treats the package as untyped and ignores type annotations.
**Why it happens:** VCS-ignored files or files not in the default include set are not bundled by hatchling.
**How to avoid:** Add `py.typed` to `artifacts` in `[tool.hatch.build.targets.wheel]` if it does not appear in the built wheel. Verify with `pip show --files ream-xlsx` after editable install, or inspect the `.whl` archive.
**Warning signs:** mypy reports "ream_xlsx is not typed" even after install.

### Pitfall 4: `tests/__init__.py` Missing Causes Import Errors
**What goes wrong:** pytest finds tests but `import ream_xlsx` inside tests fails with `ModuleNotFoundError`.
**Why it happens:** Flat layout means `ream_xlsx/` is at root. Without `pythonpath = ["."]` in pytest config or a proper editable install, the root is not on `sys.path` during test collection.
**How to avoid:** Use `pip install -e .` for the dev environment (the editable install puts the package on `sys.path`). This is confirmed by PKG-01 requiring `pip install -e .`.
**Warning signs:** `pytest` output shows `ModuleNotFoundError: No module named 'ream_xlsx'`.

### Pitfall 5: Click Declared as Runtime Dependency Before Phase 3
**What goes wrong:** Click is in `dependencies` (not `[dev]`), so `import ream_xlsx` triggers Click import. Not a problem now but coupling the runtime to CLI framework before Phase 3.
**Why it happens:** CONTEXT.md says Click should be declared in `pyproject.toml` now, but it's a Phase 3 concern.
**How to avoid:** Declare Click in `dependencies` (it will be a runtime dep when CLI ships). Do NOT import it in `__init__.py` — the `_cli.py` module (created in Phase 3) will import it. The `[project.scripts]` entry point references `ream_xlsx._cli:main` but that module won't exist until Phase 3.

---

## Code Examples

Verified patterns from official sources:

### Minimal pyproject.toml (hatchling, flat layout)
```toml
# Source: https://hatch.pypa.io/latest/config/metadata/ + https://hatch.pypa.io/latest/config/build/
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ream-xlsx"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["openpyxl>=3.1.0", "click>=8.1.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "ruff>=0.4.0", "mypy>=1.9.0"]

[project.scripts]
ream-xlsx = "ream_xlsx._cli:main"

[tool.hatch.build.targets.wheel]
packages = ["ream_xlsx"]
```

### ruff Configuration (line-length 120, recommended rules)
```toml
# Source: https://docs.astral.sh/ruff/configuration/
[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "B", "I"]
fixable = ["ALL"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

### mypy Strict Configuration
```toml
# Source: https://mypy.readthedocs.io/en/stable/config_file.html
[tool.mypy]
strict = true
python_version = "3.10"
```

### pytest Configuration
```toml
# Source: https://docs.pytest.org/en/stable/reference/customize.html
[tool.pytest.ini_options]
testpaths = ["tests"]
```

### PEP 561 py.typed Marker
```
# ream_xlsx/py.typed — empty file, no content needed
# Source: https://peps.python.org/pep-0561/
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` + `setup.cfg` | `pyproject.toml` only | PEP 517/518/621 (2016-2021) | No imperative build code needed |
| `flake8` + `black` + `isort` | `ruff` (single tool) | 2023+ | One config section, 100x faster |
| `mypy.ini` / `setup.cfg [mypy]` | `[tool.mypy]` in pyproject.toml | mypy 0.900+ (2021) | All config in one file |
| `pytest.ini` / `setup.cfg [tool:pytest]` | `[tool.pytest.ini_options]` in pyproject.toml | pytest 6.0+ (2020) | All config in one file |
| `src/` layout default | Flat layout for simple packages | Always valid | Simpler; no import path tricks needed with editable install |

**Deprecated/outdated:**
- `setup.py`: Avoid for new packages; hatchling `pyproject.toml` is the modern standard
- `MANIFEST.in`: Not needed with hatchling; use `[tool.hatch.build.targets.sdist] include`
- Separate `.ruff.toml` file: Functional but unnecessary; `[tool.ruff]` in pyproject.toml is preferred

---

## Open Questions

1. **Click as runtime dependency placement**
   - What we know: CONTEXT.md says declare Click in `pyproject.toml` now; `[project.scripts]` references `ream_xlsx._cli:main`
   - What's unclear: Should Click be in `dependencies` or `[dev]`? It is not a dev tool — it is required at runtime for the CLI entrypoint. When the CLI does not exist yet, the entrypoint will be a dangling reference.
   - Recommendation: Put Click in `dependencies` (runtime). The `[project.scripts]` entry creates a console script that will fail until Phase 3 creates `ream_xlsx/_cli.py`. This is acceptable for Phase 1 — the script exists but fails if invoked, which is expected.

2. **mypy strict on empty package**
   - What we know: `mypy --strict` with no Python sources to check exits 0 by default
   - What's unclear: Once `__init__.py` stubs exist, mypy strict will require full annotations on all stub functions
   - Recommendation: Use proper typed signatures for all stubs (not bare `raise NotImplementedError`). See Pitfall 2 and Pattern 2.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0.0 |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` (Wave 0 creates this) |
| Quick run command | `pytest tests/test_package.py -x` |
| Full suite command | `pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | `pip install -e .` succeeds | smoke | `pip install -e . && python -c "import ream_xlsx"` | Wave 0 |
| PKG-02 | `import ream_xlsx` works; `__all__` defined | unit | `pytest tests/test_package.py::test_package_importable -x` | Wave 0 |
| PKG-02 | All `__all__` names importable | unit | `pytest tests/test_package.py::test_all_names_importable -x` | Wave 0 |
| PKG-03 | `py.typed` present in package | unit | `pytest tests/test_package.py::test_py_typed_marker -x` | Wave 0 |
| PKG-04 | Only openpyxl + click in runtime deps | manual | Inspect `pyproject.toml` `[project.dependencies]` | N/A |
| PKG-05 | Python >= 3.10 declared | manual | Inspect `pyproject.toml` `requires-python` | N/A |
| TST-01 | Importability test passes | unit | `pytest tests/test_package.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_package.py -x`
- **Per wave merge:** `pytest && ruff check . && ruff format --check . && mypy ream_xlsx`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py` — empty file to make tests a package
- [ ] `tests/test_package.py` — covers PKG-01, PKG-02, PKG-03, TST-01
- [ ] `ream_xlsx/__init__.py` — public API stubs
- [ ] `ream_xlsx/py.typed` — empty PEP 561 marker
- [ ] `pyproject.toml` — all config (hatchling + ruff + mypy + pytest)
- [ ] Framework install: `pip install -e ".[dev]"` — installs pytest, ruff, mypy

---

## Sources

### Primary (HIGH confidence)
- [Hatch build configuration](https://hatch.pypa.io/latest/config/build/) — packages, artifacts, sdist include
- [Hatch metadata configuration](https://hatch.pypa.io/latest/config/metadata/) — project table, optional-dependencies, scripts
- [PEP 561](https://peps.python.org/pep-0561/) — py.typed marker specification (empty file)
- [Ruff configuration docs](https://docs.astral.sh/ruff/configuration/) — tool.ruff, tool.ruff.lint, tool.ruff.format
- [mypy config file docs](https://mypy.readthedocs.io/en/stable/config_file.html) — strict mode, pyproject.toml section
- [pytest configuration docs](https://docs.pytest.org/en/stable/reference/customize.html) — tool.pytest.ini_options, testpaths

### Secondary (MEDIUM confidence)
- [Python Packaging User Guide — writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — verified structure matches official guidance
- [pytest good integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) — flat layout + editable install pattern

### Tertiary (LOW confidence)
- None — all critical claims verified from official documentation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools verified from official docs with specific versions
- Architecture: HIGH — pyproject.toml patterns verified from hatchling and pytest official docs
- Pitfalls: HIGH (pitfall 1-4) / MEDIUM (pitfall 5) — flat layout + hatchling discovery confirmed from hatch docs

**Research date:** 2026-03-30
**Valid until:** 2026-06-30 (stable toolchain; ruff/mypy versions ship frequently but config format is stable)
