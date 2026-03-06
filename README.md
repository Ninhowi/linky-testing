# Linky Testing

Selenium-based UI tests for [Linky](https://www.linkynow.site): **sign-up** and **sign-in** flows, with support for both **automated** (Excel-driven) and **manual** (prompt-driven) runs.

---

## Project structure

```
linky-testing/
├── core/                      # Shared test flow logic
│   ├── signup_flow.py         # Sign-up flow (form, validation, OTP)
│   └── login_flow.py          # Sign-in flow (email → password → OTP)
├── utils/                     # Helpers
│   ├── chrome_driver.py       # Chrome WebDriver setup
│   ├── configure.py           # Headless, email generation, etc.
│   ├── generate_email.py     # Unique email for sign-up tests
│   └── safe_input.py         # React-friendly input clearing
├── automation_test/           # Automated tests (pytest + Excel)
│   ├── signup_test.py
│   └── login_test.py
├── manual_test/               # Manual tests (prompts for input)
│   ├── signup_manual_test.py
│   └── login_manual_test.py
├── testdata/                  # Excel test data (for automation)
│   ├── data_test_signup.xlsx
│   └── data_test_login.xlsx
├── reports/                   # Pytest HTML reports (generated)
├── run_tests.bat              # Run automation tests (pytest)
└── run_manual_test.bat        # Run manual test (signup or login)
```

- **Automation**: `automation_test/*.py` load data from Excel and call `core` flows.
- **Manual**: `manual_test/*.py` prompt for inputs, then use the same `core` flows.

---

## Setup

1. **Python 3.x** (3.10+ recommended).

2. **Virtual environment** (recommended):

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```powershell
   pip install selenium openpyxl pytest pytest-html webdriver-manager
   ```

4. **Chrome** installed (WebDriver is managed by `webdriver-manager`).

5. **Test data**: Ensure `testdata/data_test_signup.xlsx` and `testdata/data_test_login.xlsx` exist for automation. See column layout in `automation_test/signup_test.py` and `automation_test/login_test.py` if you need to adjust.

---

## Running tests

Run from the **project root** (`linky-testing/`) so `utils` and `core` resolve.

### Automation tests (pytest)

Uses `run_tests.bat` (activates `.venv`, writes HTML report to `reports/report.html`):

```powershell
# Run all automation tests
.\run_tests.bat

# Run a specific test file (name only, no path)
.\run_tests.bat signup_test.py
.\run_tests.bat login_test.py

# Re-run only last failed tests
.\run_tests.bat login_test.py lf
```

Or with pytest directly (with venv activated):

```powershell
pytest automation_test -s -v --html=reports/report.html --self-contained-html
pytest automation_test/signup_test.py -s -v --html=reports/report.html --self-contained-html
```

### Manual tests (prompt for input)

**Option 1 – batch script (recommended):**

```powershell
.\run_manual_test.bat signup    # sign-up flow
.\run_manual_test.bat login     # sign-in flow
```

**Option 2 – Python module:**

```powershell
python -m manual_test.signup_manual_test
python -m manual_test.login_manual_test
```

You’ll be prompted for the fields (e.g. email, password, OTP, expected message); the same `core` logic as automation is used.

---

## Configuration

Edit **`utils/configure.py`** to change:

- **`isEnableHeadless()`** — run Chrome in headless mode.
- **`getAutoRemoveContent()`** / **`getAutoRemoveContentPosition()`** — sign-up email generation (e.g. `+clerk_test` handling).

---

## Reports

After an automation run, open **`reports/report.html`** for the HTML report (self-contained, so you can open it in a browser without a server).
