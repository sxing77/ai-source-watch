$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    & ".\setup.ps1"
}

& ".\.venv\Scripts\python.exe" -m ai_source_watch --output reports/latest.md
