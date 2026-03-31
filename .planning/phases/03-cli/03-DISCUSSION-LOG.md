# Phase 3: CLI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 03-cli
**Areas discussed:** Flag design, Error output formatting, Output behavior, Version & help

---

## Flag Design

### Flag naming
| Option | Description | Selected |
|--------|-------------|----------|
| --max-rows | Short and intuitive. Maps to ReamOptions.max_rows_per_sheet internally. | ✓ |
| --max-rows-per-sheet | Matches the ReamOptions field name exactly. More verbose but self-documenting. | |

**User's choice:** --max-rows
**Notes:** None

### Boolean flag style
| Option | Description | Selected |
|--------|-------------|----------|
| --collapse-rows only | Simple. Default is off, passing the flag turns it on. | ✓ |
| --collapse-rows / --no-collapse-rows | Click's flag_value pattern. More explicit but unnecessary. | |

**User's choice:** --collapse-rows only
**Notes:** None

### Short flag aliases
| Option | Description | Selected |
|--------|-------------|----------|
| -o for output only | -o FILE is a well-known convention. Other flags long-only. | ✓ |
| Short flags for all | -o, -m, -c, -f for all flags. | |
| No short flags | Only long flags. | |

**User's choice:** -o for output only
**Notes:** None

---

## Error Output Formatting

### Error format
| Option | Description | Selected |
|--------|-------------|----------|
| Simple prefix | "error: file not found: path.xlsx" -- lowercase, no traceback. | ✓ |
| Click-style | "Error: ..." with Click's built-in formatting. | |
| Bare message | Just the error message, no prefix. | |

**User's choice:** Simple prefix
**Notes:** None

### Error hints
| Option | Description | Selected |
|--------|-------------|----------|
| No hints | Keep errors clean for scripts. | ✓ |
| Hint on usage errors only | "Try 'ream-xlsx --help'" for flag errors. | |

**User's choice:** No hints
**Notes:** None

---

## Output Behavior

### Trailing newline
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, trailing newline | Standard POSIX convention, click.echo() default. | ✓ |
| No trailing newline | Raw output exactly as function returns. | |

**User's choice:** Yes, trailing newline
**Notes:** None

### Multi-file input
| Option | Description | Selected |
|--------|-------------|----------|
| Single file only | Matches CLI-01 spec. Simple, no ambiguity. | ✓ |
| Multiple files now | ream-xlsx a.xlsx b.xlsx with separation. | |

**User's choice:** Single file only
**Notes:** None

---

## Version & Help

### --version flag
| Option | Description | Selected |
|--------|-------------|----------|
| Include now | Trivial with Click's @click.version_option + importlib.metadata. | ✓ |
| Defer to v2 | OPT-02 lists this as v2. | |

**User's choice:** Include now
**Notes:** None

### --help style
| Option | Description | Selected |
|--------|-------------|----------|
| Click defaults | Auto-generated from docstrings and option help text. | ✓ |
| Custom header | Brief description at top, Click-generated flags below. | |

**User's choice:** Click defaults
**Notes:** None

---

## Claude's Discretion

- Internal structure of `_cli.py`
- `__main__.py` implementation
- Click test strategy
- Error message exact wording

## Deferred Ideas

- Multi-file input support (v2)
- `--sheet` flag for single-sheet extraction (OPT-02)
