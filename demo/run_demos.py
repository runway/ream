"""Run ream-xlsx on each demo file and print the REAM output.

Usage:
    python demo/run_demos.py
    python demo/run_demos.py --collapse-rows
    python demo/run_demos.py --force-col-selectors
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ream_xlsx import ReamOptions, xlsx_to_ream

DEMO_DIR = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ream-xlsx demos")
    parser.add_argument("--collapse-rows", action="store_true", help="Enable row collapsing")
    parser.add_argument("--force-col-selectors", action="store_true", help="Force column selectors")
    parser.add_argument("--max-rows", type=int, default=500, help="Max rows per sheet")
    parser.add_argument("file", nargs="?", help="Run a single demo file instead of all")
    args = parser.parse_args()

    options = ReamOptions(
        max_rows_per_sheet=args.max_rows,
        collapse_rows=args.collapse_rows,
        force_col_selectors=args.force_col_selectors,
    )

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(DEMO_DIR.glob("*.xlsx"))

    for xlsx_path in files:
        print(f"{'=' * 60}")
        print(f"  {xlsx_path.name}")
        print(f"{'=' * 60}")
        output = xlsx_to_ream(str(xlsx_path), options)
        print(output)
        print()


if __name__ == "__main__":
    main()
