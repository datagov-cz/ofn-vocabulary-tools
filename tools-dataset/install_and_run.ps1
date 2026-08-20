$ErrorActionPreference = "Stop"

$appDir = $PSScriptRoot
$venvPython = Join-Path $appDir ".venv\Scripts\python.exe"
$venvPythonw = Join-Path $appDir ".venv\Scripts\pythonw.exe"

function Stop-WithMessage {
    param(
        [string] $Message
    )

    Write-Host ""
    Write-Host $Message
    Read-Host "Stiskněte Enter pro ukončení"
    exit 1
}


Write-Host "Aktualizuji repozitář z větve main..."
Push-Location $repoDir
git pull origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Aktualizace repozitáře selhala."
}
Pop-Location

try {
    Push-Location $appDir

    if (-not (Test-Path $venvPython)) {
        Write-Host ""
        Write-Host "Vytvářím lokální virtuální prostředí..."

        $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
        if ($pyLauncher) {
            py -3 -m venv .venv
        } else {
            python -m venv .venv
        }

        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "Vytvoření virtuálního prostředí selhalo. Zkontrolujte, že je Python 3.12 nebo novější nainstalovaný a dostupný v PATH."
        }
    } else {
        Write-Host ""
        Write-Host "Používám existující lokální virtuální prostředí."
    }

    & $venvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Aplikace vyžaduje Python 3.12 nebo novější. Odstraňte složku .venv a spusťte instalaci s podporovanou verzí Pythonu."
    }

    Write-Host ""
    Write-Host "Instaluji nebo aktualizuji závislosti..."
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Aktualizace pip selhala."
    }

    & $venvPython -m pip install --upgrade -r requirements-windows.txt
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Instalace závislostí selhala."
    }

    Write-Host ""
    Write-Host "Spouštím aplikaci v samostatném okně..."
    $appProcess = Start-Process -FilePath $venvPythonw -WorkingDirectory $appDir -ArgumentList "desktop.py" -PassThru
    Start-Sleep -Seconds 2

    if ($appProcess.HasExited) {
        Stop-WithMessage "Aplikaci se nepodařilo spustit. Podrobnosti najdete v instance\tools-dataset.log."
    }

    Pop-Location
} catch {
    Stop-WithMessage "Instalace nebo spuštění aplikace selhalo: $($_.Exception.Message)"
}
