# Ream

*Core specification, draft 9*

## Status

This document defines the core wire format for Ream. It is written as an RFC-style draft and uses normative language.

## 1. Abstract

Ream is a UTF-8, line-oriented, sparse text format for spreadsheet cell values, formulas, defined names, and named tables.

It is built around six rules:

- row records are addressed explicitly with absolute row numbers written as plain line labels
- columns are addressed by position and optional `B=` / `B:M=` entry prefixes
- selectors outside formulas use A1 notation
- direct cell and range coordinates inside formulas use R1C1 notation
- defined names and structured table references are first-class formula operands
- omitted cells are blank

Ream is meant to roundtrip sheet structure and cell content deterministically between spreadsheet state and text.

Ream core is sparse by design. It does not carry sheet extents, cached formula results, or presentation state unless an extension adds them.

## 2. Conformance language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

## 3. Core data model

A Ream document represents an ordered workbook.

A workbook contains:

- zero or more workbook-scoped defined names
- one or more sheets

A sheet contains:

- a unique sheet name
- a sparse set of cells keyed by absolute `(row, column)`
- zero or more sheet-scoped defined names
- zero or more named table declarations
- optional metadata directives

Rows and columns are 1-based.

A cell in the core model is one of:

- number
- string
- boolean
- error
- formula

Blank cells are not encoded. Omission means blank.

An empty string is not blank. It MUST be encoded explicitly.

A defined name binds an identifier to a target selector.

A named table binds an identifier to a rectangular area on one sheet. The top row of the area is the header row. The last row MAY be declared as a totals row. All rows between header and totals, or all rows below the header if there is no totals row, form the data body.

Table header labels are derived from the decoded string values in the header row cells of the table area. Ream core does not assign separate hidden per-column identifiers.

Ream core does not encode:

- sheet extents or used ranges
- cached formula results
- row heights
- column widths
- merged cells
- rich text
- charts
- conditional formatting
- macros
- objects
- calculation state
- hidden row or column state
- table styling, filter state, or sort state

## 4. Roundtrip contract

The Ream core roundtrip contract covers:

- sheet order
- sheet names
- every explicit cell's absolute row
- every explicit cell's absolute column
- every explicit cell's type
- every explicit cell's value or formula text
- workbook-scoped defined names
- sheet-scoped defined names
- named table declarations
- supported metadata directives and their selectors

The contract applies to parse -> serialize cycles over the same Ream document and to spreadsheet -> Ream -> spreadsheet cycles for the namespaces Ream core controls.

A consumer importing Ream into a spreadsheet MUST apply it to a blank sheet state, or clear the target sheet first for the namespaces Ream core controls. Otherwise omitted cells would keep stale content.

Because Ream core is sparse, it does not distinguish between "never populated" and "cleared to blank." Those are the same state.

## 5. File format

A Ream document is plain UTF-8 text.

LF and CRLF line endings MUST be accepted. Canonical output MUST use LF.

The first non-empty, non-comment line MUST be:

```text
#!REAM 9
```

Zero or more workbook-scoped `#!NAME` directives MAY appear after `#!REAM 9` and before the first `#!SHEET`.

Parsers MAY accept legacy headers `#!REAM 8` and `#!SCF 7` in compatibility mode. Canonical output MUST use `#!REAM 9`.

Each sheet MUST begin with:

```text
#!SHEET <sheet-name>
```

Sheet names MUST be unique within the document.

Comments start with `#` and are ignored, except directives, which start with `#!`. A line whose first two characters are `#!` is always a directive, not a comment.

Blank lines are ignored.

Physical line breaks are not allowed inside row records. String cells that contain line breaks MUST encode them using escapes inside quoted strings.

## 6. Directives

The core directives are:

```text
#!REAM 9
#!SHEET <sheet-name>
#!HEADERS <row-selector>
#!NAME <identifier> <name-target>
#!TABLE <identifier> <table-selector> [TOTALS]
#!FMT <selector> <metadata-value>
#!TAG <selector> <metadata-value>
#!NOTE <selector> <quoted-string>
```

`#!HEADERS` is a presentation hint only. It does not change cell addresses or parsing.

`#!FMT`, `#!TAG`, and `#!NOTE` do not change cell values or formulas.

`#!FMT` and `#!TAG` values are opaque text. They MAY be written as bare tokens or quoted strings.

A `#!NAME` that appears before the first `#!SHEET` is workbook-scoped.

A `#!NAME` that appears inside a sheet block is sheet-scoped to that sheet.

A `#!TABLE` is valid only inside a sheet block and declares a named table on that sheet.

A sheet MAY contain zero or more `#!HEADERS` directives. Together they define the set of worksheet rows that are presentation headers.

Workbook-scoped name identifiers MUST be unique case-insensitively across the workbook.

Table identifiers MUST be unique case-insensitively across the workbook.

Sheet-scoped name identifiers MUST be unique case-insensitively within the sheet.

To avoid ambiguous formula resolution:

- a workbook-scoped name MUST NOT case-insensitively equal any table identifier
- a sheet-scoped name MUST NOT case-insensitively equal any workbook-scoped name
- a sheet-scoped name MUST NOT case-insensitively equal any table identifier

Sheet-scoped names MAY repeat on different sheets.

Unknown directives that do not begin with `#!X-` MUST be rejected.

Unknown extension directives that begin with `#!X-` MAY be ignored.

## 7. Selectors and targets

Selectors are absolute and 1-based.

Ream uses A1 notation for selectors outside formulas. Canonical selectors MUST NOT use `$`. Parsers MAY accept `$` in non-canonical input and normalize it away.

Valid selector forms are:

```text
B3
B3:M13
3:3
3:5
B:B
B:E
```

Meanings:

- `B3` one cell
- `B3:M13` one rectangle
- `3:3` one whole row
- `3:5` a row span
- `B:B` one whole column
- `B:E` a column span

For `#!HEADERS`, only row selectors are valid:

```text
#!HEADERS 1:1
#!HEADERS 1:2
#!HEADERS 10:12
```

Canonical output MUST use uppercase column letters in selectors. Parsers MAY accept lowercase letters in non-canonical input.

### 7.1 Column labels

Column labels use the standard A1 bijective base-26 alphabet:

- `A` = 1
- `Z` = 26
- `AA` = 27
- `AZ` = 52
- `BA` = 53

A conforming parser MUST decode column labels case-insensitively.

Canonical output MUST use uppercase labels.

A conforming parser MUST reject invalid A1 column labels. A parser MAY additionally reject labels beyond its target spreadsheet engine's supported column limit.

### 7.2 Name targets

A `#!NAME` target is either a local selector or a sheet-qualified selector.

Examples:

```text
#!NAME tax_rate 'Assumptions'!B2
#!NAME monthly_rate B5:M5
```

For workbook-scoped `#!NAME`, the target MUST be sheet-qualified.

For sheet-scoped `#!NAME`, a bare selector is relative to the current sheet. A sheet-qualified selector is also allowed.

### 7.3 Table selectors and column names

A `#!TABLE` selector MUST be a rectangular selector of the form `A1:D10`.

Ream does not require header strings to be unique. Duplicate display headers preserve the source table shape more faithfully, but header-based structured references can become ambiguous as described in Section 10.1.2.

The first row of the rectangle is the table header row.

If the optional `TOTALS` keyword is present, the last row of the rectangle is the totals row.

Each header cell inside the table area MUST be a string cell.

Header strings MAY repeat within one table. These decoded strings are display labels, not hidden canonical column identifiers.

Structured references in formulas use these exact header strings, with `]` escaped as `]]` inside bracketed column references.

Examples:

```text
#!TABLE Sales A10:D13
#!TABLE Forecast A5:D8 TOTALS
```

## 8. Row records

A row record encodes one absolute spreadsheet row.

Syntax:

```text
<row-number> | <entry> | <entry> | ... |
```

Example:

```text
12 | EBITDA | B:M==R4C-R10C |
```

The row number is the actual spreadsheet row number.

Omitted row numbers mean blank rows.

A sheet MUST NOT contain the same row number twice.

## 9. Entry model

Each row record is parsed left to right with a column cursor.

Initial cursor value: `1`

After trimming outer ASCII spaces and tabs from the entry text, each entry is one of:

- bare scalar
- empty entry
- addressed scalar: `<col>=<scalar>` or `<col1>:<col2>=<scalar>`

An addressed entry MAY jump the cursor forward. A bare scalar always writes at the current cursor column.

### 9.1 Bare scalar

Assign to the current cursor column, then advance cursor by 1.

Example:

```text
2 | Revenue | 1000 | 1050 |
```

Maps to:

- `A2 = "Revenue"`
- `B2 = 1000`
- `C2 = 1050`

### 9.2 Empty entry

An empty entry represents a blank cell at the current cursor column, then advances cursor by 1.

Example:

```text
2 | Revenue | | 1050 |
```

Maps to blank `B2`, then `1050` at `C2`.

Empty entries are allowed for permissive parsing. Canonical output MUST NOT use them.

### 9.3 Addressed single-cell entry

`<col>=<scalar>` assigns the scalar to absolute column `<col>` in the current row.

Columns from the current cursor through the column before `<col>` are blank.

The addressed column MUST be greater than or equal to the current cursor.

After assignment, the cursor becomes the addressed column plus 1.

Example:

```text
5 | D=-50000 |
```

Maps to blank `A5:C5`, then `-50000` at `D5`.

### 9.4 Addressed range entry

`<col1>:<col2>=<scalar>` assigns the same scalar token to every column from `<col1>` through `<col2>` in the current row.

Columns from the current cursor through the column before `<col1>` are blank.

`<col1>` MUST be greater than or equal to the current cursor.

`<col2>` MUST be greater than or equal to `<col1>`.

After assignment, the cursor becomes the addressed end column plus 1.

Example:

```text
7 | B:M=8500 |
```

Maps `8500` into `B7:M7`.

For formulas, the same formula text is assigned to every addressed cell, and each cell evaluates it using normal R1C1 semantics relative to its own location.

### 9.5 Why addressed formulas use `==`

Addressed entries use `=` as the address/value separator. Formula scalars also begin with `=`.

As a result, an addressed formula is written with two adjacent equals signs:

```text
B==R[-1]C
B:M==R[-1]C*0.6
E==1
F=="A"
```

The first `=` belongs to the addressed-entry syntax. The second `=` is the formula marker.

This rule is required for deterministic roundtrips. Without it, `E=1` would be ambiguous between the number `1` and the formula `=1`.

## 10. Scalar types

A scalar is one of:

- formula
- quoted string
- boolean
- error
- number
- raw string

Classification order for bare scalars is:

1. formula
2. quoted string
3. boolean
4. error
5. number
6. raw string

Classification order for addressed scalars is the same. Addressed entries use the same scalar grammar as bare entries after the address/value separator.

This means:

- `B=Jan` is a string
- `B==R[-1]C` is a formula
- `B=1` is a number
- `B==1` is the formula `=1`

### 10.1 Formula

A formula scalar starts with `=`.

All formulas in Ream core MUST use the Ream formula profile:

- direct cell and range coordinates MUST use R1C1 notation
- comma is the argument separator
- period is the decimal point inside formulas
- function names use the English spellings of the target spreadsheet engine
- sheet names are single-quoted when needed
- formulas MAY additionally reference Ream defined names and Ream tables as described below

Examples:

```text
=R[-1]C*0.6
=R4C-R10C
=IF(R[-2]C>0,R[-1]C/R[-2]C,0)
='Sheet With Spaces'!R1C2
=SUM(revenue_inputs)
=SUM(Sales[Revenue])
=Sales[@[Qty]]*Sales[@[Price]]
```

A conforming parser MUST preserve formula text byte-for-byte after the leading `=`.

A conforming exporter from a spreadsheet SHOULD normalize formulas into the Ream formula profile.

#### 10.1.1 Defined names in formulas

A formula MAY reference defined names declared by `#!NAME`.

Valid forms are:

- bare identifier, for workbook-scoped names and current-sheet sheet-scoped names
- sheet-qualified identifier, for sheet-scoped names on any sheet

Examples:

```text
=SUM(revenue_inputs)
='Assumptions'!monthly_rate*R[-1]C
```

A bare identifier followed immediately by `(` is parsed as a function call, not a defined-name reference.

A bare identifier not followed by `(` resolves as follows:

1. current-sheet sheet-scoped name, if one exists
2. workbook-scoped name, if one exists
3. table identifier, if one exists

The identifier collision rules in Section 6 ensure this lookup is deterministic.

Canonical formulas SHOULD emit current-sheet sheet-scoped names as bare identifiers. A sheet-qualified reference to a sheet-scoped name on the same sheet MAY be accepted by a permissive parser but is non-canonical. Cross-sheet sheet-scoped name references MUST be sheet-qualified.

#### 10.1.2 Structured table references in formulas

A formula MAY reference a table declared by `#!TABLE`.

The Ream structured-reference profile is:

- `Table[#Data]`
- `Table[#Headers]`
- `Table[#Totals]`
- `Table[#All]`
- `Table[Column]`
- `Table[[Column1]:[Column2]]`
- `Table[[#Data],[Column]]`
- `Table[[#Data],[Column1]:[Column2]]`
- `Table[[#Headers],[Column]]`
- `Table[[#Headers],[Column1]:[Column2]]`
- `Table[[#Totals],[Column]]`
- `Table[[#Totals],[Column1]:[Column2]]`
- `Table[[#All],[Column]]`
- `Table[[#All],[Column1]:[Column2]]`
- `Table[@[Column]]`
- `Table[@[Column1]:[Column2]]`

Area specifiers are canonicalized as `#Data`, `#Headers`, `#Totals`, and `#All`.

`Table[Column]` is shorthand for `Table[[#Data],[Column]]`.

`Table[[Column1]:[Column2]]` is shorthand for `Table[[#Data],[Column1]:[Column2]]`.

A bare table identifier without brackets MAY be accepted by a permissive parser as a non-canonical alias for `Table[#Data]`. Canonical output MUST use the explicit `#Data` form.

A current-row reference such as `Table[@[Column]]` is valid only when the anchor cell of the formula lies in the data-body area of that same table.

A permissive parser MAY accept non-canonical current-row forms such as `[@Column]` and `[@[Column1]:[Column2]]` inside table formulas. Canonical output MUST include the explicit table identifier.

If a table does not declare `TOTALS`, references using `#Totals` are invalid.

Column names in structured references MUST use the exact header-row strings from the table declaration, with `]` escaped as `]]`.

If a table contains duplicate decoded header strings, a structured reference that identifies one or more columns by header text is valid only when each referenced header text resolves to exactly one column in that table. Structured-reference forms that do not identify specific columns, such as `Table[#Data]`, remain valid. Consumers that validate structured references MUST treat ambiguous header-based references as invalid. Exporters SHOULD rewrite ambiguous header-based structured references to equivalent R1C1 formulas.

Examples:

```text
=SUM(Sales[Revenue])
=SUM(Sales[[#All],[Revenue]])
=SUMIFS(Sales[Revenue],Sales[Region],Sales[@[Region]])
=Sales[@[Qty]]*Sales[@[Price]]
```

A conforming exporter from a spreadsheet SHOULD normalize structured references to this Ream profile and SHOULD use the declaration case of the table identifier plus the exact header cell text of the referenced columns when those header texts resolve uniquely. When they do not, the exporter SHOULD emit equivalent R1C1 references instead of ambiguous structured references.

### 10.2 Number

A number is a decimal numeric literal.

Accepted forms include:

```text
1000
-50.5
1.2e6
.5
```

Canonical output MUST use plain decimal form without exponent and MUST follow these rules:

- no leading `+`
- use `0` for both `0` and `-0`
- no leading zeros in the integer part except the single zero in `0` or `0.x`
- use a leading zero before a decimal point, so `.5` canonicalizes to `0.5`
- no trailing zeros after the decimal point
- no trailing decimal point

Examples:

- `0012` -> `12`
- `.5` -> `0.5`
- `1.2300` -> `1.23`
- `1E+06` -> `1000000`

### 10.3 Boolean

Accepted values are `TRUE` and `FALSE`.

Parsers MAY accept case-insensitive input. Canonical output MUST use uppercase.

### 10.4 Error

Accepted core errors are:

```text
#N/A
#REF!
#VALUE!
#DIV/0!
#NULL!
#NAME?
#NUM!
#SPILL!
#CALC!
```

Canonical output MUST use uppercase spelling exactly as listed.

### 10.5 Quoted string

Quoted strings are enclosed in double quotes.

They are required when the string:

- contains `|`
- contains a physical line break
- contains a double quote
- contains leading or trailing whitespace
- is empty
- starts with `=`
- starts with `[`
- starts with `"`
- would otherwise parse as a boolean, error, or number
- would otherwise match the addressed-entry prefix pattern `<col>=` or `<col1>:<col2>=`

Inside quoted strings:

- `""` means one literal `"`
- `\\` means one literal backslash
- `\n` means line feed
- `\r` means carriage return
- `\t` means tab

Examples:

```text
""
"1000"
"TRUE"
"=Not a formula"
"B=not an address"
"he said ""hello"""
"line 1\nline 2"
```

### 10.6 Raw string

A raw string is any unquoted scalar that is not parsed as another scalar type and does not contain `|`, physical line breaks, or `"`.

Examples:

```text
Revenue
Jan
Gross Profit
usd0
```

## 11. Row tokenization and quoting

Row tokenization is quote-aware.

A `|` is an entry separator only when it appears outside a double-quoted substring.

This rule applies uniformly to:

- quoted string cells
- formula text that contains string literals
- addressed formulas that contain string literals

Examples that MUST remain a single entry each:

```text
9 | "A|B|C" |
10 | =IF(RC1="A|B",1,0) |
11 | B==IF(RC1="A|B",1,0) |
```

Within a double-quoted substring, `""` is a literal quote and does not end the substring.

Tokenization does not interpret backslash escapes. Backslash escapes are interpreted only when decoding quoted string cell values.

A conforming row tokenizer MAY be implemented by scanning a row left to right and splitting only on `|` characters that occur while not inside a double-quoted substring.

## 12. Entry parsing algorithm

After row tokenization, each entry is parsed as follows:

1. Trim outer ASCII spaces and tabs.
2. If the entry is empty, emit an empty entry.
3. If the entry matches `<col1>:<col2>=` or `<col>=` using valid A1 column labels, parse it as an addressed entry.
4. Otherwise parse it as a bare scalar.

This means a bare string that looks like an addressed entry MUST be quoted.

Examples:

```text
2 | "B=not an address" |
3 | B=not an address |
```

The first is a string in the current cursor column. The second writes the string `not an address` into column `B`.

## 13. Canonical serialization

Ream defines a canonical form for deterministic export.

### 13.1 File and sheet layout

- The first line MUST be `#!REAM 9`.
- Workbook-scoped `#!NAME` lines, if present, MUST appear before the first `#!SHEET`.
- Workbook-scoped `#!NAME` lines MUST be sorted by identifier in ascending byte order.
- Sheets MUST appear in workbook order.
- Each sheet MUST begin with `#!SHEET <sheet-name>`.
- `#!HEADERS` lines, if present, MUST appear before sheet-scoped `#!NAME` and `#!TABLE` lines.
- Sheet-scoped `#!NAME` and `#!TABLE` lines, if present, MUST appear before row records.
- Within a sheet block, sheet-scoped `#!NAME` lines MUST appear before `#!TABLE` lines.
- Row records MUST appear in strictly increasing row order.
- `#!FMT`, `#!TAG`, and `#!NOTE` lines, if present, MUST appear after row records.
- Blank lines and comments MUST NOT appear in canonical output.

### 13.2 Directive spelling

Canonical output MUST use uppercase directive names exactly as defined in this specification.

For `#!SHEET`, canonical output MUST use a bare sheet name when the name is representable as a bare token. Otherwise it MUST use a quoted string.

For `#!HEADERS`, canonical output MUST sort header spans by selector order and MUST merge overlapping or directly adjacent spans into the minimal set of disjoint row selectors.

For `#!NAME`, canonical output MUST use a bare identifier. Workbook-scoped `#!NAME` targets MUST be sheet-qualified. Sheet-qualified targets MUST use the same sheet-name quoting rules as formulas.

For `#!TABLE`, canonical output MUST omit `TOTALS` when the table has no totals row and MUST emit `TOTALS` when the table has a totals row.

For `#!FMT` and `#!TAG`, canonical output MUST use a bare token when the value is representable as one. Otherwise it MUST use a quoted string.

### 13.3 Row output

- A canonical writer MUST emit one row record for each row that contains at least one explicit cell.
- A canonical writer MUST NOT emit an all-blank row record.
- Empty entries MUST NOT appear in canonical output.
- Gaps MUST be represented by the next emitted cell or range using `<col>=` or `<col1>:<col2>=`.

### 13.4 Range compaction

Within a row, a canonical writer MUST coalesce maximal contiguous runs of identical scalar tokens.

For canonical purposes, identical means:

- same scalar type
- same canonical scalar text

Examples:

```text
6 | B:C=50 | D:M=52 |
7 | B:M=8500 |
8 | B:M==R[-2]C*R[-1]C |
```

### 13.5 Singleton rules

- A singleton at the current cursor MUST be emitted as a bare scalar.
- A singleton after a gap MUST be emitted as `<col>=<scalar>`.
- A run of length greater than 1 MUST be emitted as `<col1>:<col2>=<scalar>`.

Examples:

```text
2 | Revenue | 1000 | 1050 |
5 | D=-50000 |
7 | B:M=8500 |
```

### 13.6 String form

A canonical writer SHOULD use raw strings when allowed.

Otherwise it MUST use quoted strings.

### 13.7 Exact spacing

Canonical row spacing is exact and unique:

```text
12 | EBITDA | B:M==R4C-R10C |
```

Canonical output MUST use:

- exactly one space after the row label
- exactly one space on each side of every `|`
- no alignment padding inside entries

Canonical directive lines MUST use exactly one ASCII space between the directive name and each argument.

### 13.8 Names, tables, and metadata order

In canonical output:

- workbook-scoped `#!NAME` lines MUST be sorted by identifier in ascending byte order
- within each sheet block, `#!HEADERS` lines MUST be sorted by selector order after merging overlaps and adjacencies
- sheet-scoped `#!NAME` lines MUST be sorted by identifier in ascending byte order
- `#!TABLE` lines MUST be sorted by identifier in ascending byte order
- `#!FMT`, `#!TAG`, and `#!NOTE` lines MUST be sorted by selector order, then by value or note text in ascending byte order

Selector order is defined by first normalizing each selector to the tuple `(r1, c1, r2, c2)` and then comparing those tuples lexicographically as integers.

Normalization rules:

- `B3` -> `(3, 2, 3, 2)`
- `B3:M13` -> `(3, 2, 13, 13)`
- `3:3` -> `(3, 0, 3, 0)`
- `3:5` -> `(3, 0, 5, 0)`
- `B:B` -> `(0, 2, 0, 2)`
- `B:E` -> `(0, 2, 0, 5)`

If a metadata model cannot be losslessly normalized into that ordering without changing semantics, the metadata is outside Ream core and MUST be carried by an extension.

## 14. Parsing requirements

A conforming parser MUST reject:

- duplicate row numbers in the same sheet
- duplicate `#!SHEET` names in the same document
- duplicate workbook-scoped name identifiers case-insensitively
- duplicate table identifiers case-insensitively
- duplicate sheet-scoped name identifiers case-insensitively within one sheet
- any sheet-scoped name that case-insensitively collides with a workbook-scoped name or table identifier
- any workbook-scoped name that case-insensitively collides with a table identifier
- overlapping assignments within one row
- backward jumps such as `B=` after the cursor has already moved past column `B`
- malformed selectors
- malformed name targets
- malformed quoted strings
- malformed directives
- row numbers less than 1
- invalid A1 column labels
- addressed ranges where the end column precedes the start column
- `#!TABLE` directives whose selector is not rectangular
- overlapping table areas on the same sheet
- table header cells that are not string cells
- current-row structured references used outside a table data row
- use of `#Totals` against a table that does not declare `TOTALS`

A permissive parser MAY accept non-canonical input such as:

- comments
- blank lines
- lowercase column letters in selectors and addressed entries
- optional `$` markers in A1 selectors and addressed entries
- empty row entries
- unsorted metadata directives
- a bare table identifier as an alias for `Table[#Data]`
- implicit current-row structured references such as `[@Column]` inside table formulas

A permissive parser SHOULD normalize accepted input through canonical serialization.

## 15. Name, table, and metadata semantics

The core directives have these semantics:

- `#!HEADERS` marks one or more row spans intended as headers for presentation. Repeated `#!HEADERS` directives accumulate.
- `#!NAME` binds an identifier to a target selector.
- `#!TABLE` declares a named table whose header row is the first row of the selector and whose optional totals row is the last row when `TOTALS` is present.
- `#!FMT` associates a selector with an opaque format value such as `usd0`, `pct1`, or `"currency usd"`.
- `#!TAG` associates a selector with an opaque semantic value such as `input`, `calc`, `output`, or `"sales input"`.
- `#!NOTE` attaches text to a selector.

The header text used by structured references is derived from the decoded string values of the header-row cells inside the table area.

A name target is a static selector, not an arbitrary formula. Ream core names therefore represent named ranges, named cells, named rows, or named columns, but not formula-defined names.

The core format does not prescribe how spreadsheet engines store these directives internally. Consumers SHOULD preserve them when possible.

## 16. Extensions

Ream core reserves the `#!X-` directive namespace for extensions.

Examples of likely extensions:

```text
#!X-DIM 1048576x16384
#!X-EVAL G2:M2 [1296,1399.68,1511.6544,...]
```

`#!X-DIM` could preserve exact worksheet extents.

`#!X-EVAL` could preserve cached formula results without mixing them into the row grammar.

These are not part of the core spec.

## 17. Security considerations

Formulas are active content.

A consumer opening untrusted Ream SHOULD apply the same trust rules it would apply to an untrusted spreadsheet, including controls for:

- external workbook references
- volatile formulas
- automatic recalculation
- data connections

A consumer MAY offer a values-only import mode that converts formula scalars to strings instead of executable formulas.

## 18. Examples

### 18.1 P&L with a workbook-scoped name

```text
#!REAM 9
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
7 | Avg Salary | B:M=8500 |
8 | Payroll | B:M==R[-2]C*R[-1]C |
9 | Rent | B:M=15000 |
10 | Total OpEx | B:M==R[-2]C+R[-1]C |
12 | Tax | B:M==R4C*tax_rate |
13 | Net Income | B:M==R4C-R10C-R[-1]C |

#!FMT 2:4 usd0
#!FMT 6:6 num0
#!FMT 7:13 usd0
#!TAG B2:F2 "sales input"
#!TAG G2:M2 "forecast calc"
#!TAG B13:M13 output
```

### 18.2 Table formulas with current-row references

```text
#!REAM 9
#!SHEET Sales
#!TABLE Sales A10:D13

10 | Product | Qty | Price | Revenue |
11 | A | 10 | 5 | =Sales[@[Qty]]*Sales[@[Price]] |
12 | B | 8 | 6 | =Sales[@[Qty]]*Sales[@[Price]] |
13 | C | 12 | 4 | =Sales[@[Qty]]*Sales[@[Price]] |
```

### 18.3 Table aggregation formula outside the table

```text
#!REAM 9
#!SHEET Sales
#!TABLE Sales A10:D13

10 | Product | Qty | Price | Revenue |
11 | A | 10 | 5 | 50 |
12 | B | 8 | 6 | 48 |
13 | C | 12 | 4 | 48 |
20 | Total Revenue | =SUM(Sales[Revenue]) |
```

### 18.4 Table with totals row

```text
#!REAM 9
#!SHEET Forecast
#!TABLE Forecast A5:D8 TOTALS

5 | Region | Units | Price | Revenue |
6 | East | 10 | 5 | =Forecast[@[Units]]*Forecast[@[Price]] |
7 | West | 12 | 6 | =Forecast[@[Units]]*Forecast[@[Price]] |
8 | Total | 22 | 11 | =SUM(Forecast[[#Data],[Revenue]]) |
```

### 18.5 Formula constants and addressed strings

```text
3 | B==1 | C=="A" | D="A" |
```

This means:

- `B3` contains the formula `=1`
- `C3` contains the formula `="A"`
- `D3` contains the string `A`

### 18.6 Formula with a pipe character inside a string literal

```text
5 | B==IF(RC1="A|B",1,0) |
```

This row has one entry after tokenization.

### 18.7 Bare string that looks like an addressed entry

```text
7 | "B=not an address" |
```

The quotes are required.

### 18.8 Multiple header regions and quoted metadata values

```text
#!REAM 9
#!SHEET Ops
#!HEADERS 1:2
#!HEADERS 10:10

1 | B=Jan | C=Feb |
2 | B=Plan | C=Actual |
10 | A=Notes |

#!FMT B:C "currency input"
#!TAG B:C "sales input"
```


### 18.9 Repeatable headers and quoted metadata values

```text
#!REAM 9
#!SHEET Ops
#!HEADERS 1:2
#!HEADERS 10:10

1 | B=Jan | Feb |
2 | Revenue | 100 | 110 |
10 | Notes | Open |

#!FMT B2:C2 "currency usd0"
#!TAG B2:C2 "sales input"
```

In canonical form, multiple `#!HEADERS` directives remain separate only when their row spans are disjoint and non-adjacent.

## 19. Outer syntax and tokenizer

ABNF is used for the outer line structure. Row entry splitting is defined algorithmically in Section 11.

```abnf
file            = *(blank / comment) ream-line nl
                  *(workbook-item nl / blank / comment)
                  1*(sheet-block / blank / comment)

workbook-item   = name-line / ext-line

sheet-block     = sheet-line nl
                  *(sheet-item nl / blank / comment)

sheet-item      = headers-line / name-line / table-line / fmt-line /
                  tag-line / note-line / row-line / ext-line

ream-line       = "#!REAM" SP "9"
sheet-line      = "#!SHEET" SP name
headers-line    = "#!HEADERS" SP row-sel
name-line       = "#!NAME" SP ident SP name-target
table-line      = "#!TABLE" SP ident SP rect-sel [SP "TOTALS"]
fmt-line        = "#!FMT" SP selector SP meta-value
tag-line        = "#!TAG" SP selector SP meta-value
note-line       = "#!NOTE" SP selector SP qstring
ext-line        = "#!X-" ident *(SP ext-token)

row-line        = row-label SP "|" row-body "|"
row-label       = uint
row-body        = *row-char

name-target     = selector / qualified-selector
qualified-selector = sheet-ref "!" selector
sheet-ref       = qstring / bare-name

selector        = rect-sel / cell-sel / row-sel / col-sel
cell-sel        = col-label uint
rect-sel        = col-label uint ":" col-label uint
row-sel         = uint ":" uint
col-sel         = col-label ":" col-label

name            = qstring / bare-name
bare-name       = 1*(name-char / UTF8-nonascii)
ident           = ALPHA *(ALPHA / DIGIT / "_" / "-" / ".")
meta-value      = token / qstring
token           = 1*(token-char / UTF8-nonascii)
ext-token       = 1*(%x21-7E / UTF8-nonascii)
col-label       = 1*3ALPHA

qstring         = DQUOTE *qchar DQUOTE
qchar           = qsafe / esc / dquote-esc
qsafe           = %x20-21 / %x23-5B / %x5D-7E / UTF8-nonascii
esc             = "\\" ("\\" / "n" / "r" / "t")
dquote-esc      = DQUOTE DQUOTE

name-char       = %x24-26 / %x28-5A / %x5C / %x5E-7E
token-char      = %x21 / %x24-26 / %x28-5B / %x5D-7E
row-char        = %x09 / %x20-7E / UTF8-nonascii

blank           = *WSP nl
comment         = "#" [ %x20-7E / UTF8-nonascii ]* nl
nl              = %x0A / %x0D.0A
WSP             = SP / HTAB
SP              = %x20
HTAB            = %x09
DIGIT           = %x30-39
uint            = %x31-39 *DIGIT
ALPHA           = %x41-5A / %x61-7A
DQUOTE          = %x22
```

### 19.1 Row tokenizer pseudocode

```text
function split_row_body(row_body):
    entries = []
    buf = ""
    in_quotes = false
    i = 0

    while i < len(row_body):
        ch = row_body[i]

        if ch == '"':
            if in_quotes and i + 1 < len(row_body) and row_body[i + 1] == '"':
                buf += '""'
                i += 2
                continue
            in_quotes = not in_quotes
            buf += ch
            i += 1
            continue

        if ch == '|' and not in_quotes:
            entries.append(buf)
            buf = ""
            i += 1
            continue

        buf += ch
        i += 1

    entries.append(buf)
    return entries
```

## 20. Notes for implementers

- Ream core intentionally omits used range data. A sheet's explicit cell map is the whole core state.
- Cached formula results belong in an extension if needed.
- Workbook-scoped names appear before the first `#!SHEET`. Sheet-scoped names appear inside sheet blocks.
- A `#!TABLE` declaration is structural only. It does not carry table styling or filter state.
- Table header labels come from header-row string cells. Duplicate header strings are allowed. Preserve those strings exactly for structured references when they resolve uniquely. When they do not, normalize the affected formulas to R1C1 or use an extension.
- When duplicate header strings exist in one table, header-based structured references are only safe when each referenced header text resolves to exactly one column. Exporters should rewrite ambiguous cases to equivalent R1C1 formulas.
- Canonical structured references should include an explicit table identifier, even for current-row references.
- Addressed formulas use `==` by design. Do not collapse them to a single `=` in canonical output.
- Ream uses A1 selectors outside formulas and R1C1 coordinates inside formulas. That split is intentional: A1 is easier to read in metadata and row-address prefixes, while R1C1 preserves copy-fill semantics inside formulas.
- A permissive importer MAY accept legacy headers `#!REAM 8` and `#!SCF 7` as compatibility aliases for `#!REAM 9` and MAY offer broader compatibility mode for earlier experimental drafts, but those spellings are not part of Ream 9.
