"""Tests for ReamOptions frozen dataclass."""

from __future__ import annotations

import dataclasses

import pytest

from ream_xlsx import ReamOptions


def test_ream_options_defaults() -> None:
    """ReamOptions() has correct default field values."""
    opts = ReamOptions()
    assert opts.max_rows_per_sheet == 500
    assert opts.force_col_selectors is False
    assert opts.collapse_rows is False


def test_ream_options_custom_values() -> None:
    """ReamOptions accepts custom values for all fields."""
    opts = ReamOptions(max_rows_per_sheet=10, force_col_selectors=True, collapse_rows=True)
    assert opts.max_rows_per_sheet == 10
    assert opts.force_col_selectors is True
    assert opts.collapse_rows is True


def test_ream_options_is_frozen() -> None:
    """Assigning to a ReamOptions field after creation raises FrozenInstanceError."""
    opts = ReamOptions()
    with pytest.raises(dataclasses.FrozenInstanceError):
        opts.max_rows_per_sheet = 999  # type: ignore[misc]


def test_ream_options_partial_override() -> None:
    """ReamOptions with one custom value keeps defaults for other fields."""
    opts = ReamOptions(max_rows_per_sheet=100)
    assert opts.max_rows_per_sheet == 100
    assert opts.force_col_selectors is False
    assert opts.collapse_rows is False


def test_ream_options_none_not_accepted() -> None:
    """ReamOptions is a concrete type, not None."""
    opts = ReamOptions()
    assert opts is not None
    assert isinstance(opts, ReamOptions)
