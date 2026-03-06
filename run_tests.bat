@echo off
setlocal

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Create reports folder if not exists
if not exist reports (
    mkdir reports
)

set REPORT_PATH=./reports/report.html

REM Run all tests
if "%1"=="" (
    pytest -s -v --html=%REPORT_PATH% --self-contained-html
    goto :end
)

set TEST_FILE=%1

if "%2"=="lf" (
    pytest -s -v %TEST_FILE% --lf --last-failed-no-failures=all --html=%REPORT_PATH% --self-contained-html
    goto :end
)

pytest -s -v %TEST_FILE% --html=%REPORT_PATH% --self-contained-html

:end
endlocal