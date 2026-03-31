"""Exception hierarchy for ream_xlsx.

Defined here (not in __init__.py) to avoid circular imports:
_io.py needs to raise InvalidWorkbookError, and __init__.py imports from _io.py.
__init__.py re-exports all exception classes from here.
"""

from __future__ import annotations


class ReamError(Exception):
    """Base exception for ream_xlsx errors."""


class InvalidWorkbookError(ReamError):
    """Raised when the input workbook is invalid or cannot be parsed."""


class ConversionError(ReamError):
    """Raised when the conversion from XLSX to REAM fails."""
