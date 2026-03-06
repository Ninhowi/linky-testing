@echo off
setlocal

REM Activate virtual environment
call .venv\Scripts\activate.bat

set SCRIPT=%1

if "%SCRIPT%"=="signup" set SCRIPT=signup_manual_test
if "%SCRIPT%"=="login" set SCRIPT=login_manual_test

if "%SCRIPT%"=="" (
    echo Usage: run_manual_test.bat ^(signup ^| login^)
    echo   signup - run manual sign-up test
    echo   login  - run manual sign-in test
    exit /b 1
)

python -m manual_test.%SCRIPT%
endlocal
