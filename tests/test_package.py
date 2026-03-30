"""TST-01: Verify package importability and __all__ exports."""

from __future__ import annotations

import importlib
from pathlib import Path

import ream_xlsx

_EXPECTED_EXPORTS = {
    "xlsx_to_ream",
    "bytes_to_ream",
    "file_to_ream",
    "ReamOptions",
    "ReamError",
    "InvalidWorkbookError",
    "ConversionError",
}


def test_package_importable() -> None:
    """Package imports without error."""
    mod = importlib.import_module("ream_xlsx")
    assert mod is not None


def test_all_defined() -> None:
    """__all__ is defined on the package."""
    assert hasattr(ream_xlsx, "__all__")


def test_all_exports_present() -> None:
    """All expected names are in __all__ and no extras."""
    assert set(ream_xlsx.__all__) == _EXPECTED_EXPORTS


def test_all_names_importable() -> None:
    """Every name in __all__ can be accessed on the module."""
    for name in ream_xlsx.__all__:
        assert hasattr(ream_xlsx, name), f"{name} not found in ream_xlsx"


def test_py_typed_marker() -> None:
    """py.typed marker file exists in the package directory."""
    package_dir = Path(ream_xlsx.__file__).parent
    assert (package_dir / "py.typed").exists()
