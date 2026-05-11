from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from .report import write_report
from .sources import fetch_replicate_models, fetch_toolify_new, merge_results
from .storage import SeenStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Watch Replicate and Toolify for newly discovered AI models/tools."
    )
    parser.add_argument(
        "--db",
        default="data/seen.sqlite",
        help="SQLite state database path. Default: data/seen.sqlite",
    )
    parser.add_argument(
        "--output",
        default="reports/latest.md",
        help="Report output path. Default: reports/latest.md",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Report format. Default: markdown",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Record current items as already seen and do not report them as new.",
    )
    parser.add_argument(
        "--replicate-limit",
        type=int,
        default=20,
        help="How many recent Replicate models to inspect. Default: 20",
    )
    parser.add_argument(
        "--toolify-limit",
        type=int,
        default=30,
        help="How many Toolify tools to inspect. Default: 30",
    )
    parser.add_argument(
        "--skip-replicate",
        action="store_true",
        help="Skip Replicate.",
    )
    parser.add_argument(
        "--skip-toolify",
        action="store_true",
        help="Skip Toolify.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not use Playwright as Toolify fallback.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path.cwd()
    load_dotenv(root / ".env")

    store = SeenStore(root / args.db)
    run_id = store.begin_run()
    status = "ok"
    message = ""

    try:
        results = []
        if not args.skip_replicate:
            results.append(fetch_replicate_models(limit=args.replicate_limit))
        if not args.skip_toolify:
            results.append(
                fetch_toolify_new(
                    limit=args.toolify_limit,
                    use_browser=not args.no_browser,
                )
            )

        merged = merge_results(results)
        new_items = []
        for item in merged.items:
            inserted = store.insert_if_new(item)
            if inserted and not args.bootstrap:
                new_items.append(item)

        if args.bootstrap:
            message = f"Bootstrapped {len(merged.items)} current items."
        else:
            message = f"Found {len(new_items)} new items."

        report_body = write_report(
            items=new_items,
            warnings=merged.warnings,
            output_path=root / args.output,
            report_format=args.format,
        )
        print(report_body, end="")
        return 0
    except Exception as exc:
        status = "error"
        message = str(exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        store.finish_run(run_id, status=status, message=message)
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())

