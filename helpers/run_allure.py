"""Generate or serve Allure reports from allure-results."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_DEFAULT_RESULTS = Path("allure-results")
_DEFAULT_OUTPUT = Path("allure-report")


def _find_allure() -> str:
    path = shutil.which("allure")
    if path:
        return path
    print(
        "Allure CLI not found on PATH.\n"
        "Install: https://allurereport.org/docs/install/\n"
        "  Windows (scoop): scoop install allure\n"
        "  macOS (brew):    brew install allure",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _run(allure: str, args: list[str]) -> int:
    try:
        return subprocess.call([allure, *args])
    except KeyboardInterrupt:
        return 130


def _ensure_results(results_dir: Path) -> None:
    if not results_dir.is_dir():
        print(f"Results directory not found: {results_dir}", file=sys.stderr)
        print("Run tests first: uv run test tests/", file=sys.stderr)
        raise SystemExit(1)
    if not any(results_dir.iterdir()):
        print(f"No Allure results in {results_dir}", file=sys.stderr)
        print("Run tests first: uv run test tests/", file=sys.stderr)
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Serve or generate Allure HTML report from allure-results.",
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=("serve", "generate", "open"),
        default="serve",
        help="serve: live report (default); generate: static HTML; open: open generated report",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=_DEFAULT_RESULTS,
        help=f"Allure results directory (default: {_DEFAULT_RESULTS})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help=f"Generated report directory (default: {_DEFAULT_OUTPUT})",
    )
    args = parser.parse_args(argv)

    allure = _find_allure()

    if args.action == "open":
        if not args.output.is_dir():
            print(f"Report not found: {args.output}", file=sys.stderr)
            print(f"Generate first: uv run allure-report generate", file=sys.stderr)
            return 1
        return _run(allure, ["open", str(args.output)])

    _ensure_results(args.results)

    if args.action == "serve":
        print(f"Serving Allure report from {args.results} (Ctrl+C to stop)...")
        return _run(allure, ["serve", str(args.results)])

    args.output.mkdir(parents=True, exist_ok=True)
    code = _run(
        allure,
        ["generate", str(args.results), "-o", str(args.output), "--clean"],
    )
    if code == 0:
        print(f"Report generated: {args.output.resolve()}")
        print(f"Open with: uv run allure-report open")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
