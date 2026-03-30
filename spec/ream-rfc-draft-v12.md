# Ream

*Core specification, draft 12*

## Status

This document defines the core wire format for Ream. It is written as an RFC-style draft and uses normative language.

This draft makes two parser-visible changes.

First, a record prefix may now identify either one row or a contiguous row span. A single physical line can therefore encode one row, a vertical run, or a full rectangle when combined with an addressed column range.

Second, canonical serialization now performs two-dimensional compaction: maximal identical horizontal runs are merged vertically when they align, then emitted as row-span records. This allows repeated values and repeated formulas to be represented compactly across rows as well as across columns.

The wire header for this draft is `#!REAM 11`.

## 1. Abstract

Ream is a UTF-8, line-oriented, sparse text format for spreadsheet cell values, formulas, defined names, named tables, and light metadata.

It is built around eight rules:

- record prefixes use absolute worksheet row numbers and may denote either one row or a contiguous row span
- columns are addressed by position and optional A1-style entry prefixes such as `B=` and `B:M=`
- selectors outside formulas use A1 notation
- direct cell and range coordinates inside formulas use R1C1 notation
- defined names and structured table references are first-class formula operands
- dates, times, datetimes, and other display-sensitive literal values are rendered in human-readable plain text
- omitted cells are blank
- one physical line may encode a rectangle of repeated values or repeated formulas

Ream is meant to roundtrip sheet structure and cell content deterministically between spreadsheet state and text while staying visually close to a spreadsheet row by row.

Ream core is sparse by design. It does not carry sheet extents, cached formula results, or exact spreadsheet number-format codes unless an extension adds them.

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
- date
- time
- datetime
- string
- boolean
- error
- formula

A non-formula literal MAY additionally carry a display annotation: a quoted plain-text rendering attached inline in the Ream surface. A display annotation does not change the underlying cell value.

Blank cells are not encoded. Omission means blank.

An empty string is not blank. It MUST be encoded explicitly.

A defined name binds an identifier to a target selector.

A named table binds an identifier to a rectangular area on one sheet. The top row of the area is the header row. The last row MAY be declared as a totals row. All rows between header and totals, or all rows below the header if there is no totals row, form the data body.

Table header labels are derived from the decoded string values in the header row cells of the table area. Ream core does not assign hidden per-column identifiers.

Ream core does not encode:

- sheet extents or used ranges
- cached formula results
- exact spreadsheet number-format codes
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
- every explicit cell's display annotation text, when present
- workbook-scoped defined names
- sheet-scoped defined names
- named table declarations
- supported metadata directives and their selectors

The contract applies to parse -> serialize cycles over the same Ream document and to spreadsheet -> Ream -> spreadsheet cycles for the namespaces Ream core controls.

A consumer importing Ream into a spreadsheet MUST apply it to a blank sheet state, or clear the target sheet first for the namespaces Ream core controls. Otherwise omitted cells would keep stale content.

Because Ream core is sparse, it does not distinguish between "never populated" and "cleared to blank." Those are the same state.

Ream core does not promise exact recreation of source spreadsheet number-format codes. Instead, it preserves human-readable date, time, datetime, and other display-oriented literal surfaces directly in the row data when they matter.

Ream 11 intentionally does **not** preserve, in addressed form, the difference between some constant formulas and overlapping literal surfaces. For example, an addressed `B=1` is the number `1`, not a preserved distinction between the literal `1` and the formula `=1`. Likewise, an addressed `B=2025-01-31` is a date literal, not a preserved distinction between that literal and a constant formula returning the same date. Bare formulas at the current cursor position still preserve the leading `=` marker.

## 5. File format

A Ream document is plain UTF-8 text.

LF and CRLF line endings MUST be accepted. Canonical output MUST use LF.

The first non-empty, non-comment line MUST be:

```text
#!REAM 11
```

Zero or more workbook-scoped `#!NAME` directives MAY appear after `#!REAM 11` and before the first `#!SHEET`.

Parsers MAY accept `#!REAM 10` and earlier experimental headers in compatibility mode. Canonical output MUST use `#!REAM 11`.

Each sheet MUST begin with:

```text
#!SHEET <sheet-name>
```

Sheet names MUST be unique within the document.

Comments start with `#` and are ignored, except directives, which start with `#!`. A line whose first two characters are `#!` is always a directive, not a comment.

Comment lines and blank lines MAY appear anywhere outside record lines, including between workbook-scoped directives, between sheet directives, between record lines, and between metadata directives. Parsers MUST ignore them. Canonical output MUST omit them.

Physical line breaks are not allowed inside record lines. String cells that contain line breaks MUST encode them using escapes inside quoted strings.

## 6. Directives

The core directives are:

```text
#!REAM 11
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

`#!FMT` MAY describe source formatting or downstream formatting intent, but it is **not** the mechanism by which Ream core makes literal values human-readable. Human-readable literal rendering lives directly in cell scalars through date, time, datetime, and display-annotation syntax.

A `#!NAME` that appears before the first `#!SHEET` is workbook-scoped.

A `#!NAME` that appears inside a sheet block is sheet-scoped to that sheet.

A `#!TABLE` is valid only inside a sheet block and declares a named table on that sheet.

A sheet MAY contain zero or more `#!HEADERS` directives. Together they define the set of worksheet rows that are presentation headers. `#!HEADERS` directives MAY appear anywhere within a sheet block. Their placement carries no semantics.

Except for workbook-scoped `#!NAME` directives, which MUST appear before the first `#!SHEET`, the placement of sheet-scoped directives within a sheet block carries no semantics. Canonical output normalizes their placement as defined in Section 13.

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

A workbook-scoped `#!NAME` target MUST be sheet-qualified in canonical output.

A sheet-scoped `#!NAME` target MUST be unqualified in canonical output.

### 7.3 Tables

A `#!TABLE` target MUST be a rectangular cell selector on the current sheet.

The first row of the selector is the header row.

If `TOTALS` is present, the last row of the selector is the totals row.

Each header cell inside the table area MUST be a string cell.

Header strings MAY repeat within one table. These decoded strings are display labels, not hidden canonical column identifiers.

Structured references in formulas use these exact header strings, with `]` escaped as `]]` inside bracketed column references.

Examples:

```text
#!TABLE Sales A10:D13
#!TABLE Forecast A5:D8 TOTALS
```

## 8. Grid records

A Ream record line encodes one worksheet row or one contiguous row span.

Syntax:

```text
<row-prefix> | <entry> | <entry> | ... |
```

`<row-prefix>` is either:

- `<row>`
- `<row1>:<row2>`

Examples:

```text
12 | EBITDA | B:M=R4C-R10C |
12:20 | B:M=8500 |
24:36 | N=R[-1]C*1.08 |
```

The row numbers are actual worksheet row numbers.

A row span is inclusive. `12:20` means rows 12 through 20.

Omitted row numbers mean untouched rows unless some other record line assigns cells there.

The row body is parsed once and applied independently to every targeted row in the prefix span. The column cursor resets to `1` for each targeted row.

A sheet MAY contain multiple record lines that touch the same worksheet row or row span, provided the resulting cell assignments are disjoint. Ream core state is the union of all explicit cell assignments produced by all record lines in the sheet.

A conforming parser MUST reject duplicate cell assignments, whether they arise within one record line or across multiple record lines.

## 9. Entry model

Each record line is parsed left to right with a column cursor.

Initial cursor value: `1` for each targeted row in the row prefix span.

After trimming outer ASCII spaces and tabs from the entry text, each entry is one of:

- bare scalar
- empty entry
- addressed single-column entry: `<col>=<rhs>`
- addressed column-range entry: `<col1>:<col2>=<rhs>`

A bare scalar always writes at the current cursor column in every targeted row.

An addressed entry MAY jump the cursor forward. The jump is interpreted independently for each targeted row, but because all targeted rows share the same body, the resulting column positions are identical across the full row span.

### 9.1 Bare scalar

A bare scalar assigns to the current cursor column in every targeted row, then advances the cursor by 1.

Example:

```text
2 | Revenue | 1000 | 1050 |
```

Maps to:

- `A2 = "Revenue"`
- `B2 = 1000`
- `C2 = 1050`

Example over a row span:

```text
10:12 | 0 |
```

Maps to:

- `A10 = 0`
- `A11 = 0`
- `A12 = 0`

### 9.2 Empty entry

An empty entry represents a blank cell at the current cursor column in every targeted row, then advances the cursor by 1.

Example:

```text
2 | Revenue | | 1050 |
```

Maps to blank `B2`, then `1050` at `C2`.

Example over a row span:

```text
10:12 | | B=1 |
```

Advances past column `A` for rows `10:12`, then writes `1` at `B10:B12`.

Empty entries are allowed for permissive parsing. Canonical output MUST NOT use them.

### 9.3 Addressed single-column entry

`<col>=<rhs>` assigns to absolute column `<col>` in every targeted row.

Columns from the current cursor through the column before `<col>` are blank in every targeted row.

The addressed column MUST be greater than or equal to the current cursor.

After assignment, the cursor becomes the addressed column plus 1.

Example:

```text
5 | D=-50000 |
```

Maps to blank `A5:C5`, then `-50000` at `D5`.

Example over a row span:

```text
20:24 | D=Closed |
```

Maps `Closed` to `D20:D24`.

### 9.4 Addressed column-range entry

`<col1>:<col2>=<rhs>` assigns the same cell content to every column from `<col1>` through `<col2>` in every targeted row.

Columns from the current cursor through the column before `<col1>` are blank in every targeted row.

`<col1>` MUST be greater than or equal to the current cursor.

`<col2>` MUST be greater than or equal to `<col1>`.

After assignment, the cursor becomes the addressed end column plus 1.

Example:

```text
7 | B:M=8500 |
```

Maps `8500` into `B7:M7`.

Example over a row span:

```text
7:12 | B:M=8500 |
```

Maps `8500` into every cell of `B7:M12`.

For formulas, the same formula text is assigned to every targeted cell, and each cell evaluates it using normal R1C1 semantics relative to its own location. This is what makes vertical repeated formulas and full rectangular repeated formulas compact in Ream.

## 10. Cell scalars and literal displays

A Ream cell scalar is one of:

- formula
- quoted string
- boolean
- error
- datetime
- date
- time
- number
- raw string

A non-formula number, date, time, or datetime MAY additionally carry a display annotation.

### 10.1 Bare-scalar classification

Bare entries classify their scalar text in this order:

1. formula
2. quoted string
3. boolean
4. error
5. annotated datetime
6. annotated date
7. annotated time
8. annotated number
9. datetime
10. date
11. time
12. number
13. raw string

This order matters. A text value that looks like another scalar type MUST be quoted to remain text.

### 10.2 Addressed RHS classification

Addressed entries use the same literal surface forms as bare entries, except that addressed formulas omit the leading `=` and are parsed as **formula bodies**.

After the address/value separator, the RHS is classified in this order:

1. quoted string
2. boolean
3. error
4. annotated datetime
5. annotated date
6. annotated time
7. annotated number
8. datetime
9. date
10. time
11. number
12. formula body
13. raw string

This means:

- `B=Jan` is the string `Jan`
- `B=TRUE` is the boolean `TRUE`
- `B=0.25@"25%"` is the number `0.25` with display annotation `25%`
- `B=2025-01-31` is a date
- `B=RC[-1]*1.08` is a formula
- `B:M=R[-2]C-R[-1]C` is a repeated formula over a rectangular area

Because literals are resolved first, Ream 11 intentionally does not distinguish addressed constant formulas from overlapping literal surfaces.

### 10.3 Formula

A bare formula starts with `=`.

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

All formulas in Ream core MUST use the Ream formula profile:

- direct cell and range coordinates MUST use R1C1 notation
- comma is the argument separator
- period is the decimal point inside formulas
- function names use the English spellings of the target spreadsheet engine
- sheet names are single-quoted when needed
- formulas MAY additionally reference Ream defined names and Ream tables as described below

A conforming parser MUST preserve formula text byte-for-byte after the leading `=` for bare formulas.

A conforming exporter from a spreadsheet SHOULD normalize formulas into the Ream formula profile.

### 10.4 Formula bodies in addressed entries

In addressed entries, formulas omit the leading `=`. The cell formula stored by the parser is the same formula text with an implicit leading `=` prepended.

Examples:

```text
B=RC[-1]*1.08
B:M=R[-1]C*0.6
D=SUM(Sales[Revenue])
E=tax_rate*R4C
```

A conforming parser MUST treat an addressed RHS as a formula body when, after the literal parses in Section 10.2 fail, at least one of the following is true:

- the RHS contains an R1C1 reference
- the RHS contains `(` or `)` or `,`
- the RHS contains `!`
- the RHS contains `[` or `]`
- the RHS contains one or more operator characters among `+ - * / ^ & < > =`
- the RHS is a bare identifier that resolves to a defined name or table identifier in scope
- the RHS is a sheet-qualified identifier that resolves to a defined name

Otherwise the RHS is a raw string.

If a literal string would otherwise be parsed as a formula body, it MUST be quoted.

Examples:

```text
B=Jan
B="A-B"
B=tax_rate
B="tax_rate"
B=Sales[Revenue]
B="Sales[Revenue]"
```

Interpretation depends on scope:

- `B=Jan` is the raw string `Jan`, unless `Jan` is a defined name or table identifier in scope
- `B="A-B"` is the string `A-B`
- `B=tax_rate` is a formula if `tax_rate` resolves as a defined name in scope; otherwise it is the raw string `tax_rate`
- `B="tax_rate"` is always the string `tax_rate`
- `B=Sales[Revenue]` is a formula
- `B="Sales[Revenue]"` is a string

### 10.5 Defined names in formulas

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

### 10.6 Structured table references in formulas

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

### 10.7 Number

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

### 10.8 Date

A date literal is a calendar date in canonical ISO form:

```text
YYYY-MM-DD
```

Examples:

```text
2025-01-31
1999-12-31
```

A conforming parser MUST reject impossible calendar dates.

Canonical output MUST use four-digit year, two-digit month, and two-digit day.

If the source spreadsheet cell is unambiguously temporal and date-like, an exporter SHOULD emit a date literal rather than a raw spreadsheet serial number.

A string that happens to look like a date MUST be quoted to remain a string.

### 10.9 Time

A time literal is a time of day in canonical form:

```text
hh:mm
hh:mm:ss
hh:mm:ss.fffffffff
```

Hours MUST be `00` through `23`.

Examples:

```text
09:30
14:05:07
14:05:07.25
```

Canonical output MUST use two-digit hour and minute. Seconds MAY be omitted when zero. Fractional seconds, when present, MUST omit trailing zeros.

If the source spreadsheet cell is unambiguously temporal and time-like, an exporter SHOULD emit a time literal rather than a raw spreadsheet serial number.

A string that happens to look like a time MUST be quoted to remain a string.

### 10.10 Datetime

A datetime literal is a local, timezone-free datetime in canonical ISO form:

```text
YYYY-MM-DDThh:mm
YYYY-MM-DDThh:mm:ss
YYYY-MM-DDThh:mm:ss.fffffffff
```

Examples:

```text
2025-01-31T09:30
2025-01-31T14:05:07
```

Canonical output MUST use the literal `T` separator.

If the source spreadsheet cell is unambiguously temporal and datetime-like, an exporter SHOULD emit a datetime literal rather than a raw spreadsheet serial number.

A string that happens to look like a datetime MUST be quoted to remain a string.

### 10.11 Display annotations

A number, date, time, or datetime MAY carry a display annotation:

```text
<base-literal>@"<display-text>"
```

Examples:

```text
0.25@"25%"
1234.5@"$1,234.50"
1000000@"1.0M"
2025-01-31@"Jan 2025"
2025-01-31T09:30@"Jan 31, 2025 9:30 AM"
```

The base literal is the underlying cell value.

The quoted display text is the intended human-readable rendering.

A display annotation is not a cached formula result. It is valid only on non-formula numbers, dates, times, and datetimes in Ream core.

Canonical output SHOULD include a display annotation when the human-readable rendering materially differs from the base literal and the exporter has a trustworthy plain-text display surface for the source cell.

Exact spreadsheet number-format codes remain outside Ream core. If those must be preserved, an extension MUST carry them.

### 10.12 Boolean

Accepted values are `TRUE` and `FALSE`.

Parsers MAY accept case-insensitive input. Canonical output MUST use uppercase.

### 10.13 Error

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

### 10.14 Quoted string

Quoted strings are enclosed in double quotes.

They are required when the string:

- contains `|`
- contains a physical line break
- contains a double quote
- contains leading or trailing whitespace
- is empty
- starts with `=`
- starts with `@`
- would otherwise parse as a boolean, error, number, date, time, or datetime
- would otherwise match the addressed-entry prefix pattern `<col>=` or `<col1>:<col2>=`
- would otherwise be parsed as an addressed formula body in its context

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
"2025-01-31"
"line 1\nline 2"
```

### 10.15 Raw string

A raw string is any unquoted scalar that is not parsed as another scalar type.

Examples:

```text
Revenue
Jan
Gross Profit
usd0
```

Raw strings MUST NOT contain `|` or physical line breaks.

## 11. Record tokenization and quoting

Record tokenization is quote-aware.

A `|` is an entry separator only when it appears outside a double-quoted substring.

This rule applies uniformly to:

- quoted string cells
- formula text that contains string literals
- addressed formulas that contain string literals
- display annotations

Examples that MUST remain a single entry each:

```text
9 | "A|B|C" |
10 | =IF(RC1="A|B",1,0) |
11 | B=IF(RC1="A|B",1,0) |
12 | B=0.25@"25% | promo" |
```

Within a double-quoted substring, `""` is a literal quote and does not end the substring.

Tokenization does not interpret backslash escapes. Backslash escapes are interpreted only when decoding quoted string values and display-annotation display text.

A conforming tokenizer MAY be implemented by scanning a record line left to right and splitting only on `|` characters that occur while not inside a double-quoted substring.

## 12. Entry parsing algorithm

After record tokenization, each entry is parsed as follows:

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

- The first line MUST be `#!REAM 11`.
- Workbook-scoped `#!NAME` lines, if present, MUST appear before the first `#!SHEET`.
- Workbook-scoped `#!NAME` lines MUST be sorted by identifier in ascending byte order.
- Sheets MUST appear in workbook order.
- Each sheet MUST begin with `#!SHEET <sheet-name>`.
- `#!HEADERS`, sheet-scoped `#!NAME`, and `#!TABLE` lines, if present, MUST appear before record lines.
- Within a sheet block, sheet-scoped `#!NAME` lines MUST appear before `#!TABLE` lines.
- Record lines MUST appear in canonical record order as defined below.
- `#!FMT`, `#!TAG`, and `#!NOTE` lines, if present, MUST appear after record lines.
- Blank lines and comments MUST NOT appear in canonical output.

### 13.2 Directive spelling

Canonical output MUST use uppercase directive names exactly as defined in this specification.

For `#!SHEET`, canonical output MUST use a bare sheet name when the name is representable as a bare token. Otherwise it MUST use a quoted string.

For `#!NAME`, canonical output MUST use a bare identifier. Workbook-scoped `#!NAME` targets MUST be sheet-qualified. Sheet-qualified targets MUST use the same sheet-name quoting rules as formulas.

For `#!TABLE`, canonical output MUST omit `TOTALS` when the table has no totals row and MUST emit `TOTALS` when the table has a totals row.

For `#!FMT` and `#!TAG`, canonical output MUST use the bare token form when possible and a quoted string otherwise.

Repeated `#!HEADERS` directives MUST be normalized by sorting their row spans, merging overlaps and direct adjacencies, and emitting the merged spans in ascending order.

### 13.3 Scalar canonicalization

Canonical cell scalar text is defined as follows:

- formula: exact formula text including the leading `=`
- quoted string: quoted with the escape rules of Section 10.14
- boolean: `TRUE` or `FALSE`
- error: exact canonical spelling from Section 10.13
- number: canonical form from Section 10.7
- date: canonical form from Section 10.8
- time: canonical form from Section 10.9
- datetime: canonical form from Section 10.10
- annotated literal: canonical base literal immediately followed by `@` and a canonical quoted display string
- raw string: the raw string text when raw-string form is allowed; otherwise canonical quoted-string form

For canonical purposes, two cells are identical only when they have the same scalar type and the same canonical cell scalar text.

### 13.4 Horizontal segment construction

Within each worksheet row, a canonical writer MUST partition the explicit cells of that row into maximal contiguous horizontal segments of identical cells.

A segment is the tuple:

```text
(row, start-column, end-column, canonical-cell)
```

The segment is maximal when extending it one cell left or right would either leave the row, hit a blank cell, or hit a non-identical cell.

### 13.5 Vertical merge

A canonical writer MUST then vertically merge adjacent horizontal segments into maximal rectangles when all of the following are true:

- the segments are on consecutive worksheet rows
- they have the same start column
- they have the same end column
- they have identical canonical cells

A rectangle is therefore the tuple:

```text
(start-row, end-row, start-column, end-column, canonical-cell)
```

This merge is greedy and exact because the horizontal segments are already maximal and fixed. No alternative tiling is permitted in canonical form.

### 13.6 Record grouping

After vertical merge, a canonical writer MUST group rectangles by identical row span `(start-row, end-row)`.

Each such group becomes one canonical record line.

Within a record line, rectangles MUST be emitted in strictly increasing start-column order.

Record groups MUST be emitted in ascending lexicographic order of:

```text
(start-row, end-row, first-start-column)
```

where `first-start-column` is the smallest start column among the rectangles in that record group.

This makes canonical record order unique even when multiple record lines touch overlapping worksheet rows.

### 13.7 Entry emission

Within a canonical record line:

- if a rectangle has width `1` and its start column equals the current cursor, emit it as a bare scalar
- if a rectangle has width `1` and starts after the cursor, emit it as `<col>=<rhs>`
- if a rectangle has width greater than `1`, emit it as `<col1>:<col2>=<rhs>`

If the rectangle spans exactly one row, emit the row prefix as the single row number.

If the rectangle group spans more than one row, emit the row prefix as `<row1>:<row2>`.

For formula cells:

- bare scalar form MUST include the leading `=`
- addressed form MUST omit the leading `=` and emit the formula body

For all non-formula cells, bare and addressed forms use the canonical scalar text directly.

Examples:

```text
12 | EBITDA | B:M=R4C-R10C |
12:20 | B:M=8500 |
24:36 | N=R[-1]C*1.08 |
40:43 | C=SMB | D=Upside |
```

### 13.8 Exact spacing

Canonical record spacing is exact and unique:

```text
12:20 | B:M=8500 | O=TRUE |
```

Canonical output MUST use:

- exactly one space after the record prefix
- exactly one space on each side of every `|`
- no alignment padding inside entries

Canonical directive lines MUST use exactly one ASCII space between the directive name and each argument.

### 13.9 Names, tables, and metadata order

In canonical output:

- workbook-scoped `#!NAME` lines MUST be sorted by identifier in ascending byte order
- sheet-scoped `#!NAME` lines MUST be sorted by identifier in ascending byte order
- `#!TABLE` lines MUST be sorted by identifier in ascending byte order
- `#!FMT`, `#!TAG`, and `#!NOTE` lines MUST be sorted by selector order, then by value text in ascending byte order

Selector order is defined by first normalizing each selector to the tuple `(r1, c1, r2, c2)` and then comparing those tuples lexicographically as integers.

Normalization rules:

- `B3` -> `(3, 2, 3, 2)`
- `B3:M13` -> `(3, 2, 13, 13)`
- `3:3` -> `(3, 0, 3, 0)`
- `3:5` -> `(3, 0, 5, 0)`
- `B:B` -> `(0, 2, 0, 2)`
- `B:E` -> `(0, 2, 0, 5)`

## 14. Parsing requirements

A conforming parser MUST reject:

- duplicate `#!SHEET` names in the same document
- duplicate workbook-scoped name identifiers case-insensitively
- duplicate table identifiers case-insensitively
- duplicate sheet-scoped name identifiers case-insensitively within one sheet
- any sheet-scoped name that case-insensitively collides with a workbook-scoped name or table identifier
- any workbook-scoped name that case-insensitively collides with a table identifier
- malformed record prefixes
- record prefixes whose end row precedes the start row
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
- duplicate cell assignments anywhere in the same sheet, whether produced within one record line or across multiple record lines
- backward jumps such as `B=` after the cursor has already moved past column `B` within one record body

A permissive parser MAY accept non-canonical input such as:

- comments
- blank lines
- lowercase column letters in selectors and addressed entries
- optional `$` markers in A1 selectors and addressed entries
- empty record entries
- unsorted metadata directives
- a bare table identifier as an alias for `Table[#Data]`
- implicit current-row structured references such as `[@Column]` inside table formulas
- space instead of `T` in datetime literals

A permissive parser SHOULD normalize accepted input through canonical serialization.

## 15. Name, table, and metadata semantics

The core directives have these semantics:

- `#!HEADERS` marks worksheet rows intended as headers for presentation.
- `#!NAME` binds an identifier to a target selector.
- `#!TABLE` declares a named table whose header row is the first row of the selector and whose optional totals row is the last row when `TOTALS` is present.
- `#!FMT` associates a selector with an opaque format token or text label such as `usd0`, `pct1`, or `"sales input"`.
- `#!TAG` associates a selector with an opaque semantic token or text label such as `input`, `calc`, or `"sales input"`.
- `#!NOTE` attaches text to a selector.

A table's column namespace is derived from the decoded string values of the header-row cells inside the table area.

A name target is a static selector, not an arbitrary formula. Ream core names therefore represent named ranges, named cells, named rows, or named columns, but not formula-defined names.

The core format does not prescribe how spreadsheet engines store these directives internally. Consumers SHOULD preserve them when possible.

## 16. Extensions

Ream core reserves the `#!X-` directive namespace for extensions.

Examples of likely extensions:

```text
#!X-DIM 1048576x16384
#!X-EVAL G2:M2 [1296,1399.68,1511.6544,...]
#!X-NAME-FORMULA tax_rate =R1C1*0.25
#!X-NUMFMT B2:M2 "$#,##0.00"
```

`#!X-DIM` could preserve exact worksheet extents.

`#!X-EVAL` could preserve cached formula results without mixing them into the row grammar.

`#!X-NAME-FORMULA` could preserve formula-defined names that are outside Ream core.

`#!X-NUMFMT` could preserve exact spreadsheet number-format codes when needed.

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

### 18.1 P&L with names, human-readable dates, and formatted literals

```text
#!REAM 11
#!NAME tax_rate 'Assumptions'!B2

#!SHEET Assumptions
2 | Tax Rate | 0.25@"25%" |

#!SHEET "P&L"
#!HEADERS 1:1
#!NAME revenue_inputs B2:M2

1 | B=2025-01-31@"Jan 2025" | 2025-02-28@"Feb 2025" | 2025-03-31@"Mar 2025" | 2025-04-30@"Apr 2025" | 2025-05-31@"May 2025" | 2025-06-30@"Jun 2025" | 2025-07-31@"Jul 2025" | 2025-08-31@"Aug 2025" | 2025-09-30@"Sep 2025" | 2025-10-31@"Oct 2025" | 2025-11-30@"Nov 2025" | 2025-12-31@"Dec 2025" |
2 | Revenue | 1000@"$1,000" | 1050@"$1,050" | 1100@"$1,100" | 1150@"$1,150" | 1200@"$1,200" | G:M=RC[-1]*1.08 |
3 | COGS | B:M=R[-1]C*0.6 |
4 | Gross Profit | B:M=R[-2]C-R[-1]C |
6 | Headcount | B:C=50 | D:M=52 |
7 | Avg Salary | B:M=8500@"$8,500" |
8 | Payroll | B:M=R[-2]C*R[-1]C |
9 | Rent | B:M=15000@"$15,000" |
10 | Total OpEx | B:M=R[-2]C+R[-1]C |
12 | Tax | B:M=R4C*tax_rate |
13 | Net Income | B:M=R4C-R10C-R[-1]C |

#!FMT 2:4 usd0
#!FMT 6:6 num0
#!FMT 7:13 usd0
#!TAG B2:F2 input
#!TAG G2:M2 calc
#!TAG B13:M13 output
```

### 18.2 Vertical repeated literal rectangle

```text
#!REAM 11
#!SHEET Assumptions
7:12 | B:M=8500@"$8,500" |
```

This fills the entire rectangle `B7:M12` with the same literal value and display text.

### 18.3 Vertical repeated formula rectangle

```text
#!REAM 11
#!SHEET Model
20:31 | G:M=R[-1]C*1.08 |
```

This fills every cell in `G20:M31` with the same formula text, evaluated relative to each cell's own location.

### 18.4 Mixed row-specific labels plus shared rectangular fill

```text
#!REAM 11
#!SHEET Revenue
12:19 | F:K=0 |
12 | C=Enterprise | D=Base |
16 | C=Enterprise | D=Upside |
24 | C="Mid-Market" | D=Base |
28 | C="Mid-Market" | D=Upside |
```

This is valid because the rectangle record and the row-specific label records assign disjoint cells.

### 18.5 Table formulas with current-row references

```text
#!REAM 11
#!SHEET Sales
#!TABLE Sales A10:D13

10 | Product | Qty | Price | Revenue |
11:13 | D=Sales[@[Qty]]*Sales[@[Price]] |
11 | A=A | B=10 | C=5 |
12 | A=B | B=8 | C=6 |
13 | A=C | B=12 | C=4 |
```

### 18.6 Table aggregation formula outside the table

```text
#!REAM 11
#!SHEET Sales
#!TABLE Sales A10:D13

10 | Product | Qty | Price | Revenue |
11 | A | 10 | 5 | 50 |
12 | B | 8 | 6 | 48 |
13 | C | 12 | 4 | 48 |
20 | Total Revenue | =SUM(Sales[Revenue]) |
```

### 18.7 Formula with a pipe character inside a string literal

```text
5 | B=IF(RC1="A|B",1,0) |
```

This record has one entry after tokenization.

### 18.8 Bare string that looks like a formula body

```text
7 | B="Sales[Revenue]" |
```

The quotes are required if the literal text should remain a string.

## 19. Outer syntax and tokenizer

ABNF is used for the outer line structure. Record entry splitting is defined algorithmically in Section 11.

```abnf
file            = *(blank / comment) ream-line nl
                  *(workbook-item nl / blank / comment)
                  1*(sheet-block / blank / comment)

workbook-item   = name-line / ext-line

sheet-block     = sheet-line nl
                  *(sheet-item nl / blank / comment)

sheet-item      = headers-line / name-line / table-line / fmt-line /
                  tag-line / note-line / record-line / ext-line

ream-line       = "#!REAM" SP "11"
sheet-line      = "#!SHEET" SP name
headers-line    = "#!HEADERS" SP row-sel
name-line       = "#!NAME" SP ident SP name-target
table-line      = "#!TABLE" SP ident SP rect-sel [SP "TOTALS"]
fmt-line        = "#!FMT" SP selector SP metadata-value
tag-line        = "#!TAG" SP selector SP metadata-value
note-line       = "#!NOTE" SP selector SP qstring
ext-line        = "#!X-" ident *(SP ext-token)

record-line     = row-prefix SP "|" record-body "|"
row-prefix      = uint / (uint ":" uint)
record-body     = *record-char

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
metadata-value  = token / qstring
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
record-char     = %x09 / %x20-7E / UTF8-nonascii

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

### 19.1 Record tokenizer pseudocode

```text
function split_record_body(record_body):
    entries = []
    buf = ""
    in_quotes = false
    i = 0

    while i < len(record_body):
        ch = record_body[i]

        if ch == '"':
            if in_quotes and i + 1 < len(record_body) and record_body[i + 1] == '"':
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

- Ream core intentionally omits used-range data. A sheet's explicit cell map is the whole core state.
- Cached formula results belong in an extension if needed.
- Workbook-scoped names appear before the first `#!SHEET`. Sheet-scoped names appear inside sheet blocks.
- A `#!TABLE` declaration is structural only. It does not carry table styling or filter state.
- Table column names come from header-row string cells. Preserve those strings exactly for canonical structured references.
- Canonical structured references should include an explicit table identifier, even for current-row references.
- Because row spans are now first-class, implementations MUST validate duplicate cell assignments across the full sheet, not just within one worksheet row.
- Canonical compaction is two-dimensional: horizontal segmentation first, vertical merge second.
- Addressed formulas use a single `=` separator and omit the leading `=` in the RHS. Literal parsing happens first, then formula-body detection.
- Ream uses A1 selectors outside formulas and R1C1 coordinates inside formulas. That split is intentional: A1 is easier to read in metadata and sparse addressing, while R1C1 preserves copy-fill semantics inside formulas.
- A permissive importer MAY accept the legacy header `#!REAM 10` and earlier experimental headers as aliases for older drafts, but those spellings are not part of Ream 11.
