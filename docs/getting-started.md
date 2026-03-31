# ream-xlsx

Convert XLSX workbooks to REAM text format.

REAM is a sparse, UTF-8, line-oriented text format designed for LLM spreadsheet comprehension. It encodes workbook structure — row numbers, column addresses, formulas, named ranges, and multi-sheet boundaries — into a token-efficient representation. See the [format specification](../spec/ream-rfc-draft-v12.md) for details.

This package is a pip-installable converter that exposes a small, stable Python API and a CLI command for converting XLSX workbooks to REAM text.

---

## Installation

```bash
pip install ream-xlsx
```

Requires Python >= 3.10. The only runtime dependency is `openpyxl`.

---

## Quickstart

```python
from ream_xlsx import xlsx_to_ream, ReamOptions

# Basic conversion
text = xlsx_to_ream("workbook.xlsx")

# With options
text = xlsx_to_ream("workbook.xlsx", ReamOptions(
    max_rows_per_sheet=100,
    collapse_rows=True,
    force_col_selectors=True,
))

print(text)
```

---

## API Reference

### Functions

#### `xlsx_to_ream(path, options=None) -> str`

Convert an XLSX file at the given path to REAM text.

```python
from ream_xlsx import xlsx_to_ream

text = xlsx_to_ream("workbook.xlsx")
```

**Arguments:**
- `path` (`str | Path`) — path to the XLSX workbook file
- `options` (`ReamOptions | None`) — optional conversion options; defaults to `ReamOptions()` if omitted

**Returns:** REAM-formatted string.

**Raises:** `InvalidWorkbookError` if the file cannot be read or is not a valid XLSX file; `ConversionError` if conversion fails internally.

---

#### `bytes_to_ream(data, options=None) -> str`

Convert raw XLSX bytes to REAM text. Useful when the workbook is already in memory (e.g., downloaded from an API or read from a database).

```python
from ream_xlsx import bytes_to_ream

with open("workbook.xlsx", "rb") as f:
    data = f.read()
text = bytes_to_ream(data)
```

**Arguments:**
- `data` (`bytes`) — raw bytes of an XLSX workbook
- `options` (`ReamOptions | None`) — optional conversion options

**Returns:** REAM-formatted string.

**Raises:** `InvalidWorkbookError` if the bytes are not a valid XLSX workbook; `ConversionError` if conversion fails internally.

---

#### `file_to_ream(stream, options=None) -> str`

Convert an XLSX file-like object to REAM text. Useful for streaming contexts or when reading from `BytesIO`.

```python
from io import BytesIO
from ream_xlsx import file_to_ream

with open("workbook.xlsx", "rb") as f:
    text = file_to_ream(f)
```

**Arguments:**
- `stream` (`IO[bytes]`) — binary file-like object containing an XLSX workbook
- `options` (`ReamOptions | None`) — optional conversion options

**Returns:** REAM-formatted string.

**Raises:** `InvalidWorkbookError` if the stream is not a valid XLSX workbook; `ConversionError` if conversion fails internally.

---

### ReamOptions

A frozen dataclass controlling conversion behaviour. Pass it as the `options` argument to any conversion function.

```python
from ream_xlsx import ReamOptions

opts = ReamOptions(
    max_rows_per_sheet=200,
    collapse_rows=True,
    force_col_selectors=False,
)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows_per_sheet` | `int` | `500` | Maximum rows to convert per sheet. Rows beyond this limit are omitted. |
| `force_col_selectors` | `bool` | `False` | Force A1-style column selectors on every cell (e.g., `A=Revenue`). By default, selectors are omitted when the column position is unambiguous. |
| `collapse_rows` | `bool` | `False` | Merge identical adjacent rows into row-span records (e.g., `7:9 | B:M=8500 |`). Produces `#!REAM 11` output. |

`ReamOptions` is frozen (immutable). Create a new instance to change settings.

---

### Exceptions

All exceptions inherit from `ReamError`.

```
ReamError
├── InvalidWorkbookError
└── ConversionError
```

| Exception | When raised |
|-----------|-------------|
| `ReamError` | Base class; catch this to handle any package error |
| `InvalidWorkbookError` | Input is not a valid XLSX file: missing file, corrupted data, wrong format |
| `ConversionError` | Conversion logic failed internally |

---

## CLI Usage

The `ream-xlsx` command is available after installation. You can also invoke it as a Python module.

```bash
# Convert to stdout
ream-xlsx input.xlsx

# Write output to a file
ream-xlsx input.xlsx -o output.txt

# Convert with all options
ream-xlsx workbook.xlsx --max-rows 100 --collapse-rows --force-col-selectors -o output.txt

# Via python module
python -m ream_xlsx workbook.xlsx
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-o FILE`, `--output FILE` | stdout | Write output to FILE instead of stdout |
| `--max-rows N` | `500` | Maximum rows per sheet |
| `--collapse-rows` | off | Collapse identical adjacent rows |
| `--force-col-selectors` | off | Force column selectors in output |
| `--version` | — | Show version and exit |

---

## Error Handling

All package errors inherit from `ReamError`. Catch the specific subclass for targeted handling or catch `ReamError` as a catch-all.

```python
from ream_xlsx import xlsx_to_ream, ReamError, InvalidWorkbookError

try:
    text = xlsx_to_ream("workbook.xlsx")
except InvalidWorkbookError as e:
    print(f"Bad input: {e}")
except ReamError as e:
    print(f"Conversion error: {e}")
```

The CLI exits with code `1` and prints the error message to stderr on any `ReamError`.

---

## Developer Guide

### Package Layout

```
ream_xlsx/
  __init__.py       Public API (xlsx_to_ream, bytes_to_ream, file_to_ream)
  _options.py       ReamOptions dataclass
  _exceptions.py    Exception hierarchy
  _io.py            I/O adapters (load workbooks from path/bytes/stream)
  _converter.py     Core conversion logic
  _cli.py           CLI entry point (Click command)
  __main__.py       python -m ream_xlsx support
  py.typed          PEP 561 type marker
```

Modules prefixed with `_` are internal and not part of the public API. Import only from `ream_xlsx` (i.e., what `__all__` in `__init__.py` exports): `xlsx_to_ream`, `bytes_to_ream`, `file_to_ream`, `ReamOptions`, `ReamError`, `InvalidWorkbookError`, `ConversionError`.

### Running Tests

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy ream_xlsx
```

The test suite lives in `tests/`. All tests use pytest. The dev extras include `ruff` (linting/formatting) and `mypy` (strict type checking).

---

## License

MIT
