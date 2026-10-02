@echo off
setlocal
cd /d "%~dp0"

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
    echo Pulling the latest commit from origin/main...
    git pull origin main
    if errorlevel 1 (
        echo.
        echo WARNING: The update from origin/main failed. See the Git error above.
        echo Continuing with installation and startup...
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
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto error
"%VENV_PYTHON%" -m pip install --only-binary=:all: -r tools-frontend\requirements.txt
if errorlevel 1 goto error

echo Starting OFN Workbench...
"%VENV_PYTHON%" tools-frontend\launcher.py
if errorlevel 1 goto error
exit /b 0

:download_update
set "UPDATE_TEMP=%TEMP%\ofn-vocabulary-tools-update-%RANDOM%-%RANDOM%"
set "UPDATE_ZIP=%UPDATE_TEMP%\main.zip"
set "UPDATE_EXTRACT=%UPDATE_TEMP%\extracted"
for %%I in ("%~dp0.") do set "REPO_ROOT=%%~fI"

mkdir "%UPDATE_TEMP%"
if errorlevel 1 exit /b 1

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference = 'SilentlyContinue'; $ErrorActionPreference = 'Stop'; try { Invoke-WebRequest -Uri $args[0] -OutFile $args[1]; Expand-Archive -LiteralPath $args[1] -DestinationPath $args[2] -Force } catch { Write-Error $_; exit 1 }" "https://github.com/datagov-cz/ofn-vocabulary-tools/archive/refs/heads/main.zip" "%UPDATE_ZIP%" "%UPDATE_EXTRACT%"
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

:error
echo.
echo OFN Workbench could not be started. See the error above.
pause
exit /b 1
