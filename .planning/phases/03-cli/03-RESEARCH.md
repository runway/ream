# Phase 03: CLI - Research

**Researched:** 2026-03-30
**Domain:** Click CLI, Python entry points, `__main__.py`, `importlib.metadata`
**Confidence:** HIGH

## Summary

Phase 03 adds the `ream-xlsx` command-line interface and the `python -m ream_xlsx` entrypoint. The groundwork is almost entirely done: `pyproject.toml` already declares `ream-xlsx = "ream_xlsx._cli:main"`, Click 8.3.1 is installed, and the Phase 2 public API (`xlsx_to_ream`, `ReamOptions`, exception hierarchy) is complete and tested. The only files that need to be created are `ream_xlsx/_cli.py` and `ream_xlsx/__main__.py`.

The implementation is straightforward: a single Click command in `_cli.py` wraps `xlsx_to_ream`, maps flags to `ReamOptions` fields, handles exceptions with `sys.exit(1)` + stderr message, and writes output to stdout or a file. `__main__.py` delegates to `_cli:main`. Tests use Click's `CliRunner` (available in Click 8.3.1), which provides `result.exit_code`, `result.stdout`, and `result.stderr` as separate streams.

**Primary recommendation:** Implement `_cli.py` as a single `@click.command` function with no helper decomposition needed at this scope. Use `CliRunner(mix_stderr=False)` — note this parameter was **removed in Click 8.2**; stderr is now always separate and accessed via `result.stderr`. Use `catch_exceptions=False` in `CliRunner.invoke` for tests that test happy paths (where Python exceptions should propagate as test failures, not be swallowed).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `--max-rows` flag (short name, maps to `ReamOptions.max_rows_per_sheet` internally)
- **D-02:** Boolean flags use simple `--flag` style (e.g., `--collapse-rows`, `--force-col-selectors`). No `--no-*` pairs needed since defaults are False.
- **D-03:** Only short flag is `-o` for output file. Other flags use long names only.
- **D-04:** Errors print to stderr with lowercase prefix: `error: file not found: path.xlsx`. No tracebacks, include the file path in the message.
- **D-05:** No "try --help" hints on errors. Keep stderr clean for scripted usage.
- **D-06:** Output includes a trailing newline (POSIX convention, Click default).
- **D-07:** Single input file only. No multi-file support in v1.
- **D-08:** Include `--version` flag now using Click's `@click.version_option` with `importlib.metadata` to read version from `pyproject.toml`.
- **D-09:** Use Click's default `--help` formatting. No custom header or styling.

### Claude's Discretion

- Internal structure of `_cli.py` (single function vs helpers)
- `__main__.py` implementation (simple delegation to `_cli:main`)
- Click test strategy (CliRunner vs subprocess)
- Error message exact wording beyond the `error:` prefix pattern

### Deferred Ideas (OUT OF SCOPE)

- Multi-file input support (multiple positional args) — potential v2 feature
- `--sheet` flag for single-sheet extraction (tracked as OPT-02 in REQUIREMENTS.md)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLI-01 | `ream-xlsx input.xlsx` command works via `[project.scripts]` entrypoint | `pyproject.toml` already declares entry point; only `_cli.py` needs to be created |
| CLI-02 | `python -m ream_xlsx input.xlsx` works via `__main__.py` | Create `ream_xlsx/__main__.py` that calls `from ream_xlsx._cli import main; main()` |
| CLI-03 | Output to stdout by default | Click's `echo()` writes to stdout; no `-o` flag means default path |
| CLI-04 | `-o FILE` flag writes output to file instead of stdout | `@click.option("-o", "--output", type=click.Path())` then `open(output, "w")` |
| CLI-05 | `--max-rows`, `--force-col-selectors`, `--collapse-rows` flags map to `ReamOptions` | Flags construct `ReamOptions(max_rows_per_sheet=..., force_col_selectors=..., collapse_rows=...)` |
| CLI-06 | Exit code 1 + stderr message on invalid input | Catch `ReamError` (covers both subclasses), write to `sys.stderr`, call `sys.exit(1)` |
| TST-07 | Tests for CLI success cases and output correctness | `CliRunner.invoke` with `catch_exceptions=False`, assert `result.exit_code == 0`, assert `result.stdout` content |
| TST-08 | Tests for error handling (missing file, invalid XLSX, empty workbook) | `CliRunner.invoke` without `catch_exceptions=False`, assert `result.exit_code == 1`, assert `result.stderr` contains `error:` prefix |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | 8.3.1 (installed) | CLI framework: decorators, option parsing, testing | Already in project dependencies; chosen over argparse/Typer in pre-Phase-1 decisions |
| importlib.metadata | stdlib (Python 3.10+) | Read package version at runtime | Required by D-08; no extra dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| click.testing.CliRunner | bundled with click | In-process CLI test runner | TST-07, TST-08 — avoids subprocess overhead, captures stdout/stderr separately |
| sys | stdlib | `sys.exit(1)`, `sys.stderr.write()` | Error handling path in _cli.py |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CliRunner | subprocess.run | subprocess tests real shell integration but is slower and harder to assert on; CliRunner is standard for unit testing Click apps |
| `click.echo(result, err=True)` | `sys.stderr.write()` | Both work; `click.echo(err=True)` is idiomatic Click and handles encoding edge cases automatically |

**Installation:** No new dependencies needed. Click is already in `[project.dependencies]`.

**Version verification (confirmed live):**
- click 8.3.1 installed in `.venv`
- pytest 9.0.2 installed in `.venv`
- Python 3.14.2 in venv (>= 3.10 requirement met)

## Architecture Patterns

### Recommended Project Structure

Two new files:

```
ream_xlsx/
├── __init__.py        # existing — no changes
├── __main__.py        # NEW — 2 lines: import main, call main()
├── _cli.py            # NEW — single @click.command function
├── _converter.py      # existing
├── _exceptions.py     # existing
├── _io.py             # existing
└── _options.py        # existing
tests/
└── test_cli.py        # NEW — CliRunner-based tests for TST-07, TST-08
```

### Pattern 1: Single Click Command Function

**What:** One `@click.command` decorated function in `_cli.py`. No sub-commands, no group.
**When to use:** Any CLI with a single operation and no sub-command routing.

```python
# ream_xlsx/_cli.py
from __future__ import annotations

import sys
from pathlib import Path

import click

from ream_xlsx import ReamOptions, xlsx_to_ream
from ream_xlsx._exceptions import ReamError


@click.command()
@click.version_option(package_name="ream-xlsx")
@click.argument("input_file", type=click.Path(exists=False))
@click.option("-o", "--output", "output_file", default=None, help="Write output to FILE instead of stdout.")
@click.option("--max-rows", "max_rows", default=500, show_default=True, help="Maximum rows per sheet.")
@click.option("--collapse-rows", "collapse_rows", is_flag=True, default=False, help="Collapse identical adjacent rows.")
@click.option("--force-col-selectors", "force_col_selectors", is_flag=True, default=False, help="Force column selectors in output.")
def main(
    input_file: str,
    output_file: str | None,
    max_rows: int,
    collapse_rows: bool,
    force_col_selectors: bool,
) -> None:
    """Convert an XLSX workbook to REAM text format."""
    options = ReamOptions(
        max_rows_per_sheet=max_rows,
        collapse_rows=collapse_rows,
        force_col_selectors=force_col_selectors,
    )
    try:
        result = xlsx_to_ream(input_file, options)
    except ReamError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    if output_file is not None:
        Path(output_file).write_text(result, encoding="utf-8")
    else:
        click.echo(result, nl=False)
```

**Note on trailing newline (D-06):** `xlsx_to_ream` returns the REAM string. If the string already ends with `\n`, use `nl=False` in `click.echo` to avoid a double newline. Verify the actual output of `_xlsx_to_ream_impl` during implementation and adjust accordingly.

### Pattern 2: `__main__.py` Delegation

**What:** Minimal two-line module enabling `python -m ream_xlsx`.
**When to use:** Always, when module execution support is needed.

```python
# ream_xlsx/__main__.py
from ream_xlsx._cli import main

main()
```

### Pattern 3: CliRunner Tests with Separate Stderr (Click 8.2+)

**What:** Use `CliRunner()` without `mix_stderr` (removed in 8.2). Access `result.stdout` and `result.stderr` directly.
**When to use:** TST-07 (success cases) and TST-08 (error cases).

```python
# tests/test_cli.py
from click.testing import CliRunner
from ream_xlsx._cli import main

def test_stdout_output(tmp_xlsx):
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_xlsx)], catch_exceptions=False)
    assert result.exit_code == 0
    assert len(result.stdout) > 0

def test_missing_file_exit_code():
    runner = CliRunner()
    result = runner.invoke(main, ["nonexistent.xlsx"])
    assert result.exit_code == 1
    assert result.stderr.startswith("error:")
```

**CRITICAL Click 8.2+ change:** `mix_stderr` parameter was **removed** from `CliRunner` in Click 8.2. Stderr is now always captured separately. `result.stderr` is always available. Do NOT pass `mix_stderr=False` — it will raise `TypeError`. Source: verified against Click 8.3.1 source in `.venv`.

### Pattern 4: Error Message Format (D-04)

**What:** Lowercase `error:` prefix, no traceback, include file path.
**Examples:**
- `error: file not found: missing.xlsx`
- `error: invalid workbook: data.xlsx is not a valid XLSX file`
- `error: conversion failed: ...`

The catch block uses `click.echo(f"error: {exc}", err=True)` — the exception message from `InvalidWorkbookError` / `ConversionError` already contains path information when raised by `_io.py`.

### Anti-Patterns to Avoid

- **`mix_stderr=False` in CliRunner:** Removed in Click 8.2. Will raise `TypeError` in the installed 8.3.1. Use `result.stderr` directly.
- **`@click.argument(..., type=click.Path(exists=True))`:** This raises a Click-level error (not `ReamError`) before reaching our handler, producing Click's default "Error: Invalid value..." message on stderr rather than our `error:` prefix. Use `exists=False` and validate manually in the function body, or catch `click.BadParameter`.
- **`result.output` for stderr checks in tests:** In Click 8.2+, `result.output` is the mixed stdout+stderr terminal view. Use `result.stderr` to assert on error messages specifically.
- **Double trailing newline:** If `xlsx_to_ream` returns a string ending in `\n`, using `click.echo(result)` (which adds another `\n`) produces double newlines. Use `click.echo(result, nl=False)` or strip and let Click add one.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Version reading | `open("pyproject.toml")` parse | `@click.version_option(package_name="ream-xlsx")` | Click calls `importlib.metadata.version("ream-xlsx")` internally |
| Argument parsing | Manual `sys.argv` parsing | Click decorators | Edge cases with quoting, help formatting, short flags |
| Stderr/stdout separation in tests | subprocess + pipe wrangling | `CliRunner` | In-process, captures both streams, no shell dependency |
| Help text formatting | Custom `--help` handler | Click default | D-09 explicitly requires Click default |

**Key insight:** Click's `version_option` with `package_name` reads from `importlib.metadata` automatically — no need to import `importlib.metadata` directly in `_cli.py`.

## Common Pitfalls

### Pitfall 1: `mix_stderr` Removed in Click 8.2

**What goes wrong:** Code or Stack Overflow examples from pre-8.2 use `CliRunner(mix_stderr=False)`. This raises `TypeError` in 8.3.1.
**Why it happens:** Click 8.2 changed stderr handling — it is now always separate.
**How to avoid:** Use `CliRunner()` with no arguments. Access `result.stderr` directly.
**Warning signs:** `TypeError: __init__() got an unexpected keyword argument 'mix_stderr'`

### Pitfall 2: `click.Path(exists=True)` Bypasses Error Handler

**What goes wrong:** If the argument uses `exists=True`, Click validates the file existence before the command body runs and prints `Error: Invalid value for 'INPUT_FILE': Path 'x' does not exist.` — not our `error:` prefix format.
**Why it happens:** Click performs parameter validation before calling the decorated function.
**How to avoid:** Use `type=click.Path(exists=False)` (or omit `exists`) and let `xlsx_to_ream` raise `InvalidWorkbookError` which we catch and format per D-04.
**Warning signs:** Test for `error:` prefix fails; stderr contains `Error: Invalid value`.

### Pitfall 3: mypy strict + Click Decorators

**What goes wrong:** `mypy --strict` may flag the `main` function's return type or parameter types when using Click decorators.
**Why it happens:** Click decorators transform function signatures in ways mypy needs hints about.
**How to avoid:** Add explicit type annotations to all parameters of `main`. Use `-> None` return type. The `from __future__ import annotations` pattern already used project-wide handles forward refs.
**Warning signs:** `error: Untyped decorator makes function "main" partially unknown`

### Pitfall 4: Trailing Newline Double-Add

**What goes wrong:** If `xlsx_to_ream` already returns a string ending in `\n`, and `click.echo(result)` adds another `\n`, the output has an extra blank line.
**Why it happens:** `click.echo` appends `\n` by default (`nl=True`).
**How to avoid:** Inspect `_xlsx_to_ream_impl` output format. If it ends with `\n`, use `click.echo(result, nl=False)`. If not, use default `click.echo(result)`.
**Warning signs:** Output ends with `\n\n` in tests; D-06 says "trailing newline" (one, not two).

### Pitfall 5: `result.output` vs `result.stdout` in Tests

**What goes wrong:** `result.output` in Click 8.2+ is the mixed stdout+stderr view (as a user sees in terminal). Using it to assert on pure stdout content may include error noise.
**Why it happens:** Click 8.2 changed `output` to be the terminal-view stream.
**How to avoid:** Use `result.stdout` for success output assertions, `result.stderr` for error message assertions.
**Warning signs:** Tests pass individually but fail when error messages bleed into output assertions.

## Code Examples

Verified patterns from installed Click 8.3.1:

### CliRunner Invocation (Correct for Click 8.2+)

```python
# Source: Click 8.3.1 .venv/lib/python3.14/site-packages/click/testing.py
from click.testing import CliRunner
from ream_xlsx._cli import main

runner = CliRunner()
# Success path — catch_exceptions=False lets Python exceptions propagate as test failures
result = runner.invoke(main, ["input.xlsx"], catch_exceptions=False)
assert result.exit_code == 0
assert result.stdout  # non-empty

# Error path — catch_exceptions defaults to True (swallows sys.exit)
result = runner.invoke(main, ["missing.xlsx"])
assert result.exit_code == 1
assert "error:" in result.stderr
```

### `version_option` with `importlib.metadata`

```python
# Source: Click 8.3.1 source — version_option calls importlib.metadata.version(package_name) internally
@click.version_option(package_name="ream-xlsx")
```

The package name must match the `[project] name` in `pyproject.toml` exactly (`"ream-xlsx"`). The installed version is `0.1.0`.

### `__main__.py` Minimal Pattern

```python
# ream_xlsx/__main__.py
from ream_xlsx._cli import main

main()
```

This is the complete file. No `if __name__ == "__main__":` guard needed — `python -m ream_xlsx` always executes `__main__.py` as a script.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `CliRunner(mix_stderr=False)` | `CliRunner()` — stderr always separate | Click 8.2 | Do not pass `mix_stderr`; `result.stderr` always available |
| `result.output` for stdout | `result.stdout` | Click 8.2 | `result.output` is now mixed terminal view |
| Manual `importlib.metadata.version()` call | `@click.version_option(package_name=...)` | Click 8.x | Click handles metadata lookup automatically |

**Deprecated/outdated:**
- `CliRunner(mix_stderr=False)`: Raises `TypeError` in Click 8.2+. All internet examples pre-8.2 using this will break.

## Open Questions

1. **Trailing newline in `xlsx_to_ream` output**
   - What we know: D-06 requires a trailing newline in CLI output; `click.echo` adds one by default
   - What's unclear: Whether `_xlsx_to_ream_impl` already appends `\n` to its return value
   - Recommendation: Implementer should run `repr(xlsx_to_ream(sample))` in a REPL or check `_converter.py` before choosing `nl=True` vs `nl=False` in `click.echo`

2. **`InvalidWorkbookError` message content from `_io.py`**
   - What we know: D-04 requires the file path in the error message; D-04's example is `error: file not found: path.xlsx`
   - What's unclear: Whether `_io.py`'s `InvalidWorkbookError` messages already include the path, or if `_cli.py` needs to construct the message differently
   - Recommendation: Read `_io.py` before implementing the catch block; if path is not in the exception message, format as `f"error: {exc}: {input_file}"` in the catch clause

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.14.2 (venv) | — |
| click | CLI framework | Yes | 8.3.1 | — |
| pytest | TST-07, TST-08 | Yes | 9.0.2 | — |
| ream-xlsx package (editable install) | `CliRunner` tests import `_cli` | Yes | 0.1.0 (`ream-xlsx` binary in venv) | — |
| mypy | Type checking | Yes | in venv | — |
| ruff | Linting | Yes | in venv | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `.venv/bin/pytest tests/test_cli.py -x` |
| Full suite command | `.venv/bin/pytest tests/` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | `ream-xlsx input.xlsx` exits 0, prints REAM to stdout | integration (CliRunner) | `.venv/bin/pytest tests/test_cli.py::test_stdout_success -x` | No — Wave 0 |
| CLI-02 | `python -m ream_xlsx input.xlsx` produces identical output | unit | `.venv/bin/pytest tests/test_cli.py::test_module_invocation -x` | No — Wave 0 |
| CLI-03 | No `-o` flag: output to stdout | unit | `.venv/bin/pytest tests/test_cli.py::test_stdout_default -x` | No — Wave 0 |
| CLI-04 | `-o out.txt` writes to file, nothing to stdout | unit | `.venv/bin/pytest tests/test_cli.py::test_output_file -x` | No — Wave 0 |
| CLI-05 | `--max-rows`, `--collapse-rows`, `--force-col-selectors` apply to `ReamOptions` | unit | `.venv/bin/pytest tests/test_cli.py::test_flags_apply -x` | No — Wave 0 |
| CLI-06 | Missing file: exit 1, `error:` on stderr | unit | `.venv/bin/pytest tests/test_cli.py::test_missing_file_error -x` | No — Wave 0 |
| TST-07 | CLI success cases with correct output | unit | `.venv/bin/pytest tests/test_cli.py -k "success" -x` | No — Wave 0 |
| TST-08 | Error handling: missing file, invalid XLSX, bad input | unit | `.venv/bin/pytest tests/test_cli.py -k "error" -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `.venv/bin/pytest tests/test_cli.py -x`
- **Per wave merge:** `.venv/bin/pytest tests/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_cli.py` — covers all CLI-01 through CLI-06, TST-07, TST-08 (file does not exist yet)
- [ ] `ream_xlsx/_cli.py` — implementation file (does not exist yet)
- [ ] `ream_xlsx/__main__.py` — module entrypoint (does not exist yet)

*(No framework installation needed — pytest, Click, and CliRunner are all available in `.venv`)*

## Sources

### Primary (HIGH confidence)

- Click 8.3.1 source in `.venv/lib/python3.14/site-packages/click/` — CliRunner API, Result attributes, `mix_stderr` removal, `version_option` signature — verified by live inspection
- `pyproject.toml` — confirmed entry point declaration, Click version constraint, Python version requirement
- `ream_xlsx/_options.py` — confirmed `ReamOptions` field names: `max_rows_per_sheet`, `force_col_selectors`, `collapse_rows`
- `ream_xlsx/_exceptions.py` — confirmed exception class names: `ReamError`, `InvalidWorkbookError`, `ConversionError`
- `ream_xlsx/__init__.py` — confirmed `xlsx_to_ream(path, options)` signature

### Secondary (MEDIUM confidence)

- `.planning/phases/03-cli/03-CONTEXT.md` — locked decisions D-01 through D-09

### Tertiary (LOW confidence)

- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — confirmed live against installed packages
- Architecture: HIGH — based on actual API inspection of Click 8.3.1 + existing codebase
- Pitfalls: HIGH — `mix_stderr` removal verified directly from Click 8.3.1 source
- Test patterns: HIGH — verified `CliRunner.invoke` signature and `Result` attributes live

**Research date:** 2026-03-30
**Valid until:** 2026-06-30 (stable domain — Click 8.x, Python stdlib)
