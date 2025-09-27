from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .scaffold import create_scaffold


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="redbot-orm",
        description="Utilities for managing redbot-orm powered cogs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="Create Piccolo scaffolding for a cog.",
    )
    scaffold_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Directory to populate (defaults to current working directory).",
    )
    scaffold_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files when present.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "scaffold":
        target = Path(args.target)
        created_files = create_scaffold(target, overwrite=args.overwrite)
        if created_files:
            for file_path in created_files:
                print(f"Created {file_path.resolve()}")
        else:
            print("All scaffold files already exist. Use --overwrite to recreate them.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover - exercised via console script
    sys.exit(main())
