# Stack Research

**Domain:** Python library package — XLSX-to-REAM converter
**Researched:** 2026-03-30
**Confidence:** HIGH (versions verified against PyPI and official docs)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | >=3.10 | Runtime | pytest 9.x and hatchling 1.29 both require >=3.10; type hint syntax used in the codebase (`X \| Y` unions) requires 3.10+. Do not target 3.9. |
| hatchling | >=1.29.0 | Build backend | PEP 621-compliant, zero custom config for pure-Python packages, actively maintained (latest 1.29.0, Feb 2026). Preferred over uv_build because it is a stable, independent package while uv_build is still pre-1.0 and version-pinned in a narrow range. |
| pyproject.toml | PEP 621 | Project metadata & packaging config | The single source of truth for metadata, build system, tool config, and optional dependency groups. `setup.py` / `setup.cfg` are legacy; do not use them. |
| openpyxl | >=3.1.5 | XLSX reading | Already used in the codebase. Only runtime dependency the `ream` package requires — keep it that way. |
| Click | >=8.3.1 | CLI framework | Most widely adopted Python CLI library (38.7% of CLI projects in 2025). Mature, battle-tested, decorator-based API maps cleanly to the small set of flags `ream` needs. Lower overhead than Typer (no Pydantic dependency) for a package with a minimal-footprint goal. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=9.0.2 | Test runner | All unit and integration tests. The project has no existing tests; pytest is the de-facto standard and the TDD requirement demands it from day one. |
| pytest-cov | >=7.1.0 | Coverage reporting | Measure test coverage against the public API contract. Use `--cov=ream --cov-report=term-missing` in CI. |
| mypy | >=1.19.1 | Static type checking | The existing code uses `from typing import Any` — mypy enforces that the public API (`xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`, `ReamOptions`) stays correctly typed. Run in strict mode for the `ream/` package directory. |
| ruff | >=0.15.8 | Linting + formatting | Replaces flake8 + isort + black with a single Rust-based tool. Extremely fast; configurable in `pyproject.toml` under `[tool.ruff]`. Use it as both linter and formatter. |
| mkdocs-material | >=9.7.2 | Documentation site | Best Markdown-first documentation experience; professional output with zero RST knowledge required. Suitable for the quickstart, API reference, CLI usage, and examples required by PROJECT.md. Version 9.7.x is the last feature release (end-of-feature Nov 2026) — still the correct choice for this project's lifespan. |
| mkdocstrings[python] | >=1.0.3 | API reference from docstrings | Integrates with MkDocs-Material to auto-generate API reference pages from Google-style or NumPy-style docstrings. Eliminates manual API docs maintenance. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Dependency manager, virtual env, build/publish frontend | 10–100x faster than pip. `uv sync`, `uv add`, `uv build`, `uv publish`. Use it as the developer-facing tool even though hatchling is the build backend. Install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| hatch | Optional: environment matrix management | Useful if you need to test across multiple Python versions (3.10, 3.11, 3.12). Not required if uv's environment tooling is sufficient. |

## Installation

```bash
# Initialize project with uv (creates pyproject.toml, .venv, uv.lock)
uv init --lib ream

# Install runtime dependency (goes into [project.dependencies])
uv add openpyxl

# Install dev dependencies (goes into [dependency-groups] dev)
uv add --dev pytest pytest-cov mypy ruff mkdocs-material "mkdocstrings[python]"

# Install the package in editable mode for local development
uv pip install -e .

# Run tests
uv run pytest

# Run type checking
uv run mypy ream/ --strict

# Run linter/formatter
uv run ruff check ream/
uv run ruff format ream/

# Build wheel + sdist
uv build
```

## pyproject.toml Skeleton

```toml
[build-system]
requires = ["hatchling>=1.29"]
build-backend = "hatchling.build"

[project]
name = "ream"
version = "0.1.0"
description = "Convert XLSX workbooks to REAM format for LLM consumption"
readme = "README.md"
license = { text = "MIT" }
authors = [{ name = "Siqi Chen", email = "..." }]
requires-python = ">=3.10"
dependencies = ["openpyxl>=3.1.5"]

[project.scripts]
ream = "ream.__main__:cli"

[dependency-groups]
dev = [
  "pytest>=9.0.2",
  "pytest-cov>=7.1.0",
  "mypy>=1.19.1",
  "ruff>=0.15.8",
  "mkdocs-material>=9.7.2",
  "mkdocstrings[python]>=1.0.3",
]

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "N"]

[tool.mypy]
strict = true
python_version = "3.10"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| hatchling | uv_build | If your entire toolchain is uv-native and you need zero-config defaults. Avoid for now: uv_build is pre-1.0 (currently 0.11.x), narrow version pin required, and the ecosystem is less proven. |
| hatchling | setuptools | Only if you have C extensions or need `setup.py` hooks for legacy build steps. Pure-Python packages have no reason to use setuptools in 2026. |
| hatchling | poetry-core | Use poetry-core only if the team already uses Poetry for dependency management and wants a single-tool experience. Poetry's PEP 621 compliance is still partial, creating friction with uv. |
| Click | Typer | Use Typer if the CLI grows to have many nested subcommands and you want automatic Pydantic validation on arguments. Typer adds a Pydantic dependency — incompatible with the "minimal footprint" goal. |
| Click | argparse | Use argparse only if you want zero additional dependencies and the CLI is trivially simple (one command, two flags). The `ream` CLI has enough flag complexity (max-rows, force-col-selectors, collapse-rows, output file) that Click's ergonomics are worth the single dependency. |
| mypy | pyright | Pyright is faster and stricter; it powers Pylance in VS Code. Use pyright if the team is VS Code-centric and wants IDE-integrated checking. Both are valid; mypy is chosen here because it has more predictable PEP compliance and better plugin support. Consider adding `pyright` as a secondary check in CI. |
| mypy | ruff's `ty` checker | `ty` (Astral's new Rust type checker) is promising but pre-1.0 as of early 2026. Do not use for production CI yet. Revisit in 6 months. |
| mkdocs-material | Sphinx | Use Sphinx for projects that need PDF output, Intersphinx cross-referencing, or the PyData/NumPy documentation ecosystem. For a focused converter library with Markdown-first docs, mkdocs-material is faster to set up and produces better-looking output. |
| ruff | flake8 + black + isort | There is no reason to use three tools when ruff does all three faster. flake8, black, and isort are legacy for new projects. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| setup.py / setup.cfg | Superseded by pyproject.toml (PEP 517/621). setuptools still works but setup.py is not needed for pure-Python packages and creates confusion. | `pyproject.toml` with hatchling |
| pandas | PROJECT.md explicitly excludes it: "pandas is used only by the pandas converter (not needed for REAM)." Adding it to the package dependency would inflate install size by ~30MB. | openpyxl only |
| Poetry (as dependency manager) | Poetry's `pyproject.toml` format deviates from PEP 621 for dependency specification, creating a two-tool story when uv already handles the same workflow in a standards-compliant way. | uv |
| tox | Adds a layer of complexity that uv's environment management replaces. Only consider tox if you need integration with a non-uv CI system that doesn't support uv natively. | uv run + GitHub Actions matrix |
| Typer | Adds pydantic as a transitive dependency, violating the "minimal dependency footprint" constraint in PROJECT.md. | Click |
| pdoc3 | Generates API docs from code only, with no support for hand-written guides (quickstart, examples). PROJECT.md requires "complete developer documentation." | mkdocs-material + mkdocstrings |

## Stack Patterns by Variant

**If publishing to PyPI later:**
- Add `[project.urls]` to pyproject.toml (Homepage, Documentation, Repository)
- Use `uv publish` — it reads PyPI credentials from environment variables (`UV_PUBLISH_TOKEN`)
- No twine required

**If testing across Python 3.10 / 3.11 / 3.12:**
- Add a `[[tool.hatch.envs.test.matrix]]` block and use `hatch test` OR
- Use a GitHub Actions matrix with `python-version: ["3.10", "3.11", "3.12"]`
- Do not use tox

**If the existing `src/converters.py` benchmark scripts must keep working:**
- Keep `requirements.txt` for research deps (pandas, openai, tqdm, etc.)
- The `ream/` package directory uses only openpyxl
- Do not add research deps to `[project.dependencies]`

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| hatchling>=1.29.0 | Python >=3.10 | hatchling 1.29 requires Python >=3.10, consistent with project minimum |
| pytest>=9.0.2 | Python >=3.10 | pytest 9 dropped Python 3.8/3.9 support |
| openpyxl>=3.1.5 | Python >=3.8 | Compatible; no upper constraint needed |
| Click>=8.3.1 | Python >=3.8 | Compatible; no upper constraint needed |
| ruff>=0.15.8 | Python >=3.7 | Compatible; no upper constraint needed |
| mypy>=1.19.1 | Python >=3.9 | Compatible; no upper constraint needed |

## Sources

- PyPI: pytest 9.0.2 — https://pypi.org/project/pytest/ (verified March 2026)
- PyPI: hatchling 1.29.0 — https://pypi.org/project/hatchling/ (verified March 2026)
- PyPI: Click 8.3.1 — https://pypi.org/project/click/ (verified March 2026)
- PyPI: mypy 1.19.1 — https://pypi.org/project/mypy/ (verified March 2026)
- PyPI: ruff 0.15.8 — https://pypi.org/project/ruff/ (verified March 2026)
- PyPI: pytest-cov 7.1.0 — https://pypi.org/project/pytest-cov/ (verified March 2026)
- PyPI: mkdocs-material 9.7.2 — https://pypi.org/project/mkdocs-material/ (verified March 2026)
- PyPI: mkdocstrings 1.0.3 — https://pypi.org/project/mkdocstrings/ (verified March 2026)
- PyPI: openpyxl 3.1.5 — https://pypi.org/project/openpyxl/ (verified March 2026)
- Astral uv build backend docs — https://docs.astral.sh/uv/concepts/build-backend/ (uv_build 0.11.2 current, pre-1.0 warning noted)
- Python Packaging Best Practices 2026 — https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/
- State of Python Packaging 2026 — https://learn.repoforge.io/posts/the-state-of-python-packaging-in-2026/
- Python Build Backends 2025 (uv_build vs Hatchling) — https://medium.com/@dynamicy/python-build-backends-in-2025-what-to-use-and-why-uv-build-vs-hatchling-vs-poetry-core-94dd6b92248f
- mkdocs-material end-of-feature note — https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/

---
*Stack research for: Python package — ream (XLSX to REAM converter)*
*Researched: 2026-03-30*
