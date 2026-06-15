# Linky Auth E2E (pytest + Selenium + CloakBrowser)

Standalone Python E2E suite for Linky **sign-up**, **sign-in**, **reset-password**, **user profile**, and **`/call` video chat** flows. Auth and profile cases are driven by Excel rows in `test_data/data.xlsx`; call page tests are scenario-based.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.14 (see `.python-version`)
- [Allure CLI](https://allurereport.org/docs/install/) (optional, for HTML reports)
- A running Linky app and `.env` with `BASE_TEST_URL`
- For `/call` tests: Go API, Redis, Clerk test accounts, Cloudflare Realtime credentials, and fake media Chrome flags (configured in `tests/conftest.py`)

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
uv run test tests/test_5_call_page.py         # /call page (serial — do not use -n auto)
uv run test tests/test_5_call_page.py -m call_smoke
uv run test tests -m sign_in                    # by marker
uv run test tests -n auto                       # parallel (xdist; not for call tests)
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
| `USER_EMAIL` | Login email for profile and call tests |
| `USER_PASSWORD` | Login password for profile and call tests |
| `USER_OTP` | OTP code when the test account uses 2FA |
| `USER2_EMAIL` | Second Clerk account for two-user call integration tests |
| `USER2_PASSWORD` | Password for `USER2_EMAIL` |
| `USER2_OTP` | Optional OTP for `USER2_EMAIL` |

Profile and call tests sign in through the Clerk UI using `USER_EMAIL` / `USER_PASSWORD` (and optional `USER_OTP`). Integration call tests also require `USER2_*` credentials for a second browser session.

Variables are loaded from `.env` and optional `.env.e2e` at the project root. Existing process env vars are not overwritten.

## Test data (Excel)

File: `test_data/data.xlsx`

| Sheet | Test file |
|-------|-----------|
| `sign_up` | `tests/test_1_sign_up.py` |
| `login` | `tests/test_2_sign_in.py` |
| `reset_password` | `tests/test_3_reset_password.py` |
| `profile` | `tests/test_4_user_profile.py` |
| `call_chat` | `tests/test_6_call_in_call_chat.py` |

Call page tests in `tests/test_5_call_page.py` follow the Linky `docs/e2e/call-page.md` spec (smoke + integration core). They are **not** Excel-driven.

In-call chat tests (`test_6`) use sheet **`call_chat`** when present; column reference: [`test_data/call_chat.md`](test_data/call_chat.md).

Format per sheet:

- Row 1: column headers (`email`, `password`, `otp`, `message`, …)
- Row 2+: one test case per row until the last non-empty row

Each row drives inputs through the Clerk auth UI and asserts the expected `message` (field-level and on-screen). Sign-up emails matching `name+clerk_test@domain` are auto-uniquified for successful registration cases.

## Project layout

```
linky-testing-final/
  helpers/
    auth/            # Clerk auth flows, session login, HTML5 validation
    browser/         # Selenium locators, waits, viewport, E2E key injection
    call/            # matched-call setup, in-call chat excel/flow/validation
    excel/           # workbook loading, shared cell parsing
    profile/         # profile sheet parsing and save assertions
    runtime/         # env loading, test runner, Allure, CloakBrowser setup
  pages/             # page objects (sign-up, sign-in, reset-password, video chat, Clerk forms)
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
