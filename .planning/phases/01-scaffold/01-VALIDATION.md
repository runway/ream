---
phase: 1
slug: scaffold
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0.0 |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` (Wave 0 creates this) |
| **Quick run command** | `pytest tests/test_package.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_package.py -x`
- **After every plan wave:** Run `pytest && ruff check . && ruff format --check . && mypy ream_xlsx`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | PKG-01 | smoke | `pip install -e . && python -c "import ream_xlsx"` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | PKG-02 | unit | `pytest tests/test_package.py::test_package_importable -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | PKG-02 | unit | `pytest tests/test_package.py::test_all_names_importable -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | PKG-03 | unit | `pytest tests/test_package.py::test_py_typed_marker -x` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | PKG-04 | manual | Inspect `pyproject.toml` `[project.dependencies]` | N/A | ⬜ pending |
| 01-01-06 | 01 | 1 | PKG-05 | manual | Inspect `pyproject.toml` `requires-python` | N/A | ⬜ pending |
| 01-01-07 | 01 | 1 | TST-01 | unit | `pytest tests/test_package.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — empty file to make tests a package
- [ ] `tests/test_package.py` — covers PKG-01, PKG-02, PKG-03, TST-01
- [ ] `ream_xlsx/__init__.py` — public API stubs with typed signatures
- [ ] `ream_xlsx/py.typed` — empty PEP 561 marker
- [ ] `pyproject.toml` — all config (hatchling + ruff + mypy + pytest)
- [ ] Framework install: `pip install -e ".[dev]"` — installs pytest, ruff, mypy

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Only openpyxl + click in runtime deps | PKG-04 | Static config check | Inspect `[project.dependencies]` in `pyproject.toml` |
| Python >= 3.10 declared | PKG-05 | Static config check | Inspect `requires-python` in `pyproject.toml` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
