@echo off
setlocal
cd /d "%~dp0"

where git >nul 2>nul
if errorlevel 1 (
    echo Git is not installed or is not available in PATH. Skipping update.
) else (
    echo Pulling the latest commit from origin/main...
    git pull origin main
    if errorlevel 1 (
        echo.
        echo WARNING: The update from origin/main failed. See the Git error above.
        echo Continuing with installation and startup...
    )
)
echo.

set "VENV_PYTHON=.venv-windows\Scripts\python.exe"

if exist "%VENV_PYTHON%" goto install

echo Creating the Python environment...
if defined OFN_PYTHON (
    "%OFN_PYTHON%" -m venv .venv-windows
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv-windows
    ) else (
        python -m venv .venv-windows
    )
)
if errorlevel 1 goto error

:install
echo Installing Python dependencies...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto error
"%VENV_PYTHON%" -m pip install --only-binary=:all: -r requirements.txt
if errorlevel 1 goto error

echo Starting OFN Workbench...
"%VENV_PYTHON%" launcher.py
if errorlevel 1 goto error
exit /b 0

:error
echo.
echo OFN Workbench could not be started. See the error above.
pause
exit /b 1
