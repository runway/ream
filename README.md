# Ream

**A sparse text format for LLM spreadsheet comprehension.**

Ream is a UTF-8, line-oriented format that serializes spreadsheet workbooks into text optimized for large language model consumption. It combines absolute row numbering, A1-style column addressing, R1C1 formula notation, defined names, structured table references, display annotations, and row-span compaction for repeated data.

## Quick Example

```
#!REAM 11
#!NAME tax_rate 'Assumptions'!B2
#!SHEET Assumptions
2 | Tax Rate | 0.25 |

#!SHEET "P&L"
#!HEADERS 1:1
#!NAME revenue_inputs B2:M2

1 | B=Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
2 | Revenue | 1000 | 1050 | 1100 | 1150 | 1200 | G:M==RC[-1]*1.08 |
3 | COGS | B:M==R[-1]C*0.6 |
4 | Gross Profit | B:M==R[-2]C-R[-1]C |
6 | Headcount | B:C=50 | D:M=52 |
7:9 | B:M=8500 |
10 | Total OpEx | B:M==R[-2]C+R[-1]C |
12 | Tax | B:M==R4C*tax_rate |
13 | Net Income | B:M==R4C-R10C-R[-1]C |

#!FMT 2:4 usd0
#!TAG B13:M13 output
```

Key features: sparse row numbering (rows 5, 8, 11 omitted), range compaction (`B:M=8500`), row-span records (`7:9 | ...`), cross-sheet named references (`tax_rate`), addressed formulas (`==`), and metadata directives.

## Design Principles

- **A1-style column letters** (`B=`, `M=`) — leverages model pre-training on Excel documentation
- **Sparse encoding** — omits blank cells, uses 26–53% fewer tokens than JSON on enterprise workbooks
- **Row-span compaction** — identical consecutive rows merge into `7:9 | B:M=8500 |`
- **Structural directives** — `#!SHEET`, `#!HEADERS`, `#!TABLE`, `#!NAME` preserve multi-sheet boundaries
- **Display annotations** — `0.25@"25%"` carries both the value and its human-readable rendering
- **Formula support** — R1C1 notation with defined names and structured table references

## ream-xlsx Python Package

The `ream-xlsx` package is a pip-installable converter for XLSX-to-REAM conversion with a Python API and CLI.

```bash
pip install ream-xlsx
```

See [docs/getting-started.md](docs/getting-started.md) for installation, API reference, CLI usage, and developer guide.

## Benchmark Results

We benchmarked Ream against 10 alternative serialization formats across four evaluation corpora and three OpenAI models, executing 19,000+ LLM calls.

### GPT-5.4 Cross-Corpus Accuracy

| Format | FRTR (enterprise) | MiMoTable | NL2Formula | Average |
|--------|-------------------|-----------|------------|---------|
| **Ream** | **92.0%** | 66.5% | 78.5% | **79.0%** |
| JSON | 89.5% | 67.5% | 79.0% | 78.7% |
| Cell-Address MD | 92.0% | 67.5% | 75.5% | 78.3% |
| XML | 89.4% | 66.5% | 78.5% | 78.1% |
| CSV | 84.0% | 66.0% | 76.5% | 75.5% |

Ream achieves the **highest cross-corpus average** while using **26–53% fewer tokens** than JSON and XML. It is the **only top-tier format with zero context-length failures** across all models.

## Converter Usage

```python
from src.converters import xlsx_to_ream

# Default: sparse column prefixes, no row collapse (#!REAM 9)
text = xlsx_to_ream("workbook.xlsx")

# Force column selectors on every cell (A=Revenue | B=1000 |)
text = xlsx_to_ream("workbook.xlsx", force_col_selectors=True)

# Enable row-span compaction (#!REAM 11)
text = xlsx_to_ream("workbook.xlsx", collapse_rows=True)

# Both: full addressing + row collapse
text = xlsx_to_ream("workbook.xlsx", force_col_selectors=True, collapse_rows=True)
```

## Repository Structure

```
spec/               Ream format specifications (drafts 9 and 12)
src/                Evaluation harness and format converters
  converters.py     12 XLSX-to-text converters (Ream, CSV, JSON, etc.)
  run_eval.py       Parallel evaluation runner with caching
  scoring.py        Answer scoring (numeric, string, boolean)
  generate_questions.py   QA generation from FRTR-Bench
  extract_mimotable.py    MiMoTable question extraction
  extract_nl2formula.py   NL2Formula question extraction
data/               Generated question corpora (JSON)
results/            Full evaluation results (JSON)
docs/               Package documentation
paper/              LaTeX source and PDF
```

## Running the Benchmark

```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
echo "OPENAI_API_KEY=sk-..." > .env

# Download corpora (not included due to size)
git clone --depth 1 https://github.com/AnmolGulati6/FRTR-bench.git corpus/frtr
git clone --depth 1 https://github.com/xxsdds/MiMoTable.git corpus/mimotable
git clone --depth 1 https://github.com/timetub/NL2Formula.git corpus/nl2formula

# Generate questions
python src/generate_questions.py corpus/frtr corpus/spreadsheetbench/data/sample_data_200 1000

# Run evaluation
cd src && python run_eval.py \
  --questions ../data/questions_sample_200.json \
  --models gpt-4o-mini gpt-5.4 \
  --formats ream ream_v12 csv json html xml markdown \
  --max-rows 1000
```

## Specification

The latest Ream specification is [`spec/ream-rfc-draft-v12.md`](spec/ream-rfc-draft-v12.md) (wire version `#!REAM 11`).

The previous draft is at [`spec/ream-rfc-draft-v9.md`](spec/ream-rfc-draft-v9.md) (wire version `#!REAM 9`).

## Paper

The benchmark paper is available at [`paper/ream-benchmark.pdf`](paper/ream-benchmark.pdf).

## License

MIT
