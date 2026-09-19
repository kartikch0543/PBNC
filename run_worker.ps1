Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  DocuQ — Document Intelligence & Question Extraction  " -ForegroundColor Cyan
Write-Host "  Starting Dedicated Background Worker Process         " -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan

$env:PYTHONPATH = "$PSScriptRoot\backend"
.\venv\Scripts\python.exe -m app.workers.worker
