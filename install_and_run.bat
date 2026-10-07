@echo off
setlocal
cd /d "%~dp0"

set "RUN_MODE=production"
if "%~1"=="" goto arguments_done
if /I "%~1"=="--debug" (
    set "RUN_MODE=debug"
    goto arguments_done
)
if /I "%~1"=="--help" goto usage
if /I "%~1"=="/?" goto usage
echo Unknown option: %~1
goto usage_error

:arguments_done
where git >nul 2>nul
if errorlevel 1 (
    echo Git is not installed or is not available in PATH.
    echo Downloading the latest version from origin/main instead...
    call :download_update
    if errorlevel 1 (
        echo.
        echo WARNING: The manual update from origin/main failed. See the error above.
        echo Continuing with installation and startup...
    )
) else (
    set "LOCAL_CHANGES="
    for /f %%I in ('git status --porcelain') do set "LOCAL_CHANGES=1"
    if defined LOCAL_CHANGES (
        echo Local changes detected. Skipping automatic update to preserve them.
    ) else (
        echo Pulling the latest commit from origin/main...
        git pull origin main
        if errorlevel 1 (
            echo.
            echo WARNING: Automatic update failed. Continuing with the current version...
        )
    )
)
echo.

set "VENV_PYTHON=tools-frontend\.venv-windows\Scripts\python.exe"

if exist "%VENV_PYTHON%" goto install

echo Creating the Python environment...
if defined OFN_PYTHON (
    "%OFN_PYTHON%" -m venv tools-frontend\.venv-windows
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv tools-frontend\.venv-windows
    ) else (
        python -m venv tools-frontend\.venv-windows
    )
)
if errorlevel 1 goto error

:install
echo Installing Python dependencies...
"%VENV_PYTHON%" -m pip install --only-binary=:all: -r tools-frontend\requirements.txt
if errorlevel 1 goto error

if /I "%RUN_MODE%"=="debug" (
    echo Starting OFN Workbench in debug mode...
    "%VENV_PYTHON%" tools-frontend\app.py
) else (
    echo Starting OFN Workbench...
    "%VENV_PYTHON%" tools-frontend\launcher.py
)
if errorlevel 1 goto error
exit /b 0

:download_update
set "UPDATE_TEMP=%TEMP%\ofn-vocabulary-tools-update-%RANDOM%-%RANDOM%"
set "UPDATE_ZIP=%UPDATE_TEMP%\main.zip"
set "UPDATE_EXTRACT=%UPDATE_TEMP%\extracted"
set "UPDATE_URL=https://github.com/datagov-cz/ofn-vocabulary-tools/archive/refs/heads/main.zip"
for %%I in ("%~dp0.") do set "REPO_ROOT=%%~fI"

mkdir "%UPDATE_TEMP%"
if errorlevel 1 exit /b 1

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; $ErrorActionPreference = 'Stop'; try { Invoke-WebRequest -Uri $env:UPDATE_URL -OutFile $env:UPDATE_ZIP; Expand-Archive -LiteralPath $env:UPDATE_ZIP -DestinationPath $env:UPDATE_EXTRACT -Force } catch { Write-Error $_; exit 1 }"
if errorlevel 1 (
    rmdir /s /q "%UPDATE_TEMP%"
    exit /b 1
)

if not exist "%UPDATE_EXTRACT%\ofn-vocabulary-tools-main\" (
    echo The downloaded archive did not contain the expected repository folder.
    rmdir /s /q "%UPDATE_TEMP%"
    exit /b 1
)

xcopy "%UPDATE_EXTRACT%\ofn-vocabulary-tools-main\*" "%REPO_ROOT%\" /E /H /I /Y
if errorlevel 2 (
    rmdir /s /q "%UPDATE_TEMP%"
    exit /b 1
)

rmdir /s /q "%UPDATE_TEMP%"
echo Manual update completed successfully.
exit /b 0

:usage
echo Usage: install_and_run.bat [--debug]
echo.
echo   --debug  Start the Flask development server with automatic reload.
exit /b 0

:usage_error
echo Usage: install_and_run.bat [--debug]
exit /b 2

:error
echo.
echo OFN Workbench could not be started. See the error above.
pause
exit /b 1
