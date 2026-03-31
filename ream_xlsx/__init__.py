"""ream_xlsx -- Convert XLSX workbooks to REAM text format."""

from __future__ import annotations

from pathlib import Path
from typing import IO

from ream_xlsx._converter import _xlsx_to_ream_impl
from ream_xlsx._exceptions import ConversionError, InvalidWorkbookError, ReamError
from ream_xlsx._io import _load_from_bytes, _load_from_path, _load_from_stream
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


def xlsx_to_ream(path: str | Path, options: ReamOptions | None = None) -> str:
    """Convert an XLSX file at the given path to REAM text.

    Args:
        path: Path to the XLSX workbook.
        options: Optional conversion options.

    Returns:
        REAM-formatted string.

    Raises:
        InvalidWorkbookError: If the file cannot be read or is not a valid XLSX file.
        ConversionError: If the conversion logic fails internally.
    """
    wb = _load_from_path(path)
    opts = options if options is not None else ReamOptions()
    try:
        return _xlsx_to_ream_impl(wb, opts)
    except ReamError:
        raise
    except Exception as exc:
        raise ConversionError(f"Conversion failed: {exc}") from exc


def bytes_to_ream(data: bytes, options: ReamOptions | None = None) -> str:
    """Convert raw XLSX bytes to REAM text.

    Args:
        data: Raw bytes of an XLSX workbook.
        options: Optional conversion options.

    Returns:
        REAM-formatted string.

    Raises:
        InvalidWorkbookError: If the bytes do not represent a valid XLSX file.
        ConversionError: If the conversion logic fails internally.
    """
    wb = _load_from_bytes(data)
    opts = options if options is not None else ReamOptions()
    try:
        return _xlsx_to_ream_impl(wb, opts)
    except ReamError:
        raise
    except Exception as exc:
        raise ConversionError(f"Conversion failed: {exc}") from exc


def file_to_ream(stream: IO[bytes], options: ReamOptions | None = None) -> str:
    """Convert an XLSX file-like object to REAM text.

    Args:
        stream: Binary file-like object containing an XLSX workbook.
        options: Optional conversion options.

    Returns:
        REAM-formatted string.

    Raises:
        InvalidWorkbookError: If the stream does not represent a valid XLSX file.
        ConversionError: If the conversion logic fails internally.
    """
    wb = _load_from_stream(stream)
    opts = options if options is not None else ReamOptions()
    try:
        return _xlsx_to_ream_impl(wb, opts)
    except ReamError:
        raise
    except Exception as exc:
        raise ConversionError(f"Conversion failed: {exc}") from exc
