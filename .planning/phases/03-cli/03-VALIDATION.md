---
phase: 03
slug: cli
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `.venv/bin/pytest tests/test_cli.py -x -v` |
| **Full suite command** | `.venv/bin/pytest tests/ -v && .venv/bin/ruff check . && .venv/bin/mypy ream_xlsx` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_cli.py -x -v`
- **After every plan wave:** Run `.venv/bin/pytest tests/ -v && .venv/bin/ruff check . && .venv/bin/mypy ream_xlsx`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | CLI-01, CLI-03, CLI-04, CLI-05, CLI-06 | unit+integration | `.venv/bin/pytest tests/test_cli.py -x -v` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | CLI-02 | unit | `.venv/bin/pytest tests/test_cli.py -k __main__ -v` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | TST-07, TST-08 | integration | `.venv/bin/pytest tests/test_cli.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_cli.py` — stubs for CLI-01 through CLI-06, TST-07, TST-08
- Existing test infrastructure (pytest, conftest) already in place from Phase 1-2

*Existing infrastructure covers framework and fixture needs.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
