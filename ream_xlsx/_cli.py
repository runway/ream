"""CLI entry point for ream-xlsx."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from ream_xlsx import ReamOptions, xlsx_to_ream
from ream_xlsx._exceptions import ReamError


@click.command()
@click.version_option(package_name="ream-xlsx")
@click.argument("input_file")
@click.option("-o", "--output", "output_file", default=None, help="Write output to FILE instead of stdout.")
@click.option("--max-rows", "max_rows", default=500, show_default=True, help="Maximum rows per sheet.")
@click.option("--collapse-rows", "collapse_rows", is_flag=True, default=False, help="Collapse identical adjacent rows.")
@click.option(
    "--force-col-selectors",
    "force_col_selectors",
    is_flag=True,
    default=False,
    help="Force column selectors in output.",
)
def main(
    input_file: str,
    output_file: str | None,
    max_rows: int,
    collapse_rows: bool,
    force_col_selectors: bool,
) -> None:
    """Convert an XLSX workbook to REAM text format."""
    options = ReamOptions(
        max_rows_per_sheet=max_rows,
        collapse_rows=collapse_rows,
        force_col_selectors=force_col_selectors,
    )
    try:
        result = xlsx_to_ream(input_file, options)
    except ReamError as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    if output_file is not None:
        Path(output_file).write_text(result + "\n", encoding="utf-8")
    else:
        click.echo(result)
