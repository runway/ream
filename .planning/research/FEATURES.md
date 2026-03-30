# Feature Research

**Domain:** Python file-format conversion package (XLSX → REAM text)
**Researched:** 2026-03-30
**Confidence:** HIGH (based on direct analysis of analogous packages: openpyxl, PyYAML, python-markdown, xlrd)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `xlsx_to_ream(path)` — filepath input | Every file-format package accepts a path string as its primary entry point (openpyxl `load_workbook`, xlrd `open_workbook`) | LOW | Already implemented in `src/converters.py`; just needs to be surfaced as the public API |
| `bytes_to_ream(data)` — bytes input | Packages used in web apps or pipelines receive content as bytes, not paths (openpyxl accepts file-like, yaml.safe_load accepts bytes) | LOW | `io.BytesIO` wrapper around existing openpyxl call |
| `file_to_ream(stream)` — file-like input | Standard Python I/O protocol; lets callers pass `open()` handles, `BytesIO`, HTTP response bodies | LOW | Same `io.BytesIO` / openpyxl accepts `BinaryIO` already |
| `ReamOptions` dataclass | Conversion options need a stable, documented, type-annotated surface. Ad-hoc keyword args don't version well and aren't introspectable | LOW | `@dataclass(frozen=True)` with `max_rows_per_sheet`, `force_col_selectors`, `collapse_rows`; already identified in PROJECT.md |
| CLI entrypoint (`ream` / `python -m ream`) | Converter tools are routinely used from the shell or in shell pipelines. Missing CLI = users write wrapper scripts | MEDIUM | argparse (no added dep) is sufficient; must support stdout default and optional `-o FILE` |
| Stdout-by-default CLI | Unix convention — `ream file.xlsx > output.ream` must work without flags | LOW | Print to sys.stdout; exit 0 on success |
| Sensible, named exceptions | Users need to distinguish "file not found" from "not a valid XLSX" from "sheet empty". Raising raw openpyxl exceptions leaks internals | LOW | `ReamError` base, `InvalidWorkbookError`, `ConversionError` hierarchy in `exceptions.py` |
| Deterministic output | Same input → same output on every run. Required for diffs, caching, reproducible benchmarks | LOW | Already a project requirement; must be verified in tests |
| `pyproject.toml` with `[project.scripts]` | Standard packaging since PEP 518/621. `setup.py`-only packages feel unmaintained | LOW | Hatchling or setuptools backend; `ream = "ream.__main__:main"` entry point |
| Minimal dependencies (`openpyxl` only) | Packages with large dependency trees create conflicts. openpyxl is the right call — no pandas, no xlrd | LOW | Already a stated constraint; enforce via `[project.dependencies]` in pyproject.toml |
| `py.typed` marker (PEP 561) | Type checkers (mypy, pyright) silently ignore annotations unless `py.typed` is present. Users who type-check their code get zero benefit without it | LOW | Empty file at `ream/py.typed`; include in package_data |
| Full type annotations on public API | Modern Python packages ship typed APIs. `Any`-heavy signatures erode trust and IDE completion | LOW | `xlsx_to_ream(path: str | Path, options: ReamOptions | None = None) -> str` |
| README quickstart + API reference | Converter packages live or die by copy-pasteable examples. No docs = no adoption | LOW | Install, 3-line example, options table, CLI usage |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `pathlib.Path` acceptance everywhere | Modern Python code uses `Path` objects; requiring `str` is a friction point. `openpyxl.load_workbook` accepts both already | LOW | `str \| Path` union type in signatures; no extra logic needed |
| Version header in output (`#!REAM 11`) | The REAM format has versioned wire formats (v9, v11). Encoding the version in output enables consumers to route parsing logic correctly | LOW | Already part of format spec; must be preserved faithfully in all code paths |
| `collapse_rows` flag (REAM v11 row-span compaction) | Reduces token count further for repeated data. Differentiates REAM from naive row-dump converters | MEDIUM | Already implemented; must be exposed as a first-class `ReamOptions` field |
| `force_col_selectors` flag | Lets callers trade token efficiency for maximal explicitness (useful when feeding to weaker models) | LOW | Already implemented; expose as `ReamOptions` field |
| `max_rows_per_sheet` cap with truncation marker | Prevents silent context-window blowup for large workbooks. LLM-facing tools need this guard by default | LOW | Default 500; emit truncation comment in output when capped |
| `__all__` explicit export list | Makes `from ream import *` safe and communicates the public API surface unambiguously | LOW | `__all__ = ["xlsx_to_ream", "bytes_to_ream", "file_to_ream", "ReamOptions", "ReamError", ...]` |
| `read_only=True` mode passed to openpyxl | Significant memory reduction for large workbooks; openpyxl supports it. Most wrappers don't expose it | LOW | Pass `read_only=True, data_only=True` in all load calls; already efficient since we only read values |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Other format converters in public API (CSV, JSON, Markdown, HTML) | Converters for these exist in `src/converters.py` and users may want them | Explodes the package surface; other formats are research artifacts not production-hardened; versioning and maintenance cost multiplies with each format | Keep them in `src/converters.py` as internal/research tools. If demand exists, publish as separate packages later |
| Async / `asyncio` support | Web frameworks use async; callers may want `await xlsx_to_ream(...)` | openpyxl is synchronous file I/O; wrapping in `asyncio.to_thread` adds complexity with zero throughput benefit for single-file conversion | Callers who need async can wrap with `asyncio.to_thread(xlsx_to_ream, path)` — document this pattern in the README |
| Streaming / incremental output | Large workbooks might benefit from yielding output line-by-line | REAM format requires multi-pass decisions (e.g., row-span collapse, column selector optimization) that cannot be done in a single forward pass over the file | Accept `max_rows_per_sheet` to bound output size; streaming adds API complexity with no clear user benefit at this scale |
| PyPI auto-publishing in CI | Convenient for maintainers | Mixes packaging concerns with conversion logic; CI/CD publishing is infrastructure, not a package feature | Package must be *publishable* (correct `pyproject.toml`, `CHANGELOG`, version), but the publish step is a separate repo/workflow concern (out of scope per PROJECT.md) |
| Plugin/extension system | Power users want to customize cell serialization, add custom directives | Premature generalization; REAM format is spec-defined and stable. Plugin hooks create surface area before the format has external adopters | Expose `ReamOptions` for all known knobs; accept format spec PRs through the spec document |
| Pandas/numpy integration | Data scientists work in DataFrames and may want `df_to_ream()` | Adds pandas as a required dependency (400MB+ install), defeating the minimal-footprint goal | Document how to write a temp XLSX from a DataFrame and pass it to `xlsx_to_ream`; pandas is a research dep only |

---

## Feature Dependencies

```
ReamOptions (dataclass)
    └──required by──> xlsx_to_ream(path, options)
    └──required by──> bytes_to_ream(data, options)
    └──required by──> file_to_ream(stream, options)

file_to_ream(stream)
    └──implements──> bytes_to_ream (wraps BytesIO)
    └──implements──> xlsx_to_ream (wraps open())

ReamError hierarchy (exceptions.py)
    └──used by──> all three public API functions

py.typed marker
    └──enables──> type annotations to be honored by mypy/pyright

CLI (__main__.py)
    └──calls──> xlsx_to_ream or file_to_ream
    └──uses──> ReamOptions (maps flags to fields)
    └──raises──> ReamError (converts to exit code 1 + stderr message)

pyproject.toml [project.scripts]
    └──requires──> __main__.py:main entry point
```

### Dependency Notes

- **`bytes_to_ream` and `file_to_ream` require `ReamOptions`:** All input-type variants share the same options surface; options must exist before any input variant can be designed
- **CLI requires `ReamOptions`:** CLI flags (`--max-rows`, `--force-col-selectors`, `--collapse-rows`) are a direct mapping onto `ReamOptions` fields; the dataclass must be stable before the CLI argument parser is written
- **`py.typed` requires full type annotations:** There is no value shipping `py.typed` with unannotated public functions; type annotations must be complete on all public symbols first
- **`ReamError` hierarchy enables clean CLI exit codes:** The CLI catch block can convert `InvalidWorkbookError` → exit 1 + specific message without inspecting raw openpyxl exceptions

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] `xlsx_to_ream(path, options)` — primary entry point; what 90% of callers use
- [ ] `bytes_to_ream(data, options)` — required for in-memory and web use cases
- [ ] `file_to_ream(stream, options)` — required for pipe/stream use cases
- [ ] `ReamOptions` frozen dataclass — stable options API; all three converters depend on it
- [ ] `ReamError`, `InvalidWorkbookError`, `ConversionError` — clean error surface; don't leak openpyxl internals
- [ ] `ream` CLI + `python -m ream` — makes the package useful as a shell tool; stdout default + `-o FILE` flag + key option flags
- [ ] Full type annotations + `py.typed` marker — needed from day one; retrofitting is painful and breaks adopters' type checks
- [ ] `pyproject.toml` with `[project.scripts]` entry point — modern packaging; `pip install -e .` must work

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] `pathlib.Path` union type in all signatures — ergonomic improvement; add when first user friction report comes in
- [ ] `--sheet` CLI flag for single-sheet extraction — likely first requested CLI feature; add when use cases confirm it
- [ ] Version introspection (`ream.__version__`) — useful for debugging reports; trivial to add

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Additional output options (sheet selection, include/exclude named ranges) — only if format spec evolves to support them
- [ ] Performance profiling + `read_only` flag exposure as `ReamOptions` field — relevant only if benchmark shows bottleneck at >10MB files
- [ ] Separate packages for other converters (CSV, JSON, Markdown) — only if external demand materializes

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| `xlsx_to_ream(path)` | HIGH | LOW | P1 |
| `bytes_to_ream(data)` | HIGH | LOW | P1 |
| `file_to_ream(stream)` | HIGH | LOW | P1 |
| `ReamOptions` dataclass | HIGH | LOW | P1 |
| `ReamError` exception hierarchy | HIGH | LOW | P1 |
| CLI (`ream` / `python -m ream`) | HIGH | MEDIUM | P1 |
| Full type annotations | HIGH | LOW | P1 |
| `py.typed` marker | MEDIUM | LOW | P1 |
| `pyproject.toml` packaging | HIGH | LOW | P1 |
| Deterministic output guarantee | HIGH | LOW | P1 |
| `pathlib.Path` acceptance | MEDIUM | LOW | P2 |
| `max_rows_per_sheet` truncation marker in output | MEDIUM | LOW | P2 |
| `__all__` explicit exports | MEDIUM | LOW | P2 |
| Version introspection (`__version__`) | LOW | LOW | P2 |
| `--sheet` CLI flag | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | openpyxl | PyYAML | python-markdown | Our Approach |
|---------|----------|--------|-----------------|--------------|
| Input types | `str`, `Path`, `BinaryIO` | `str`, `bytes`, file-like | `str`, file-like | All three: `str/Path`, `bytes`, `BinaryIO` |
| Options API | keyword args on `load_workbook()` | `Loader` class parameter | `Extension` list + keyword kwargs | `ReamOptions` frozen dataclass — more discoverable, typed, extensible |
| CLI | None | None | `python -m markdown` | `ream` command + `python -m ream` — follows python-markdown pattern |
| Exceptions | `InvalidFileException`, `CellCoordinatesException` | `YAMLError` subclasses | `MarkdownException` | `ReamError` base + typed subclasses |
| Type annotations | Partial | Partial (via types-PyYAML stub package) | Partial | Full inline annotations + `py.typed` from day one |
| Stdout default | N/A | N/A | Yes (writes to stdout) | Yes — `ream file.xlsx` prints to stdout |

---

## Sources

- openpyxl API reference: https://openpyxl.readthedocs.io/en/stable/tutorial.html (HIGH confidence — official docs)
- PyYAML public API pattern: https://python.land/data-processing/python-yaml (MEDIUM confidence — tutorial, consistent with official docs)
- PEP 561 `py.typed` marker: https://peps.python.org/pep-0561/ (HIGH confidence — official PEP)
- Python packaging `pyproject.toml`: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/ (HIGH confidence — official PyPA guide)
- CLI patterns (argparse / stdin-or-file): https://chris48s.github.io/blogmarks/posts/2020/stdin-or-file/ (MEDIUM confidence — community, consistent with stdlib docs)
- Python exception hierarchy best practices: https://jacobpadilla.com/articles/custom-python-exceptions (MEDIUM confidence — community, consistent with official docs)
- Python typing distribution: https://typing.python.org/en/latest/spec/distributing.html (HIGH confidence — official typing spec)
- Click vs argparse comparison (2025): https://dasroot.net/posts/2025/12/building-cli-tools-python-click-typer-argparse/ (MEDIUM confidence — community)

---

*Feature research for: Python file-format conversion package (XLSX to REAM)*
*Researched: 2026-03-30*
