# Opens the API, the RQ worker and the frontend in three PowerShell windows. Run from the project root.
$root = Split-Path -Parent $PSScriptRoot
docker compose up -d --wait postgres redis
Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location '$root\backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location '$root\backend'; .\.venv\Scripts\python.exe -m app.worker"
Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location '$root\frontend'; npm run dev"
Write-Host "API http://localhost:8000/docs | Web http://localhost:3000 | Check with .\scripts\verify.ps1"
