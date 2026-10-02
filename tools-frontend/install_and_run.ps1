# Keep the PowerShell entry point for existing shortcuts. The batch file owns
# setup so both Windows launch methods follow exactly the same checked path.
& "$PSScriptRoot\..\install_and_run.bat"
exit $LASTEXITCODE
