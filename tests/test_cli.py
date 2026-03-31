"""TDD tests for the ream-xlsx CLI: ream-xlsx and python -m ream_xlsx."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import openpyxl
import pytest
from click.testing import CliRunner

from ream_xlsx._cli import main

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_xlsx(tmp_path: Path) -> Path:
    """Create a simple XLSX workbook with 1 sheet, header + 3 data rows."""
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Sheet1"
    ws.append(["Name", "Value"])
    ws.append(["Alpha", 100])
    ws.append(["Beta", 200])
    ws.append(["Gamma", 300])
    p = tmp_path / "test.xlsx"
    wb.save(p)
    return p


@pytest.fixture()
def tmp_invalid_xlsx(tmp_path: Path) -> Path:
    """Create an invalid XLSX file (just text bytes)."""
    p = tmp_path / "bad.xlsx"
    p.write_bytes(b"this is not xlsx")
    return p


# ---------------------------------------------------------------------------
# TST-07: Success cases
# ---------------------------------------------------------------------------


def test_stdout_success(tmp_xlsx: Path) -> None:
    """invoke with valid XLSX path: exit_code == 0, stdout starts with '#!REAM'."""
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_xlsx)], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout.startswith("#!REAM")


def test_output_file(tmp_xlsx: Path, tmp_path: Path) -> None:
    """invoke with valid XLSX + '-o' + tmp path: exit_code==0, stdout empty, file has REAM content."""
    runner = CliRunner()
    out_path = tmp_path / "out.txt"
    result = runner.invoke(main, [str(tmp_xlsx), "-o", str(out_path)], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout == ""
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("#!REAM")


def test_stdout_trailing_newline(tmp_xlsx: Path) -> None:
    """stdout ends with exactly one trailing newline (D-06)."""
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_xlsx)], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout.endswith("\n")
    assert not result.stdout.endswith("\n\n")


def test_max_rows_flag(tmp_xlsx: Path) -> None:
    """'--max-rows 2' limits data rows in output (fixture has 3 data rows)."""
    runner = CliRunner()
    result_default = runner.invoke(main, [str(tmp_xlsx)], catch_exceptions=False)
    result_limited = runner.invoke(main, ["--max-rows", "2", str(tmp_xlsx)], catch_exceptions=False)
    assert result_limited.exit_code == 0
    # The limited output should have fewer lines than the default
    default_lines = [ln for ln in result_default.stdout.splitlines() if ln and not ln.startswith("#")]
    limited_lines = [ln for ln in result_limited.stdout.splitlines() if ln and not ln.startswith("#")]
    assert len(limited_lines) < len(default_lines)


def test_collapse_rows_flag(tmp_xlsx: Path) -> None:
    """'--collapse-rows' causes output to start with '#!REAM 11'."""
    runner = CliRunner()
    result = runner.invoke(main, ["--collapse-rows", str(tmp_xlsx)], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.stdout.startswith("#!REAM 11")


def test_force_col_selectors_flag(tmp_xlsx: Path) -> None:
    """'--force-col-selectors' causes data row lines to contain 'A=' pattern."""
    runner = CliRunner()
    result = runner.invoke(main, ["--force-col-selectors", str(tmp_xlsx)], catch_exceptions=False)
    assert result.exit_code == 0
    data_lines = [ln for ln in result.stdout.splitlines() if ln and not ln.startswith("#")]
    assert len(data_lines) > 0
    for line in data_lines:
        assert "A=" in line


def test_version_flag() -> None:
    """'--version' exits 0 and stdout contains '0.1.0'."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_help_flag() -> None:
    """'--help' exits 0 and stdout contains 'Convert an XLSX'."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Convert an XLSX" in result.stdout


def test_module_invocation(tmp_xlsx: Path) -> None:
    """'python -m ream_xlsx input.xlsx' exits 0 and stdout starts with '#!REAM'."""
    proc = subprocess.run(
        [sys.executable, "-m", "ream_xlsx", str(tmp_xlsx)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.startswith("#!REAM")


# ---------------------------------------------------------------------------
# TST-08: Error cases
# ---------------------------------------------------------------------------


def test_missing_file_error() -> None:
    """invoke with nonexistent.xlsx: exit_code == 1, stderr starts with 'error:'."""
    runner = CliRunner()
    result = runner.invoke(main, ["nonexistent.xlsx"])
    assert result.exit_code == 1
    assert result.stderr.startswith("error:")


def test_missing_file_stderr_format() -> None:
    """invoke with nonexistent.xlsx: stderr contains 'error:' and 'nonexistent.xlsx'."""
    runner = CliRunner()
    result = runner.invoke(main, ["nonexistent.xlsx"])
    assert result.exit_code == 1
    assert "error:" in result.stderr
    assert "nonexistent.xlsx" in result.stderr


def test_invalid_xlsx_error(tmp_invalid_xlsx: Path) -> None:
    """invoke with plain-text file renamed .xlsx: exit_code == 1, stderr starts with 'error:'."""
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_invalid_xlsx)])
    assert result.exit_code == 1
    assert result.stderr.startswith("error:")


def test_no_stdout_on_error() -> None:
    """invoke with nonexistent.xlsx: stdout is empty."""
    runner = CliRunner()
    result = runner.invoke(main, ["nonexistent.xlsx"])
    assert result.stdout == ""
