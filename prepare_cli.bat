@echo off
REM Move to the directory of this script (saving current directory to return later)
pushd "%~dp0"

REM Check if 'uv' is installed
echo Checking for uv...
where uv >nul 2>nul
if errorlevel 1 (
    echo uv not found. Installing uv...
    pip install uv
) else (
    echo uv is already installed.
)

REM Recreate venv only if needed
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv .venv
) else (
    echo Using existing virtual environment...
)

REM Activate the virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Navigate to CLI directory and install in editable mode
echo Installing CLI in editable mode...
cd src\cli
uv pip install -e .

REM Return to root directory
cd ..\..

REM Set the PYTHONPATH environment variable (optional, useful for imports)
set PYTHONPATH=%PYTHONPATH%;%CD%\src\cli

echo.
echo ========================================
echo CLI installed successfully!
echo ========================================
echo.
echo To use the CLI:
echo 1. Activate the virtual environment: .venv\Scripts\activate.bat
echo 2. Run your CLI command
echo.

REM Return to original directory
popd

pause