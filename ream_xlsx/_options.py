"""ReamOptions frozen dataclass for controlling XLSX-to-REAM conversion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReamOptions:
    """Options controlling XLSX-to-REAM conversion behaviour."""

    max_rows_per_sheet: int = 500
    force_col_selectors: bool = False
    collapse_rows: bool = False
