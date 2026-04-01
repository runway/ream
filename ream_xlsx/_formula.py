"""A1-to-R1C1 formula conversion for REAM export."""

from __future__ import annotations

import re


def _col_to_num(col_str: str) -> int:
    """Convert column letters (A, B, ..., Z, AA, ...) to 1-based number."""
    result = 0
    for ch in col_str:
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result


# Tokeniser: matches double-quoted string literals (to skip) or A1-style
# cell references (to convert).  The alternation ensures strings are consumed
# before any embedded text is tested as a reference.
_TOKEN_RE = re.compile(
    r"""
    (?P<string>"(?:[^"]*"")*[^"]*")                          # string literal
    | (?P<ref>
        (?:(?:'(?:[^']*'')*[^']*'|[A-Za-z_]\w*)\!)?          # optional sheet! prefix
        (?P<col_abs>\$?)(?P<col>[A-Z]{1,3})
        (?P<row_abs>\$?)(?P<row>[1-9]\d{0,6})
        (?![(\w])                                              # not fn call or word
      )
    """,
    re.VERBOSE,
)


def _a1_formula_to_r1c1(formula: str, cell_row: int, cell_col: int) -> str:
    """Convert A1-style references in a formula body to R1C1 notation.

    Args:
        formula: Formula text *without* the leading ``=``.
        cell_row: 1-based row of the cell containing the formula.
        cell_col: 1-based column of the cell containing the formula.

    Returns:
        Formula with A1 references replaced by R1C1 references.
    """

    def _replace(m: re.Match[str]) -> str:
        # String literals are returned untouched.
        if m.group("string") is not None:
            return m.group(0)

        full = m.group(0)
        col_str = m.group("col")
        col_num = _col_to_num(col_str)
        if col_num > 16384:  # max Excel column XFD
            return full

        row_num = int(m.group("row"))
        if row_num > 1048576:  # max Excel row
            return full

        # Preserve any sheet prefix (e.g. ``Sheet1!`` or ``'My Sheet'!``).
        sheet_prefix = ""
        if "!" in full:
            sheet_prefix = full[: full.index("!") + 1]

        # Row part
        if m.group("row_abs") == "$":
            r_part = f"R{row_num}"
        else:
            offset = row_num - cell_row
            r_part = f"R[{offset}]" if offset != 0 else "R"

        # Column part
        if m.group("col_abs") == "$":
            c_part = f"C{col_num}"
        else:
            offset = col_num - cell_col
            c_part = f"C[{offset}]" if offset != 0 else "C"

        return sheet_prefix + r_part + c_part

    return _TOKEN_RE.sub(_replace, formula)
