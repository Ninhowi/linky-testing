@echo off
setlocal
cd /d "%~dp0"

REM Activate virtual environment (project root)
call ..\.venv\Scripts\activate.bat

REM Create reports folder if not exists
if not exist reports mkdir reports

set REPORT_PATH=./reports/report.html
set AUTOMATION_DIR=automation_test

if "%~1"=="" (
    pytest %AUTOMATION_DIR% -s -v --html=%REPORT_PATH% --self-contained-html
    goto :end
)

set TEST_FILE=%~1
if "%~2"=="lf" (
    pytest %AUTOMATION_DIR%/%TEST_FILE% -s -v --lf --last-failed-no-failures=all --html=%REPORT_PATH% --self-contained-html
    goto :end
)

pytest %AUTOMATION_DIR%/%TEST_FILE% -s -v --html=%REPORT_PATH% --self-contained-html

:end
endlocal
