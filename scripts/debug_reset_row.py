"""Debug failing reset-password rows."""

from __future__ import annotations

import os
import sys

from cloakbrowser.config import get_default_stealth_args
from cloakbrowser.download import ensure_binary
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from helpers.auth_excel import password_text, reset_password_should_submit
from helpers.env import load_env
from helpers.load_excel import load_excel
from pages.reset_password import ResetPasswordPage
from tests.test_reset_password import _run_reset_password_flow

load_env()
base_url = os.environ["BASE_TEST_URL"].rstrip("/")
row_index = int(sys.argv[1]) if len(sys.argv) > 1 else 6
case = load_excel("test_data/data.xlsx")["reset_password"][row_index]

binary_path = ensure_binary()
options = Options()
options.binary_location = binary_path
for arg in get_default_stealth_args():
    options.add_argument(arg)
options.add_argument("--window-size=1280,720")

drv = webdriver.Chrome(service=Service(), options=options)
try:
    page = ResetPasswordPage.open(drv, base_url)
    _run_reset_password_flow(page, case)
    info = drv.execute_script("""
        const btn = [...document.querySelectorAll('button')].find(b =>
            /reset password/i.test(b.textContent || ''));
        return {
            url: location.href,
            btnText: btn?.textContent?.trim(),
            btnDisabled: btn?.disabled,
            errors: [...document.querySelectorAll('[id^="error-"], [data-testid="form-feedback-error"]')]
                .map(el => el.textContent?.trim()).filter(Boolean),
            feedback: [...document.querySelectorAll('[id*="feedback"], [class*="feedback"]')]
                .map(el => el.textContent?.trim()).filter(Boolean).slice(0, 5),
            body: document.body.innerText.slice(0, 1500),
        };
    """)
    print("info:", {k: (v.encode("ascii", "replace").decode() if isinstance(v, str) else v) for k, v in info.items()})
finally:
    drv.quit()
