"""I/O adapter layer for loading XLSX workbooks from various sources."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import IO
from zipfile import BadZipFile

import openpyxl
from openpyxl import Workbook
from openpyxl.utils.exceptions import InvalidFileException

from ream_xlsx._exceptions import InvalidWorkbookError


def _load_from_path(path: str | Path) -> Workbook:
    """Load an XLSX workbook from a file path.

    Args:
        path: Path to the XLSX file (str or Path).

    Returns:
        An openpyxl Workbook opened with data_only=True.

    Raises:
        InvalidWorkbookError: If the file is missing, is a directory,
            is not a valid XLSX file, or cannot be read.
    """
    path = Path(path)
    try:
        return openpyxl.load_workbook(path, data_only=True)
    except FileNotFoundError:
        raise InvalidWorkbookError(f"File not found: {path}") from None
    except IsADirectoryError:
        raise InvalidWorkbookError(f"Path is a directory, not a file: {path}") from None
    except InvalidFileException as exc:
        raise InvalidWorkbookError(f"Not a valid XLSX file: {path} ({exc})") from exc
    except BadZipFile as exc:
        raise InvalidWorkbookError(f"Corrupted or invalid XLSX file: {path} ({exc})") from exc
    except Exception as exc:
        raise InvalidWorkbookError(f"Failed to load workbook from path: {path} ({exc})") from exc


def _load_from_bytes(data: bytes) -> Workbook:
    """Load an XLSX workbook from raw bytes.

    Args:
        data: Raw bytes of an XLSX workbook.

    Returns:
        An openpyxl Workbook opened with data_only=True.

    Raises:
        InvalidWorkbookError: If the bytes do not represent a valid XLSX file.
    """
    return _load_from_stream(BytesIO(data))


def _load_from_stream(stream: IO[bytes]) -> Workbook:
    """Load an XLSX workbook from a binary file-like object.

    Args:
        stream: Binary file-like object containing an XLSX workbook.

    Returns:
        An openpyxl Workbook opened with data_only=True.

    Raises:
        InvalidWorkbookError: If the stream does not represent a valid XLSX file.
    """
    try:
        return openpyxl.load_workbook(stream, data_only=True)
    except InvalidFileException as exc:
        raise InvalidWorkbookError(f"Not a valid XLSX stream: ({exc})") from exc
    except BadZipFile as exc:
        raise InvalidWorkbookError(f"Corrupted or invalid XLSX stream: ({exc})") from exc
    except Exception as exc:
        raise InvalidWorkbookError(f"Failed to load workbook from stream: ({exc})") from exc
