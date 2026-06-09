"""Download and verify CloakBrowser Chromium and matching ChromeDriver for Selenium.

Tải và xác minh CloakBrowser Chromium cùng ChromeDriver tương thích cho Selenium.
"""

from __future__ import annotations

import argparse
import logging
import sys


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
        force=True,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def install_chromedriver(binary_path: str) -> str:
    """Resolve ChromeDriver matched to the Cloak Chromium binary via Selenium Manager.

    Tìm ChromeDriver khớp với binary Cloak Chromium qua Selenium Manager.
    """
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.driver_finder import DriverFinder

    options = Options()
    options.binary_location = binary_path
    service = Service()
    finder = DriverFinder(service, options)
    return finder.get_driver_path()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Download / verify CloakBrowser Chromium and ChromeDriver for Selenium.\n"
            "Tải / xác minh CloakBrowser Chromium và ChromeDriver cho Selenium."
        ),
    )
    parser.add_argument(
        "--skip-chromedriver",
        action="store_true",
        help=(
            "Only ensure the CloakBrowser Chromium binary (skip ChromeDriver). "
            "Chỉ đảm bảo binary CloakBrowser Chromium (bỏ qua ChromeDriver)."
        ),
    )
    args = parser.parse_args(argv)

    _setup_logging()

    from cloakbrowser.download import binary_info, ensure_binary

    print("Downloading / verifying CloakBrowser Chromium binary...")
    binary_path = ensure_binary()
    print(f"CloakBrowser binary ready: {binary_path}")

    info = binary_info()
    print(f"  version: {info['version']}")
    print(f"  platform: {info['platform']}")

    if not args.skip_chromedriver:
        print("Installing / verifying ChromeDriver (matched to Cloak Chromium)...")
        driver_path = install_chromedriver(binary_path)
        print(f"ChromeDriver ready: {driver_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ensure-cloak failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
