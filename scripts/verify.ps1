# Health check + a full signup -> worker -> roadmap smoke run against your local Postgres/Redis.
$root = Split-Path -Parent $PSScriptRoot
try {
  Write-Host "health: " (Invoke-RestMethod http://localhost:8000/api/v1/health | ConvertTo-Json -Compress)
  Write-Host "ready:  " (Invoke-RestMethod http://localhost:8000/api/v1/health/ready | ConvertTo-Json -Compress)
} catch { Write-Host "API is not reachable on :8000 (is .\scripts\dev.ps1 running?)" -ForegroundColor Yellow }
Set-Location "$root\backend"
& ".\.venv\Scripts\python.exe" scripts\smoke_journey.py
