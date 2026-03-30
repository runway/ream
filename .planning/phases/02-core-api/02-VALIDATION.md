---
phase: 2
slug: core-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0.0 |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v && ruff check . && mypy ream_xlsx`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | API-01 | unit | `pytest tests/test_api.py::test_xlsx_to_ream_returns_ream_string -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | API-02 | unit | `pytest tests/test_api.py::test_bytes_to_ream_returns_ream_string -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | API-03 | unit | `pytest tests/test_api.py::test_file_to_ream_returns_ream_string -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | API-04 | unit | `pytest tests/test_api.py::test_xlsx_to_ream_accepts_path_object -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | API-05 | unit | `pytest tests/test_options.py::test_ream_options_defaults -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | API-06 | unit | `pytest tests/test_api.py::test_output_is_deterministic -x` | ❌ W0 | ⬜ pending |
| 02-01-07 | 01 | 1 | ERR-01 | unit | `pytest tests/test_errors.py::test_ream_error_hierarchy -x` | ❌ W0 | ⬜ pending |
| 02-01-08 | 01 | 1 | ERR-02 | unit | `pytest tests/test_errors.py::test_missing_file_raises_invalid_workbook_error -x` | ❌ W0 | ⬜ pending |
| 02-01-09 | 01 | 1 | ERR-03 | unit | `pytest tests/test_errors.py::test_error_subclass_hierarchy -x` | ❌ W0 | ⬜ pending |
| 02-01-10 | 01 | 1 | TST-02 | unit | `pytest tests/test_api.py -k "path" -x` | ❌ W0 | ⬜ pending |
| 02-01-11 | 01 | 1 | TST-03 | unit | `pytest tests/test_api.py::test_bytes_to_ream_matches_path -x` | ❌ W0 | ⬜ pending |
| 02-01-12 | 01 | 1 | TST-04 | unit | `pytest tests/test_api.py::test_file_to_ream_matches_path -x` | ❌ W0 | ⬜ pending |
| 02-01-13 | 01 | 1 | TST-05 | unit | `pytest tests/test_options.py -x` | ❌ W0 | ⬜ pending |
| 02-01-14 | 01 | 1 | TST-06 | unit | `pytest tests/test_api.py::test_output_is_deterministic -x` | ❌ W0 | ⬜ pending |
| 02-01-15 | 01 | 1 | TST-09 | unit | `pytest tests/test_errors.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_api.py` — covers API-01, API-02, API-03, API-04, TST-02, TST-03, TST-04, TST-06
- [ ] `tests/test_options.py` — covers API-05, TST-05
- [ ] `tests/test_errors.py` — covers ERR-01, ERR-02, ERR-03, TST-09
- [ ] `ream_xlsx/_options.py` — ReamOptions frozen dataclass
- [ ] `ream_xlsx/_io.py` — I/O adapters + error mapping
- [ ] `ream_xlsx/_converter.py` — ported conversion logic

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| *None* | — | — | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
