---
phase: 03-cli
plan: 01
subsystem: cli
tags: [click, cli, pytest, mypy, ruff]

# Dependency graph
requires:
  - phase: 02-core-api
    provides: xlsx_to_ream, ReamOptions, ReamError, InvalidWorkbookError from ream_xlsx public API
provides:
  - ream-xlsx CLI command via ream_xlsx/_cli.py
  - python -m ream_xlsx entrypoint via ream_xlsx/__main__.py
  - CLI tests in tests/test_cli.py (13 tests)
affects: [04-docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Click command with argument + options pattern (no click.Path(exists=True) to preserve error format)
    - ReamError caught at CLI boundary, formatted as 'error: {exc}' to stderr with sys.exit(1)
    - click.version_option(package_name=...) reads version from importlib.metadata automatically

key-files:
  created:
    - ream_xlsx/_cli.py
    - ream_xlsx/__main__.py
    - tests/test_cli.py
  modified: []

key-decisions:
  - "No click.Path(exists=True) on input_file argument: preserves 'error:' prefix format (D-04)"
  - "click.echo(result) with default nl=True provides exactly one trailing newline per D-06 spec"
  - "File output writes result + newline to match stdout trailing newline behavior"

patterns-established:
  - "TDD RED-GREEN: write failing tests first, then implement to make them pass"
  - "CLI error format: 'error: {exc message}' to stderr, exit code 1 for ReamError"
  - "CliRunner tests: use result.stdout/result.stderr, never result.output; no mix_stderr"

requirements-completed: [CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-06, TST-07, TST-08]

# Metrics
duration: 2min
completed: 2026-03-30
---

# Phase 3 Plan 01: CLI Command and Module Entrypoint Summary

**Click CLI with `ream-xlsx` command and `python -m ream_xlsx` entrypoint, 13 passing tests covering success and error paths**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-30T00:30:06Z
- **Completed:** 2026-03-30T00:32:00Z
- **Tasks:** 2 (RED + GREEN TDD cycle)
- **Files modified:** 3

## Accomplishments

- Implemented `ream_xlsx/_cli.py` with Click command, all five flags (`-o`, `--max-rows`, `--collapse-rows`, `--force-col-selectors`, `--version`) and proper error handling
- Implemented `ream_xlsx/__main__.py` to enable `python -m ream_xlsx` invocation
- Created `tests/test_cli.py` with 13 tests covering TST-07 (9 success cases) and TST-08 (4 error cases)
- Full test suite: 49/49 passing; mypy strict and ruff clean on all ream_xlsx/ modules

## Task Commits

1. **Task 1: Write CLI tests (RED phase)** - `b5b6b58` (test)
2. **Task 2: Implement CLI command and module entrypoint (GREEN phase)** - `e2daed0` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified

- `tests/test_cli.py` - 13 CLI tests using CliRunner and subprocess
- `ream_xlsx/_cli.py` - Click command wrapping xlsx_to_ream with all option flags
- `ream_xlsx/__main__.py` - python -m ream_xlsx entrypoint

## Decisions Made

- No `click.Path(exists=True)` on the input argument: Click's built-in error format would bypass our `error:` prefix requirement (D-04); we catch `ReamError` instead
- `click.echo(result)` with `nl=True` (default) adds exactly one trailing newline matching D-06 spec; converter returns no trailing newline itself
- File output writes `result + "\n"` to match stdout trailing newline behavior consistently

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CLI complete and fully tested; ready for Phase 4 documentation
- Package can be installed (`pip install -e .`) and `ream-xlsx` is available on PATH

---
*Phase: 03-cli*
*Completed: 2026-03-30*
