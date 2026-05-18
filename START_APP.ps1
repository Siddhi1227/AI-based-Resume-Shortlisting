# AI Resume Shortlisting System - PowerShell Launcher
# Right-click this file and select "Run with PowerShell"

Write-Host "`n===============================================" -ForegroundColor Green
Write-Host "   🚀 AI Resume Shortlisting System" -ForegroundColor Green
Write-Host "===============================================`n" -ForegroundColor Green

# Get current directory
$currentDir = Get-Location
Write-Host "Current directory: $currentDir`n"

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation`n" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✅ Python found: $pythonVersion`n" -ForegroundColor Green

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "✅ Virtual environment created`n" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists`n" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✅ Virtual environment activated`n" -ForegroundColor Green

# Check requirements.txt
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ ERROR: requirements.txt not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host "📚 Checking and installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✅ Dependencies installed`n" -ForegroundColor Green

# Download spaCy model
Write-Host "🧠 Checking spaCy language model..." -ForegroundColor Cyan
python -c "import spacy; spacy.load('en_core_web_sm')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "📥 Downloading spaCy language model..." -ForegroundColor Cyan
    python -m spacy download en_core_web_sm
    Write-Host ""
}
Write-Host "✅ spaCy model ready`n" -ForegroundColor Green

# Check app.py
if (-not (Test-Path "app.py")) {
    Write-Host "❌ ERROR: app.py not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Launch Streamlit
Write-Host "===============================================" -ForegroundColor Green
Write-Host "✨ Starting Streamlit application..." -ForegroundColor Green
Write-Host "===============================================`n" -ForegroundColor Green
Write-Host "The app will open in your default browser at:" -ForegroundColor Yellow
Write-Host "👉 http://localhost:8501`n" -ForegroundColor Yellow
Write-Host "Press Ctrl+C in this window to stop the server`n" -ForegroundColor Yellow

Start-Sleep -Seconds 2
streamlit run app.py

Read-Host "`nPress Enter to exit"
