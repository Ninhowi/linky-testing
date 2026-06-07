"""Load environment variables from project .env files."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
_LOADED = False


def load_env(*, force: bool = False) -> None:
    """Load ``.env`` and optional ``.env.e2e`` from the project root.

    Existing process environment variables are not overwritten.
    """
    global _LOADED
    if _LOADED and not force:
        return

    load_dotenv(_ROOT / ".env")
    load_dotenv(_ROOT / ".env.e2e")
    _LOADED = True
