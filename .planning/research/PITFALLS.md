# Pitfalls Research

**Domain:** Python packaging — extracting a library from a research/eval repo
**Researched:** 2026-03-30
**Confidence:** HIGH (critical packaging pitfalls verified against official Python Packaging User Guide, setuptools docs, pytest docs)

---

## Critical Pitfalls

### Pitfall 1: PyPI Name Collision — "ream" Is Already Taken

**What goes wrong:**
An existing PyPI package named `ream` already exists (a parser/emitter for a different REAM file format, hosted at `chmlee/ream-python`). Attempting to publish to PyPI with the same name will fail. More dangerously, users who do `pip install ream` today get the *wrong* package. During development, a local `pip install -e .` will shadow the PyPI package correctly, but any downstream consumer who tries to `pip install ream` before this project is published will get the unrelated parser package.

**Why it happens:**
Package names on PyPI are a global flat namespace. The name `ream` is short and already claimed. The existing package is inactive (51 weekly downloads, no recent releases), but PyPI first-come-first-served ownership means it cannot be reclaimed without going through the PyPI dispute resolution process.

**How to avoid:**
Before publishing: verify the name is unclaimed or claim it. Options in priority order:
1. Claim the `ream` name on PyPI immediately by publishing a placeholder release (even `0.0.1`) to reserve the name, then follow up with the real release.
2. If the existing owner disputes it: use a scoped name like `ream-converter` or `runway-ream`. Do not use underscores (`ream_converter`) as PyPI normalizes `-` and `_` to the same name anyway.
3. If the project is Runway Financial internal-only (likely given the MIT + company copyright), confirm whether PyPI publishing is actually needed — the constraint says "publishable but release is a separate step."

**Warning signs:**
- `pip install ream` in a clean venv installs something other than this project
- `import ream; ream.__version__` returns an unexpected version
- PyPI search for "ream" shows the chmlee parser package as the top result

**Phase to address:**
Package scaffolding phase (Phase 1 / initial pyproject.toml setup). Register the name or decide on a final name before writing any import paths or documentation, since a name change later touches every import statement, README example, and CLI docs.

---

### Pitfall 2: Flat Repo Structure Causes Silent Import Shadowing

**What goes wrong:**
The repo currently has `src/converters.py` at the top level with no package scaffolding. If you create a `ream/` package directory at the repo root and run `pytest` from the repo root *without* installing the package, Python's `sys.path` includes the current directory first. This means `import ream` resolves to the local `ream/` directory regardless of whether the package is installed. Tests pass locally but may behave differently once installed — you're testing the raw source tree, not the installed package.

The inverse is also true: if scripts in `src/` do `from converters import ...` and you move converter logic into `ream/`, those scripts break because `converters` is no longer on the path.

**Why it happens:**
Python always inserts `''` (current working directory) or the script's directory as `sys.path[0]`. A flat layout without `pip install -e .` silently uses the uninstalled source tree instead of the installed package.

**How to avoid:**
Use a strict `src/` layout structure where the installable package lives at `src/ream/` (not `ream/` at repo root). This forces Python to never import `ream` from the working directory — you must `pip install -e .` first. Configure `pyproject.toml` with:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

Pytest configuration should include `addopts = ["--import-mode=importlib"]` and the `src/` path should not be manually added to `PYTHONPATH` in CI.

**Warning signs:**
- Tests pass without running `pip install -e .` first
- `python -c "import ream; print(ream.__file__)"` shows a path inside the repo root rather than `site-packages`
- Deleting the local `ream/` directory causes tests to fail even with the package installed

**Phase to address:**
Phase 1 (project scaffolding). Decide and lock in the layout before writing any code. Changing from flat to `src/` layout after tests are written requires updating all import paths, CI configs, and potentially IDE settings.

---

### Pitfall 3: Breaking Existing Benchmark Scripts During Restructuring

**What goes wrong:**
The constraint says "existing `src/converters.py` must keep working for benchmark scripts." Every script in `src/` currently does `from converters import xlsx_to_ream` or similar. If the REAM conversion logic is moved into a new `ream/` package without a compatibility shim, all 7 existing scripts in `src/` break immediately.

**Why it happens:**
When extracting library code from a research repo, the natural instinct is to delete the old file once the new package exists. But benchmarks, evals, and research scripts often have no tests and no one runs them regularly — breakage is discovered late.

**How to avoid:**
Keep `src/converters.py` intact and have it re-export from the new package as a thin shim:

```python
# src/converters.py — backward compat shim
from ream import xlsx_to_ream
from ream._internal import (
    # re-export research-only converters that aren't part of public API
    xlsx_to_csv, xlsx_to_markdown, ...
)
```

The `ream` package handles public API; `src/converters.py` stays as a passthrough for research scripts. Mark the shim with a deprecation warning if desired, but do not remove it until benchmark scripts are updated.

**Warning signs:**
- `run_eval.py` fails with `ImportError: cannot import name 'xlsx_to_ream' from 'converters'`
- Any `from src.converters import` or `from converters import` at the top of benchmark scripts

**Phase to address:**
Phase 1 (scaffolding) and Phase 2 (public API extraction). The shim strategy must be decided before moving any code.

---

### Pitfall 4: Leaking Internal Implementation into Public API via `__init__.py`

**What goes wrong:**
When writing `ream/__init__.py`, it is tempting to import everything for convenience. This accidentally exposes internal helpers (e.g., `_ream_quote`, `_ream_scalar`, `_cell_value_str`) as part of the public API. Once users import them directly (even undocumented), removing or renaming them becomes a breaking change.

**Why it happens:**
Research code has no distinction between "public" and "internal." When lifting code into a package, the default is to import everything into the top-level namespace to mirror the old import style.

**How to avoid:**
In `ream/__init__.py`, only expose the intended public surface explicitly:

```python
from ream._converter import xlsx_to_ream, bytes_to_ream, file_to_ream
from ream._options import ReamOptions

__all__ = ["xlsx_to_ream", "bytes_to_ream", "file_to_ream", "ReamOptions"]
```

All implementation functions (`_ream_quote`, `_ream_scalar`, etc.) stay in private submodules with underscore prefixes. Document that anything not in `__all__` is internal and subject to change.

**Warning signs:**
- `dir(ream)` shows more than 4-6 names
- Users can do `from ream import _ream_quote` without an `AttributeError`
- No `__all__` defined in `__init__.py`

**Phase to address:**
Phase 2 (public API implementation). Define `__all__` before writing tests — the test suite should only import from `__all__`, which enforces the boundary.

---

### Pitfall 5: CLI Entrypoint `main()` With Arguments

**What goes wrong:**
`console_scripts` entry points call a Python function with *no arguments*. If `main()` in `ream/__main__.py` or `ream/cli.py` is written to accept arguments directly (e.g., `def main(args=None)`), it works fine when called via `argparse` internally. But if the function signature requires arguments at all (i.e., is not callable as `main()`), `setuptools` shim generation will silently install a broken entrypoint that fails at runtime.

The dual entrypoint requirement (`python -m ream` and `ream` command) also has a subtle difference: `python -m ream` executes `__main__.py`; `ream` the CLI command calls the `console_scripts` function. If these diverge in behavior (e.g., different arg parsing, different exit codes), users see inconsistent behavior.

**Why it happens:**
Developers write `__main__.py` and forget to wire it as the console_scripts target, or they add arguments to `main()` while assuming `argparse` handles `sys.argv` internally (it does, but the function signature must still accept zero args).

**How to avoid:**
Wire them both to the same implementation:

```python
# ream/__main__.py
from ream.cli import main
if __name__ == "__main__":
    main()
```

```toml
# pyproject.toml
[project.scripts]
ream = "ream.cli:main"
```

```python
# ream/cli.py
def main():
    # argparse reads from sys.argv internally — no parameters
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    ...
```

**Warning signs:**
- `ream --help` works but `python -m ream --help` behaves differently
- `pip install -e .` installs the `ream` command but it raises `TypeError` on invocation
- `main` function signature has required positional parameters

**Phase to address:**
Phase 3 (CLI implementation). Write a smoke test for both invocation paths before considering CLI done.

---

### Pitfall 6: `python_requires` Upper Bound Locks Out Future Python Versions

**What goes wrong:**
Setting `python_requires = ">=3.10, <3.13"` means the package is unpipable on Python 3.13+. Users on newer Python get `ERROR: Package 'ream' requires a different Python: 3.13.x not in '>=3.10,<3.13'` even though the code likely works fine.

**Why it happens:**
Copying boilerplate from old projects, being overly conservative about untested Python versions, or misreading the `python_requires` semantics. Upper bounds on Python version are almost always wrong for libraries.

**How to avoid:**
Only specify a lower bound:

```toml
[project]
requires-python = ">=3.10"
```

Test against 3.10, 3.11, 3.12, 3.13 in CI. Only add upper bounds if you have confirmed breakage on a specific Python version.

**Warning signs:**
- `pyproject.toml` has `<3.X` in `requires-python`
- CI only tests one Python version

**Phase to address:**
Phase 1 (pyproject.toml scaffolding). Set it correctly once, never revisit.

---

### Pitfall 7: Missing Files in Distributed Package (sdist/wheel)

**What goes wrong:**
`pip install -e .` works perfectly because it reads the live source tree. But a built wheel (`pip install dist/ream-0.1.0-py3-none-any.whl`) may be missing files if `pyproject.toml` package discovery is misconfigured. Common victims: `py.typed` marker (PEP 561), `__init__.pyi` stubs, data files, or the LICENSE file.

**Why it happens:**
`include_package_data` in setuptools defaults to `False`. Files not in the package directory are not auto-included. MANIFEST.in only affects sdists, not wheels. Developers never test the wheel install path because `pip install -e .` always works.

**How to avoid:**
After building (`python -m build`), inspect the wheel contents:

```bash
python -m zipfile -l dist/ream-*.whl
```

Verify all expected files appear. Include `py.typed` for type-checker support:

```toml
[tool.setuptools.package-data]
ream = ["py.typed"]
```

**Warning signs:**
- `import ream` works in editable mode but fails after `pip install dist/ream-*.whl`
- Type checkers report `ream` has no type stubs even though `py.typed` exists in source
- `ream.__version__` raises `AttributeError` in wheel installs

**Phase to address:**
Phase 4 (validation / release prep). Add a CI step that builds the wheel and runs the test suite against the installed wheel (not editable) before the PR merges.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep all 15 converters in a single `converters.py` | Zero restructuring effort | Public package ships with research-only code; hard to remove later without breaking API | Never — isolate public API from research code at day one |
| Skip `__all__` in `__init__.py` | Less boilerplate | Every internal function becomes implicitly public; refactoring breaks users | Never for a published package |
| Pin openpyxl to exact version (`==3.1.3`) | Reproducible behavior | Dependency conflicts in any environment that has a different openpyxl version | Never — use `>=3.1.0` lower bound only |
| Use `setup.py` instead of `pyproject.toml` | More examples available online | setup.py is deprecated; setuptools will eventually drop it | Never for new packages |
| Flat layout (no `src/` directory) | Simpler directory structure | Tests may silently run against uninstalled source; CI false positives | Acceptable only for scripts, never for libraries |
| No `py.typed` marker | One less file | Downstream users get `py.typed not found` from mypy; type inference broken | Never — takes 30 seconds to add |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| openpyxl version pinning | Pinning `openpyxl==3.1.x` exactly in `pyproject.toml` | Use `openpyxl>=3.1.0` — let the resolver pick a compatible version |
| Existing `requirements.txt` | Assuming `requirements.txt` covers package deps | `requirements.txt` is for the research environment only; `pyproject.toml` `[project.dependencies]` is the source of truth for the package |
| pandas in research scripts | Importing pandas in any `ream/` package code | pandas must not be imported anywhere in `ream/` — it is research-only; the package constraint says openpyxl-only |
| `src/converters.py` imports | Research scripts importing directly from `src/` path | The shim approach keeps `converters.py` working; do not add `src/` to the installed package |
| pytest discovery | pytest auto-discovers tests in `src/` and finds non-test files | Place tests in `tests/` at repo root, not inside `src/` or `ream/` |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Non-deterministic REAM output from dict iteration order | Same workbook produces different output on different Python versions | Use `openpyxl` row/column iteration order (already deterministic); avoid `dict.items()` for ordering cell data | Python < 3.7 (insertion-ordered dicts not guaranteed); irrelevant above 3.7 but worth documenting |
| Loading entire workbook into memory for large XLSX files | OOMKill on workbooks with 100k+ rows | Use `openpyxl` read-only mode (`load_workbook(path, read_only=True)`) for streaming | Files > ~50MB |
| `max_rows_per_sheet` not enforced causing runaway output | LLM context window overflow | Enforce `max_rows_per_sheet` default at the `ReamOptions` dataclass level, not as an afterthought | Any large workbook without a row cap |

---

## "Looks Done But Isn't" Checklist

- [ ] **Package installable:** `pip install -e .` works, but does `pip install dist/ream-*.whl` also work? — build the wheel and test it in a fresh venv
- [ ] **CLI registered:** `ream --help` works after install — verify `which ream` points to the installed script, not a local alias
- [ ] **`python -m ream` parity:** same behavior as `ream` command — test both paths in CI
- [ ] **Name not colliding:** `pip install ream` in a clean venv installs *this* package — verify against PyPI before publishing
- [ ] **No pandas import in package code:** `grep -r "import pandas" src/ream/` returns nothing
- [ ] **Backward compat preserved:** `python src/run_eval.py --help` still works after restructuring
- [ ] **`__all__` defined:** `python -c "import ream; print(ream.__all__)"` lists exactly the public API
- [ ] **Type marker present:** `py.typed` file exists in the installed `ream/` package directory
- [ ] **Python version range correct:** `requires-python` has no upper bound

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Name collision discovered after publishing | HIGH | File PyPI dispute resolution, or rename package and update all docs/imports; notify any downstream users |
| Flat layout used, now causing import shadowing | MEDIUM | Create `src/ream/` directory, move files, update `pyproject.toml`, update all import paths in tests and scripts; one-time refactor |
| Research scripts broken by restructuring | LOW | Add `src/converters.py` shim re-exporting from `ream`; no consumer-facing API change |
| Internal helpers leaked into public API | MEDIUM | Deprecate with `DeprecationWarning`, remove in next minor version; document in CHANGELOG |
| Wheel missing files | LOW | Fix `pyproject.toml` package-data config, rebuild, re-release patch version |
| Upper bound `python_requires` blocking users | LOW | Remove upper bound, release patch version |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| PyPI name collision | Phase 1 (scaffolding) | Check PyPI before writing pyproject.toml; register name if needed |
| Import shadowing (flat layout) | Phase 1 (scaffolding) | `pip install -e .` required before any test run; CI fails without it |
| Breaking benchmark scripts | Phase 1 + Phase 2 | Run `python src/run_eval.py` in CI as a smoke test after restructuring |
| Leaking internal API | Phase 2 (public API) | Tests only import from `ream.__all__`; lint rule blocks direct `_` imports in tests |
| CLI entrypoint bug | Phase 3 (CLI) | Smoke test both `ream --help` and `python -m ream --help` in CI |
| Wrong `python_requires` | Phase 1 (scaffolding) | CI matrix includes Python 3.10, 3.11, 3.12, 3.13 |
| Missing files in wheel | Phase 4 (validation) | CI builds wheel, installs in fresh venv, runs full test suite |

---

## Sources

- [Python Packaging User Guide — src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) (official)
- [Writing your pyproject.toml — Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) (official)
- [Entry points specification — Python Packaging User Guide](https://packaging.python.org/specifications/entry-points/) (official)
- [Good Integration Practices — pytest documentation](https://docs.pytest.org/en/stable/explanation/goodpractices.html) (official)
- [Development Mode (Editable Installs) — setuptools](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) (official)
- [Including files in source distributions with MANIFEST.in](https://packaging.python.org/en/latest/guides/using-manifest-in/) (official)
- [Dropping support for older Python versions](https://packaging.python.org/en/latest/guides/dropping-older-python-versions/) (official)
- [Package names conflicts discussion — pypa/packaging-problems #114](https://github.com/pypa/packaging-problems/issues/114) (community)
- [ream package on PyPI — Snyk Advisor](https://snyk.io/advisor/python/ream) (third-party, MEDIUM confidence — name is taken)
- [chmlee/ream-python — GitHub](https://github.com/chmlee/ream-python) (existing conflicting package)
- [8 Common Python Package Management Mistakes to Avoid](https://envelope.dev/blog/8-common-python-package-management-mistakes-to-avoid) (MEDIUM confidence — community blog)

---
*Pitfalls research for: Python packaging of XLSX-to-REAM converter (extracting library from research repo)*
*Researched: 2026-03-30*
