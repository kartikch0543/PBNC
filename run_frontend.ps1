Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  DocuQ — Document Intelligence & Question Extraction  " -ForegroundColor Cyan
Write-Host "  Starting React 18 + Vite Dev Server on http://localhost:5173" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\frontend"
npm run dev
