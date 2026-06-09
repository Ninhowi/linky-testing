# Linky Auth E2E (pytest + Selenium + CloakBrowser)

Standalone Python E2E suite for Linky **sign-up**, **sign-in**, **reset-password**, and **user profile** flows. Test cases are driven by Excel rows in `test_data/data.xlsx`.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.14 (see `.python-version`)
- [Allure CLI](https://allurereport.org/docs/install/) (optional, for HTML reports)
- A running Linky app and `.env` with `BASE_TEST_URL`

## Setup

```bash
uv sync
cp .env.example .env   # set BASE_TEST_URL to your app URL
uv run ensure-cloak    # download / verify CloakBrowser Chromium + ChromeDriver (~200MB first run)
```

`ensure-cloak` calls `cloakbrowser.ensure_binary()` and resolves a matching ChromeDriver via Selenium Manager. Run it before the first test run or on CI.

## Run tests

The `test` script wraps pytest with `-s -v` and writes Allure results to `allure-results/`.

```bash
uv run test tests/                              # all auth tests
uv run test tests/test_1_sign_up.py             # sign-up only
uv run test tests/test_2_sign_in.py             # sign-in only
uv run test tests/test_3_reset_password.py      # reset-password only
uv run test tests/test_4_user_profile.py      # user profile only
uv run test tests -m sign_in                    # by marker
uv run test tests -n auto                       # parallel (xdist)
```

Run with a visible browser:

```bash
HEADED=1 uv run test tests/test_2_sign_in.py
```

Or set `HEADED=1` in `.env`.

## Allure reports

On Windows, install the Allure CLI from an elevated PowerShell at the project root:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\install-allure.ps1
```

Then run tests and open reports:

```bash
uv run test tests/                  # produces allure-results/
uv run allure-report serve          # live report (default)
uv run allure-report generate       # static HTML in allure-report/
uv run allure-report open           # open generated report
```

## Environment

| Variable | Description |
|----------|-------------|
| `BASE_TEST_URL` | App under test (required; tests skip if unset) |
| `HEADED` | `1` / `true` / `yes` for headed browser (default: headless) |
| `IGNORE_HTTPS_ERRORS` | `1` / `true` / `yes` to pass `--ignore-certificate-errors` |
| `USER_EMAIL` | Login email for profile tests |
| `USER_PASSWORD` | Login password for profile tests |
| `USER_OTP` | OTP code when the test account uses 2FA |

Variables are loaded from `.env` and optional `.env.e2e` at the project root. Existing process env vars are not overwritten.

## Test data (Excel)

File: `test_data/data.xlsx`

| Sheet | Test file |
|-------|-----------|
| `sign_up` | `tests/test_1_sign_up.py` |
| `login` | `tests/test_2_sign_in.py` |
| `reset_password` | `tests/test_3_reset_password.py` |
| `profile` | `tests/test_4_user_profile.py` |

Format per sheet:

- Row 1: column headers (`email`, `password`, `otp`, `message`, …)
- Row 2+: one test case per row until the last non-empty row

Each row drives inputs through the Clerk auth UI and asserts the expected `message` (field-level and on-screen). Sign-up emails matching `name+clerk_test@domain` are auto-uniquified for successful registration cases.

## Project layout

```
linky-testing-final/
  helpers/           # env, Excel loading, auth helpers, test runner, Allure
  pages/             # page objects (sign-up, sign-in, reset-password, Clerk forms)
  tests/             # parametrized pytest modules per auth flow
  test_data/
    data.xlsx        # case matrix
  scripts/           # ad-hoc debug helpers
```

## Clerk test accounts

For Clerk test mode (when using `+clerk_test` emails):

| | Value |
|---|--------|
| Email pattern | `{name}+clerk_test@{domain}` |
| OTP | `424242` |
