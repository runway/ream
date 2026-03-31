"""Run ream-xlsx on each demo file, print output, and save to demo/results/.

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
RESULTS_DIR = DEMO_DIR / "results"


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

    RESULTS_DIR.mkdir(exist_ok=True)

    if args.file:
        files = [Path(args.file).resolve()]
    else:
        files = sorted(DEMO_DIR.glob("*.xlsx"))
        # Also include any xlsx files in subdirectories (e.g. demo/private/)
        for subdir in sorted(DEMO_DIR.iterdir()):
            if subdir.is_dir() and subdir.name not in ("results", "__pycache__"):
                files.extend(sorted(subdir.glob("*.xlsx")))

    flags = []
    if args.collapse_rows:
        flags.append("--collapse-rows")
    if args.force_col_selectors:
        flags.append("--force-col-selectors")
    if args.max_rows != 500:
        flags.append(f"--max-rows {args.max_rows}")
    flags_str = " ".join(flags)

    for xlsx_path in files:
        output = xlsx_to_ream(str(xlsx_path), options)

        # Print to stdout
        print(f"{'=' * 60}")
        print(f"  {xlsx_path.name}")
        print(f"{'=' * 60}")
        print(output)
        print()

        # Write to results/
        md_name = xlsx_path.stem + ".md"
        md_path = RESULTS_DIR / md_name

        # Build relative path from demo dir for display
        try:
            rel_path = xlsx_path.relative_to(DEMO_DIR)
        except ValueError:
            rel_path = xlsx_path

        cmd = f"ream-xlsx {rel_path}"
        if flags_str:
            cmd += f" {flags_str}"

        md_content = f"# {xlsx_path.stem}\n\nSource: `{rel_path}`\n\n"
        md_content += f"```bash\n{cmd}\n```\n\n"
        md_content += f"```\n{output}\n```\n"

        md_path.write_text(md_content)
        print(f"  -> saved to results/{md_name}")
        print()

    print(f"Results written to {RESULTS_DIR.relative_to(DEMO_DIR)}/")


if __name__ == "__main__":
    main()
