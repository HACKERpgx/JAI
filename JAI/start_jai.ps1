# JAI Assistant Startup Script
# Run this to start JAI server

Write-Host "Starting JAI Assistant..." -ForegroundColor Cyan

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.template to .env and configure your API keys." -ForegroundColor Yellow
    exit 1
}

# Start the server
Write-Host "JAI is now running on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python jai_assistant.py
