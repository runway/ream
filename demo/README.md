# Demo Files

Sample XLSX workbooks for testing and exploring `ream-xlsx`.

## Files

| File | Description | Features demonstrated |
|------|-------------|---------------------|
| `simple_table.xlsx` | Employee table with names, departments, salaries, dates | Basic conversion, date handling |
| `multi_sheet.xlsx` | Revenue, Expenses, and Summary sheets | `#!SHEET` directives, multi-sheet workbooks |
| `sparse_data.xlsx` | Sensor readings with gaps in rows and columns | Sparse row numbering, column selectors (`D=`, `F=`) |
| `repeated_rows.xlsx` | Pricing table with many identical rows | `--collapse-rows` row-span compaction (`2:6 \| ... \|`) |
| `financial_model.xlsx` | Mini P&L with an Assumptions sheet | Real-world financial layout, blank row handling |
| `mixed_types.xlsx` | Various data types: strings, dates, numbers, booleans | Type handling, special character quoting |

## Usage

### Convert a single file

```bash
ream-xlsx demo/simple_table.xlsx
```

### Run all demos

Converts all demo XLSX files and saves the REAM output to `demo/results/*.md`.

```bash
python demo/run_demos.py
```

### Run a single file

```bash
python demo/run_demos.py demo/simple_table.xlsx
```

### Try different options

```bash
# Collapse repeated rows into spans
python demo/run_demos.py --collapse-rows

# Force column selectors on every cell
python demo/run_demos.py --force-col-selectors

# Limit rows per sheet
python demo/run_demos.py --max-rows 3

# Single file with options
python demo/run_demos.py --collapse-rows demo/repeated_rows.xlsx
```

### Private files

Drop your own XLSX files into `demo/private/` to test them without committing to git. They will be picked up automatically when running `python demo/run_demos.py` and results will be saved to `demo/results/`.

## Regenerating demo files

The XLSX files are checked in so you don't need openpyxl to use them. To regenerate:

```bash
python demo/generate_demos.py
```
