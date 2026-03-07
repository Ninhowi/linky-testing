# Linky Testing

Selenium-based UI tests for [Linky](https://www.linkynow.site): **sign-up** and **sign-in** flows, with support for **automated** (Excel-driven) and **manual** (prompt-driven) runs.

The project offers two structures:

- **POM (Page Object Model)** — at project root: pages, flows, tests, shared utils. Recommended for maintainability.
- **Function-based** — legacy flow-based code under `function-based/`: core flows, automation_test, manual_test.

---

## Project structure

```
linky-testing/
├── pages/                     # [POM] Page objects
│   ├── base_page.py           # Base URL, driver, wait
│   ├── sign_up_page.py        # Sign-up form locators & actions
│   ├── sign_in_page.py        # Sign-in (email → password)
│   ├── verify_email_page.py   # OTP (verify-email / factor-two)
│   └── dashboard_page.py      # Success (start-chat)
├── flows/                     # [POM] Step logic using page objects
│   ├── signup_flow.py
│   └── login_flow.py
├── tests/                     # [POM] Pytest tests (Excel-driven)
│   ├── test_signup.py
│   └── test_login.py
├── utils/                     # [POM] Shared helpers
│   ├── chrome_driver.py
│   ├── configure.py
│   ├── generate_email.py
│   └── safe_input.py
├── testdata/                  # Excel test data (shared by POM and function-based)
│   ├── data_test_signup.xlsx
│   └── data_test_login.xlsx
├── reports/                   # Pytest HTML reports (generated)
├── conftest.py                # [POM] Fixtures (driver, pages)
├── run_tests.bat              # [POM] Run pytest tests/
│
└── function-based/            # Legacy function-based approach
    ├── core/                  # Flow logic (no page objects)
    │   ├── signup_flow.py
    │   └── login_flow.py
    ├── utils/
    ├── automation_test/       # Uses root testdata/
    ├── manual_test/
    ├── run_tests.bat          # Run from function-based/
    └── run_manual_test.bat    # Manual signup/login
```

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

5. **Test data**: Ensure `testdata/data_test_signup.xlsx` and `testdata/data_test_login.xlsx` exist at **project root** — both POM and function-based use this single `testdata/` folder.

---

## Running tests

**Activate the virtual environment first** (from project root):

```powershell
.venv\Scripts\activate
```

Then run from the **project root** (`linky-testing/`).

### POM (recommended)

```powershell
# Run all POM tests
.\run_tests.bat

# Run a specific test file
.\run_tests.bat test_signup.py
.\run_tests.bat test_login.py

# Re-run only last failed
.\run_tests.bat test_login.py lf
```

Or with pytest directly (venv activated):

```powershell
pytest tests -s -v --html=reports/report.html --self-contained-html
pytest tests/test_signup.py -s -v --html=reports/report.html --self-contained-html
```

### Function-based (legacy)

```powershell
cd function-based
.\run_tests.bat              # all automation tests
.\run_tests.bat signup_test.py
.\run_tests.bat login_test.py lf
.\run_manual_test.bat signup
.\run_manual_test.bat login
```

---

## Configuration

- **POM**: Edit **`utils/configure.py`** at root.
- **Function-based**: Edit **`function-based/utils/configure.py`**.

Options:

- **`isEnableHeadless()`** — run Chrome in headless mode.
- **`getAutoRemoveContent()`** / **`getAutoRemoveContentPosition()`** — sign-up email generation (e.g. `+clerk_test` handling).

---

## Reports

After a run, open **`reports/report.html`** (at root for POM; `function-based/reports/report.html` for legacy) for the self-contained HTML report.
