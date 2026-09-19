# Run script for Automated Test Suite
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Running Automated Test Suite (Unit & Integration)        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$env:PYTHONPATH = "$PSScriptRoot\backend"

& "$PSScriptRoot\venv\Scripts\python.exe" -m pytest backend/tests -v
