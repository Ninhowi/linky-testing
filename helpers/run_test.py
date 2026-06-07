"""Run pytest with default -s -v and Allure reporting."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from helpers.env import load_env

_ALLURE_DIR = Path("allure-results")
_DEFAULT_OPTS = (
    "-s",
    "-v",
    "--clean-alluredir",
    f"--alluredir={_ALLURE_DIR.as_posix()}",
)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: uv run test <pytest-args>", file=sys.stderr)
        print("Example: uv run test tests/test_sign_in.py", file=sys.stderr)
        print("Example: uv run test tests -k sign_in -m sign_in", file=sys.stderr)
        raise SystemExit(2)

    load_env()
    _ALLURE_DIR.mkdir(parents=True, exist_ok=True)
    code = pytest.main([*args, *_DEFAULT_OPTS])
    raise SystemExit(code)


if __name__ == "__main__":
    main()
