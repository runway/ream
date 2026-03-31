# Phase 3: CLI - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the `ream-xlsx` CLI command and `python -m ream_xlsx` entrypoint using Click. Single input file, stdout or file output, all `ReamOptions` fields as flags, clean error handling. No multi-file support, no interactive features.

</domain>

<decisions>
## Implementation Decisions

### Flag design
- **D-01:** `--max-rows` flag (short name, maps to `ReamOptions.max_rows_per_sheet` internally)
- **D-02:** Boolean flags use simple `--flag` style (e.g., `--collapse-rows`, `--force-col-selectors`). No `--no-*` pairs needed since defaults are False.
- **D-03:** Only short flag is `-o` for output file. Other flags use long names only.

### Error output formatting
- **D-04:** Errors print to stderr with lowercase prefix: `error: file not found: path.xlsx`. No tracebacks, include the file path in the message.
- **D-05:** No "try --help" hints on errors. Keep stderr clean for scripted usage.

### Output behavior
- **D-06:** Output includes a trailing newline (POSIX convention, Click default).
- **D-07:** Single input file only. No multi-file support in v1.

### Version & help
- **D-08:** Include `--version` flag now using Click's `@click.version_option` with `importlib.metadata` to read version from `pyproject.toml`.
- **D-09:** Use Click's default `--help` formatting. No custom header or styling.

### Claude's Discretion
- Internal structure of `_cli.py` (single function vs helpers)
- `__main__.py` implementation (simple delegation to `_cli:main`)
- Click test strategy (CliRunner vs subprocess)
- Error message exact wording beyond the `error:` prefix pattern

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Package config
- `pyproject.toml` -- `[project.scripts]` declares `ream-xlsx = "ream_xlsx._cli:main"`, version string, Click dependency

### Public API (Phase 2 outputs)
- `ream_xlsx/__init__.py` -- Public functions `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream` and exception hierarchy
- `ream_xlsx/_options.py` -- `ReamOptions` frozen dataclass with field names and defaults
- `ream_xlsx/_exceptions.py` -- `ReamError`, `InvalidWorkbookError`, `ConversionError`

### Requirements
- `.planning/REQUIREMENTS.md` -- CLI-01 through CLI-06, TST-07, TST-08

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ream_xlsx/__init__.py`: `xlsx_to_ream(path, options)` is the primary function the CLI wraps
- `ream_xlsx/_options.py`: `ReamOptions` dataclass -- CLI flags map directly to its fields
- `ream_xlsx/_exceptions.py`: `InvalidWorkbookError`, `ConversionError` -- CLI catches these for exit code 1

### Established Patterns
- All config in `pyproject.toml` (no separate tool configs)
- Tests in `tests/` directory, TDD approach
- ruff + mypy strict + pytest as dev toolchain
- Private modules prefixed with `_` (e.g., `_cli.py`, `_converter.py`, `_io.py`)

### Integration Points
- `pyproject.toml [project.scripts]`: `ream-xlsx = "ream_xlsx._cli:main"` -- already declared
- `ream_xlsx/__main__.py`: Needs to be created for `python -m ream_xlsx` support
- Click is already in `[project.dependencies]`

</code_context>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

- Multi-file input support (multiple positional args) -- potential v2 feature
- `--sheet` flag for single-sheet extraction (tracked as OPT-02 in REQUIREMENTS.md)

</deferred>

---

*Phase: 03-cli*
*Context gathered: 2026-03-31*
