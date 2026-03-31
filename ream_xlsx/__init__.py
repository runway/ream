"""ream_xlsx -- Convert XLSX workbooks to REAM text format."""

from __future__ import annotations

from pathlib import Path
from typing import IO

from ream_xlsx._options import ReamOptions

__all__ = [
    "xlsx_to_ream",
    "bytes_to_ream",
    "file_to_ream",
    "ReamOptions",
    "ReamError",
    "InvalidWorkbookError",
    "ConversionError",
]


class ReamError(Exception):
    """Base exception for ream_xlsx errors."""


class InvalidWorkbookError(ReamError):
    """Raised when the input workbook is invalid or cannot be parsed."""


class ConversionError(ReamError):
    """Raised when the conversion from XLSX to REAM fails."""


def xlsx_to_ream(path: str | Path, options: ReamOptions | None = None) -> str:
    """Convert an XLSX file at the given path to REAM text.

    Args:
        path: Path to the XLSX workbook.
        options: Optional conversion options.

    Returns:
        REAM-formatted string.
    """
    raise NotImplementedError


def bytes_to_ream(data: bytes, options: ReamOptions | None = None) -> str:
    """Convert raw XLSX bytes to REAM text.

    Args:
        data: Raw bytes of an XLSX workbook.
        options: Optional conversion options.

    Returns:
        REAM-formatted string.
    """
    raise NotImplementedError


def file_to_ream(stream: IO[bytes], options: ReamOptions | None = None) -> str:
    """Convert an XLSX file-like object to REAM text.

    Args:
        stream: Binary file-like object containing an XLSX workbook.
        options: Optional conversion options.

    Returns:
        REAM-formatted string.
    """
    raise NotImplementedError
