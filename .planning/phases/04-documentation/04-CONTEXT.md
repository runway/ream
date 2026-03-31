# Phase 4: Documentation - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete README documentation (install, quickstart, API reference, CLI usage, developer guide), move existing benchmark content to BENCHMARK.md, validate built wheel in a clean environment. All documentation lives in a single README.md.

</domain>

<decisions>
## Implementation Decisions

### README strategy
- **D-01:** Replace the current README.md entirely. The new README is about the `ream-xlsx` package — installation, API, CLI, developer guide. The package is the primary artifact.
- **D-02:** Move the current benchmark/research README content to `BENCHMARK.md` at the repo root. Link from the new README: "See BENCHMARK.md for research evaluation details."
- **D-03:** All documentation lives in a single `README.md` — no `docs/` directory. Sections: Install, Quickstart, API Reference, CLI Usage, Developer Guide. The package is small enough for one file.

### Claude's Discretion
- Exact section ordering within README.md
- API reference formatting (tables vs. code blocks for function signatures)
- How much of the REAM format to explain in README vs. linking to spec
- Wheel validation approach (script vs. documented steps)
- Whether to include a "Contributing" section or keep it minimal
- Developer guide depth (just package layout + running tests, or more)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Package source (for accurate API reference)
- `ream_xlsx/__init__.py` -- Public API: `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream` signatures and docstrings
- `ream_xlsx/_options.py` -- `ReamOptions` dataclass fields and defaults
- `ream_xlsx/_exceptions.py` -- Exception hierarchy
- `ream_xlsx/_cli.py` -- CLI command with all flags and help text

### Existing content to move
- `README.md` -- Current benchmark README, to be moved to BENCHMARK.md

### Requirements
- `.planning/REQUIREMENTS.md` -- DOC-01 through DOC-05

### Build config
- `pyproject.toml` -- Package metadata, version, dependencies, entry points

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ream_xlsx/__init__.py` docstrings: All 3 public functions have full docstrings with Args, Returns, Raises
- `ream_xlsx/_cli.py` help text: Click decorators have help strings for all flags
- `ream_xlsx/_options.py`: Dataclass fields have type annotations and defaults
- `README.md`: Current benchmark content (to move to BENCHMARK.md)

### Established Patterns
- MIT license (Copyright 2026 Siqi Chen, Runway Financial)
- Package version in `pyproject.toml` (static, 0.1.0)
- Dev dependencies in `[project.optional-dependencies] dev` group

### Integration Points
- `README.md` at repo root — the primary documentation target
- `BENCHMARK.md` at repo root — new file for moved content
- `pyproject.toml` — source of version, dependencies, entry points for documentation

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-documentation*
*Context gathered: 2026-03-31*
