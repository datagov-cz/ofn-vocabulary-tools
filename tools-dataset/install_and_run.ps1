$ErrorActionPreference = "Stop"

$appDir = $PSScriptRoot
$repoDir = Split-Path -Parent $appDir
$venvPython = Join-Path $appDir ".venv\Scripts\python.exe"
$appUrl = "http://127.0.0.1:5000"

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
            Stop-WithMessage "Vytvoření virtuálního prostředí selhalo. Zkontrolujte, že je Python nainstalovaný a dostupný v PATH."
        }
    } else {
        Write-Host ""
        Write-Host "Používám existující lokální virtuální prostředí."
    }

    Write-Host ""
    Write-Host "Instaluji nebo aktualizuji závislosti..."
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Aktualizace pip selhala."
    }

    & $venvPython -m pip install --upgrade -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Instalace závislostí selhala."
    }

    Write-Host ""
    Write-Host "Spouštím aplikaci na adrese $appUrl ..."
    Start-Process powershell.exe -WorkingDirectory $appDir -ArgumentList @(
        "-NoExit",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "& '$venvPython' app.py"
    )

    Start-Sleep -Seconds 3
    Start-Process $appUrl

    Pop-Location
} catch {
    Stop-WithMessage "Instalace nebo spuštění aplikace selhalo: $($_.Exception.Message)"
}
