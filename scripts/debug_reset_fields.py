import os
import time

from helpers.env import load_env

load_env()

from cloakbrowser.config import get_default_stealth_args
from cloakbrowser.download import ensure_binary
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from pages.reset_password import ResetPasswordPage

base_url = os.environ["BASE_TEST_URL"].rstrip("/")
opts = Options()
opts.binary_location = ensure_binary()
for a in get_default_stealth_args():
    opts.add_argument(a)
opts.add_argument("--window-size=1280,720")
drv = webdriver.Chrome(service=Service(), options=opts)
page = ResetPasswordPage.open(drv, base_url)
page.identifier.submit_email("aaaa+clerk_test@linky.now")
page.password.wait_until_visible()
page.password.click_forgot_password()
page.forgot.click_reset_your_password()
page.otp.wait_until_visible()
page.otp.fill_otp("424242")
page.reset.wait_until_visible()
page.reset.fill_new_password("aaaaaaaaaa")
page.reset.fill_confirm_password("aaaaaaaaaa")
print("before submit:", drv.execute_script(
    "const b=[...document.querySelectorAll('button')].find(x=>/reset password/i.test(x.textContent||''));"
    "return b?{disabled:b.disabled}:null"))
page.reset.submit()
time.sleep(3)
print("after submit url:", drv.current_url)
print("body:", drv.execute_script("return document.body.innerText.slice(0,1200)").encode("ascii","replace").decode())
vals = drv.execute_script(
    "return [...document.querySelectorAll('input')].map(el => "
    "({name: el.name, id: el.id, value: el.value, type: el.type, "
    "visible: !!(el.offsetWidth || el.offsetHeight)}))"
)
print("inputs:", vals)
btn = drv.execute_script(
    "const b = [...document.querySelectorAll('button')]"
    ".find(x => /reset password/i.test(x.textContent || ''));"
    "return b ? {disabled: b.disabled, text: b.textContent} : null"
)
print("btn:", btn)
drv.quit()
