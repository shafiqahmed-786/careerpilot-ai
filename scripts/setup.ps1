# One-time setup for Windows PowerShell. Run from the project root:  .\scripts\setup.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "Created .env (add GROQ_API_KEY / TAVILY_API_KEY if you have them)" }
if (-not (Test-Path "frontend\.env.local")) { Copy-Item "frontend\.env.example" "frontend\.env.local"; Write-Host "Created frontend\.env.local" }

Write-Host "Starting PostgreSQL and Redis..."
docker compose up -d --wait postgres redis

Write-Host "Installing backend dependencies..."
Set-Location "$root\backend"
if (-not (Test-Path ".venv")) { python -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
Write-Host "Applying database migrations..."
& ".\.venv\Scripts\python.exe" -m alembic upgrade head

Write-Host "Installing frontend dependencies..."
Set-Location "$root\frontend"
npm ci

Write-Host "Setup complete. Start everything with:  .\scripts\dev.ps1"
