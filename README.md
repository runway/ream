# Ream

**A sparse text format for LLM spreadsheet comprehension.**

Ream is a UTF-8, line-oriented format that serializes spreadsheet workbooks into text optimized for large language model consumption. It combines absolute row numbering, A1-style column addressing, R1C1 formula notation, and structural directives for sheets, named ranges, and tables.

## Quick Example

```
#!REAM 9
#!SHEET "P&L"
#!HEADERS 1:1

1 | B=Jan | Feb | Mar | Apr | May | Jun |
2 | Revenue | 1000 | 1050 | 1100 | 1150 | 1200 | G:M==RC[-1]*1.08 |
3 | COGS | B:M==R[-1]C*0.6 |
4 | Gross Profit | B:M==R[-2]C-R[-1]C |
6 | Headcount | B:C=50 | D:M=52 |
7 | Avg Salary | B:M=8500 |
8 | Payroll | B:M==R[-2]C*R[-1]C |
```

## Benchmark Results

We benchmarked Ream against 10 alternative serialization formats (CSV, Markdown, HTML, XML, JSON, Pandas, Markdown-KV, Cell-Address MD, Reverse-Index, Raw OOXML) across four evaluation corpora and three OpenAI models, executing 19,000+ LLM calls.

### GPT-5.4 Cross-Corpus Accuracy

| Format | FRTR (enterprise) | MiMoTable | NL2Formula | Average |
|--------|-------------------|-----------|------------|---------|
| **Ream** | **92.0%** | 66.5% | 78.5% | **79.0%** |
| JSON | 89.5% | 67.5% | 79.0% | 78.7% |
| Cell-Address MD | 92.0% | 67.5% | 75.5% | 78.3% |
| XML | 89.4% | 66.5% | 78.5% | 78.1% |
| CSV | 84.0% | 66.0% | 76.5% | 75.5% |

Ream achieves the **highest cross-corpus average** while using **26-53% fewer tokens** than JSON and XML. It is the **only top-tier format with zero context-length failures** across all models.

## Repository Structure

```
spec/               Ream format specification (draft 9)
src/                Evaluation harness and format converters
  converters.py     11 XLSX-to-text converters (Ream, CSV, JSON, etc.)
  run_eval.py       Parallel evaluation runner with caching
  scoring.py        Answer scoring (numeric, string, boolean)
  generate_questions.py   QA generation from FRTR-Bench
  extract_mimotable.py    MiMoTable question extraction
  extract_nl2formula.py   NL2Formula question extraction
data/               Generated question corpora (JSON)
results/            Full evaluation results (JSON)
paper/              LaTeX source and PDF
analysis/           Format improvement analysis
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
  --formats ream csv json html xml markdown \
  --max-rows 1000
```

## Specification

The full Ream format specification is in [`spec/ream-rfc-draft-v9.md`](spec/ream-rfc-draft-v9.md).

## Paper

The benchmark paper is available at [`paper/ream-benchmark.pdf`](paper/ream-benchmark.pdf).

## License

MIT
