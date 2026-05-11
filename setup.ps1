$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -e .
& ".\.venv\Scripts\python.exe" -m playwright install chromium

Write-Host "Setup finished. Copy .env.example to .env and fill REPLICATE_API_TOKEN if needed."

