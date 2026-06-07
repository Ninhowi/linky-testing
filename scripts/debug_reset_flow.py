"""One-off debug: reset-password flow through OTP."""

from __future__ import annotations

import os
import time

from cloakbrowser.config import get_default_stealth_args
from cloakbrowser.download import ensure_binary
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from helpers.env import load_env
from pages.reset_password import ResetPasswordPage

load_env()
base_url = os.environ["BASE_TEST_URL"].rstrip("/")

binary_path = ensure_binary()
options = Options()
options.binary_location = binary_path
for arg in get_default_stealth_args():
    options.add_argument(arg)
options.add_argument("--window-size=1280,720")

drv = webdriver.Chrome(service=Service(), options=options)
drv.set_window_size(1280, 720)
try:
    page = ResetPasswordPage.open(drv, base_url)
    page.identifier.submit_email("aaaa+clerk_test@linky.now")
    print("after email:", drv.current_url)
    page.password.wait_until_visible()
    page.password.click_forgot_password()
    page.forgot.click_reset_your_password()
    print("after forgot:", drv.current_url)
    page.otp.wait_until_visible()
    print("otp visible:", drv.current_url)
    otp_el = page.otp.otp_input()
    print("otp element attrs:", {
        "name": otp_el.get_attribute("name"),
        "placeholder": otp_el.get_attribute("placeholder"),
        "aria-label": otp_el.get_attribute("aria-label"),
        "autocomplete": otp_el.get_attribute("autocomplete"),
    })
    page.otp.fill_otp("424242")
    time.sleep(2)
    print("after otp:", drv.current_url)
    try:
        page.otp.wait_until_hidden(timeout=15)
        print("otp hidden")
    except Exception as exc:
        print("otp still visible:", exc)
    info = drv.execute_script("""
        return {
            url: location.href,
            inputs: [...document.querySelectorAll('input')].map(el => ({
                name: el.name, type: el.type, id: el.id,
                placeholder: el.placeholder, autocomplete: el.autocomplete,
                inputmode: el.inputMode, ariaLabel: el.getAttribute('aria-label'),
                className: el.className,
                visible: !!(el.offsetWidth || el.offsetHeight)
            })),
            body: document.body.innerText.slice(0, 800)
        };
    """)
    print("page info:", info)
    try:
        page.reset.wait_until_visible(timeout=5)
        print("reset form visible")
    except Exception as exc:
        print("reset form missing:", exc)
finally:
    drv.quit()
