# ream-xlsx

`ream-xlsx` converts Excel `.xlsx` workbooks into [REAM](https://github.com/runway/ream), a sparse text format for LLM-friendly spreadsheet comprehension.

REAM preserves spreadsheet structure such as:

- sheet boundaries
- sparse row numbering
- A1-style column addressing
- formulas in R1C1 notation
- named ranges
- optional row-span compaction

## Installation

```bash
pip install ream-xlsx
```

Requires Python 3.10 or newer.

## Python API

```python
from ream_xlsx import ReamOptions, xlsx_to_ream

text = xlsx_to_ream(
    "workbook.xlsx",
    ReamOptions(
        max_rows_per_sheet=100,
        collapse_rows=True,
        force_col_selectors=True,
    ),
)

print(text)
```

The public API includes:

- `xlsx_to_ream(path, options=None)`
- `bytes_to_ream(data, options=None)`
- `file_to_ream(stream, options=None)`
- `ReamOptions`

## CLI

```bash
ream-xlsx workbook.xlsx
ream-xlsx workbook.xlsx --collapse-rows --force-col-selectors -o output.ream
python -m ream_xlsx workbook.xlsx
```

## More Information

- Documentation: <https://github.com/runway/ream/tree/main/docs>
- Format spec: <https://github.com/runway/ream/blob/main/spec/ream-rfc-draft-v12.md>
- Source: <https://github.com/runway/ream>
