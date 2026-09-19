# Run script for FastAPI API Layer & Review Dashboard
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Document Intelligence Service (FastAPI Server) " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Set Python path to backend
$env:PYTHONPATH = "$PSScriptRoot\backend"

# Ensure uploads folder exists
if (-not (Test-Path "$PSScriptRoot\uploads")) {
    New-Item -ItemType Directory -Path "$PSScriptRoot\uploads" | Out-Null
}

# Run FastAPI server
& "$PSScriptRoot\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
