@echo off
setlocal
cd /d "%~dp0"

call .venv\Scripts\activate.bat

if not exist reports mkdir reports

set REPORT_PATH=./reports/report.html

if "%~1"=="" (
    pytest tests -s -v --html=%REPORT_PATH% --self-contained-html
    goto :end
)

set TEST_FILE=%~1
if "%~2"=="lf" (
    pytest tests/%TEST_FILE% -s -v --lf --last-failed-no-failures=all --html=%REPORT_PATH% --self-contained-html
    goto :end
)

pytest tests/%TEST_FILE% -s -v --html=%REPORT_PATH% --self-contained-html

:end
endlocal
