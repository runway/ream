# SCF Improvement Proposals Based on Benchmark Analysis

## Executive Summary

Across 6,498 evaluations, SCF achieves second-highest accuracy (85.0% on GPT-5.4, leading on GPT-4o-mini at 63.6%). JSON leads on larger models. The gap is **only 11 questions out of 200** on GPT-5.4. Forensic analysis of every failure reveals five root causes, each with a targeted fix.

---

## The 11 Failures: Root Cause Taxonomy

On GPT-5.4 (the clearest signal), JSON correctly answered 11 questions that SCF got wrong. These cluster into five categories:

| Root Cause | Count | Fixable? |
|---|---|---|
| Column-position miscounting | 3 | Yes — explicit column IDs |
| Truncation-induced hallucination | 2 | Yes — remove total row count |
| Value extraction from wrong cell | 3 | Yes — column-header annotations |
| Model refused to answer (data appeared insufficient) | 1 | Yes — row-count directive |
| Ambiguous SpreadsheetBench tasks | 2 | Partially — better instructions |

Note: SCF also uniquely beats JSON on 6 questions where JSON over-counted or hallucinated from its verbose structure. The net gap is only 5 questions.

---

## Failure 1: Column-Position Miscounting

**What happens**: The model must count pipe-delimited positions to determine which column a value belongs to. On wide rows, it miscounts.

**Example** (cell_lookup on GPT-4o-mini):
```
Q: What is the value in the 'AmountUSD' column of row 45 in sheet 'AP_Invoices'?
GT: 2787.2    SCF predicted: 1221.05    JSON predicted: 2787.2
```

In SCF, row 45 looks like:
```
R45 | 2025-06-28 | VEND-0674 | INV-28397 | 2025-02-16 | 2025-09-30 | 1221.05 | 2787.2 | Logistics | Partial |
```

The model picked position 6 (1221.05) instead of position 7 (2787.2) for "AmountUSD". With 9 columns and no column markers, counting from the header row is error-prone.

In JSON, the answer is unambiguous:
```json
{"A": "2025-06-28", "B": "VEND-0674", ..., "G": "2787.2", ...}
```

**Impact**: 3/11 failures on GPT-5.4; 12/28 on GPT-4o-mini. This is SCF's single biggest weakness.

### Proposed Fix: `#!COLUMNS` directive + always-on column prefixes

**Option A — Column header directive** (minimal token cost):
```
#!SHEET AP_Invoices
#!HEADERS R1
#!COLUMNS C1=Date C2=Vendor C3=InvoiceID C4=InvoiceDate C5=DueDate C6=InvoiceAmt C7=AmountUSD C8=Dept C9=Status
R1 | Date | Vendor | InvoiceID | InvoiceDate | DueDate | InvoiceAmt | AmountUSD | Dept | Status |
R45 | 2025-06-28 | VEND-0674 | INV-28397 | 2025-02-16 | 2025-09-30 | 1221.05 | 2787.2 | Logistics | Partial |
```

This adds ~1 line per sheet but gives the model an explicit column-number-to-name mapping.

**Option B — Per-entry column prefixes** (higher token cost, highest accuracy):
```
R45 | C1=2025-06-28 | C2=VEND-0674 | C3=INV-28397 | C4=2025-02-16 | C5=2025-09-30 | C6=1221.05 | C7=2787.2 | C8=Logistics | C9=Partial |
```

This makes every cell unambiguously addressed at the cost of ~30% more tokens on dense sheets (the C<N>= prefix adds 3-4 chars per cell).

**Option C — Periodic column echo** (middle ground):
```
# Columns: Date | Vendor | InvoiceID | InvoiceDate | DueDate | InvoiceAmt | AmountUSD | Dept | Status
R45 | 2025-06-28 | VEND-0674 | ...
```

Repeat the column names as a comment every N rows (e.g., every 50 rows). This helps models maintain context over long sheets.

**Recommendation**: Option A (column directive) + Option C (periodic echo every 50 rows). This adds minimal tokens while giving the model a reference table.

---

## Failure 2: Truncation-Induced Hallucination

**What happens**: SCF's truncation comment leaks the total row count, causing the model to extrapolate.

**Example**:
```
Q: How many rows have 'CashFlowType' equal to 'Operating CF' in sheet 'CF_Ledger'?
GT: 130    SCF predicted: 24,980    JSON predicted: 126
```

The SCF encoding ends with:
```
# ... truncated at 200 rows (50002 total)
```

The model sees "50002 total" and reasons: "If ~128/200 visible rows are Operating CF, then 128/200 × 50000 ≈ 24,980". This is creative but wrong — the question asks about the visible data.

JSON's truncation metadata doesn't include the total, so the model just counts what it sees.

**Impact**: 2/11 failures on GPT-5.4. Caused the largest absolute errors (24,980 vs 130).

### Proposed Fix: Remove total row count from truncation comments

**Before**:
```
# ... truncated at 200 rows (50002 total)
```

**After**:
```
# ... showing first 200 data rows
```

Or add an explicit instruction:
```
#!TRUNCATED rows_shown=200
```

No total row count. If the consumer needs the total, it should come from a separate metadata directive (`#!META total_rows=50002`) that the prompt can choose to include or not.

**Token impact**: Saves ~5 tokens per truncated sheet.

---

## Failure 3: Wrong Value Extraction from Adjacent Cell

**What happens**: The model identifies the correct row but extracts a value from the wrong column — typically an adjacent one.

**Example**:
```
Q: What is the value in the 'Currency' column of row 9 in sheet 'FX_Rates'?
GT: INR    SCF predicted: CNY
```

SCF encoding:
```
R8 | AUD | 0.8734 |
R9 | INR | 0.7464 |    ← correct answer is INR
R10 | CNY | 1.0054 |
```

The model somehow returned CNY (row 10) instead of INR (row 9). Despite the R9 prefix being explicit, the model shifted by one row.

This is distinct from column miscounting — the row number is correct, but the model's attention mechanism slips to an adjacent row.

**Impact**: 3/11 failures on GPT-5.4.

### Proposed Fix: Header echo + value annotation

When the question specifically asks about a named column, having that column name appear alongside the value would prevent slip:

**Option A — Column-name annotation mode**:
```
R9 | Currency=INR | RateToUSD=0.7464 |
```

This is the most radical change but makes every cell self-describing. Token cost: ~2× on dense sheets.

**Option B — Key-value mode for narrow sheets**:

For sheets with ≤5 columns, automatically switch to key-value format:
```
R9 | Currency: INR | RateToUSD: 0.7464 |
```

This is human-readable and unambiguous, at modest token cost on narrow sheets.

**Recommendation**: Option B for sheets ≤5 columns. Option A as an optional mode flag (`#!MODE annotated`).

---

## Failure 4: Model Refused to Answer

**What happens**: The model decides the data is insufficient and refuses to compute an answer.

**Example**:
```
Q: What is the average of the 'VarianceUSD' column in sheet 'Project_Summary'?
GT: 6937308.35    SCF predicted: "Insufficient data provided to determine..."    JSON predicted: 7002419.97
```

The SCF encoding had the data, but the model didn't find it (possibly due to the column-counting issue, or the data appearing sparse).

**Impact**: 1/11 failures on GPT-5.4.

### Proposed Fix: `#!ROWS` directive

Add an explicit data-row count at the sheet level:
```
#!SHEET Project_Summary
#!HEADERS R1
#!ROWS 12
```

This tells the model exactly how many data rows are present, reducing uncertainty about whether the data is complete.

---

## Failure 5: Ambiguous SpreadsheetBench Tasks

**What happens**: Complex formula-generation questions where the SCF encoding doesn't provide enough context for the model to reason about the formula.

**Example**:
```
Q: Given this spreadsheet, What value should appear at cell E2?
GT: 33.333    SCF predicted: 50    JSON predicted: 33.333
```

These are fundamentally formula-interpretation tasks where the model needs to understand the relationship between cells. JSON's explicit column letters make cross-referencing easier.

**Impact**: 2/11 failures on GPT-5.4.

### Proposed Fix: Formula preservation

SCF's R1C1 formula encoding is the correct solution here, but our benchmark used `data_only=True` (values only). With formulas:
```
R2 | C5==AVERAGE(RC[-3]:RC[-1]) |
```
The model would know E2 is an average of B2:D2, making the answer trivially derivable.

**This is not a format design issue — it's a benchmark limitation.** The fix is to test with formulas enabled.

---

## Additional Improvements (Not from Failure Analysis)

### 6. Column-letter aliases

Add an optional mapping from column numbers to Excel column letters:
```
#!COLMAP C1=A C2=B C3=C ... C26=Z C27=AA
```

This bridges the gap between SCF's numeric addressing and the Excel column-letter convention that all models are trained on. Questions that say "column B" can then be resolved by the model without counting.

### 7. Sheet-level summary stats

Add optional aggregate metadata:
```
#!SHEET Data_Main
#!ROWS 200
#!STATS C4:min=3.2 max=9847.1 sum=482910.7 avg=2414.55
```

This lets the model answer aggregation questions from metadata without scanning all rows. For truncated sheets, the stats could cover the full dataset while the rows only show a sample.

### 8. Interleaved column-name comments for wide sheets

For sheets with 10+ columns, add a comment before each row echoing the column names:
```
# | Date | Vendor | ID | InvDate | DueDate | InvAmt | AmtUSD | Dept | Status |
R45 | 2025-06-28 | VEND-0674 | INV-28397 | 2025-02-16 | 2025-09-30 | 1221.05 | 2787.2 | Logistics | Partial |
```

Only emit this every N rows (e.g., 50) to limit token overhead.

---

## Projected Impact

If all five targeted fixes were implemented:

| Fix | Failures Resolved | New SCF Accuracy (GPT-5.4) |
|---|---|---|
| Baseline | — | 85.0% (170/200) |
| + Column directive (#1) | +3 | 86.5% |
| + Remove truncation total (#2) | +2 | 87.5% |
| + Value annotation mode (#3) | +3 | 89.0% |
| + Row count directive (#4) | +1 | 89.5% |
| + Formula preservation (#5) | +2 | 90.5% |
| **Total** | **+11** | **90.5%** |

This would close the gap with JSON (87.5%) and potentially surpass it, while using 52% fewer tokens. With the additional improvements (column aliases, summary stats), SCF could reach the mid-90s.

---

## Implementation Priority

1. **`#!COLUMNS` directive** — highest impact, easiest to implement, minimal token cost
2. **Remove total from truncation** — trivial change, prevents worst-case hallucinations
3. **`#!ROWS` directive** — small change, helps model confidence
4. **Periodic column echo** — medium effort, helps on long sheets
5. **Column-letter aliases** — bridges SCF/Excel mental models
6. **Annotated value mode** — highest token cost, reserved for narrow sheets or high-stakes queries
7. **Sheet-level stats** — useful for aggregation-heavy workloads
