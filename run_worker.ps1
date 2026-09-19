# Run script for ARQ Asynchronous Background Worker
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Document Intelligence Async Worker (ARQ)       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$env:PYTHONPATH = "$PSScriptRoot\backend"

& "$PSScriptRoot\venv\Scripts\python.exe" -m app.workers.worker
