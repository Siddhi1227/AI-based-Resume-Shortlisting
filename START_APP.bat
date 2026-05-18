@echo off
setlocal enabledelayedexpansion
title AI Resume Shortlisting System
color 0A

REM Change to the script directory
cd /d "%~dp0"
echo Current directory: %cd%
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo.
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)
echo ✅ Python found
echo.


echo.
echo ===============================================
echo   🚀 AI Resume Shortlisting System
echo ===============================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
    echo.
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment activated
echo.

REM Check if pip works
echo Testing pip...
pip --version
if errorlevel 1 (
    echo ❌ pip not working properly
    pause
    exit /b 1
)
echo ✅ pip working
echo.

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo ❌ ERROR: requirements.txt not found in %cd%
    echo Please ensure you're in the correct project directory
    pause
    exit /b 1
)

REM Check if requirements are installed
echo 📚 Checking dependencies...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo 📥 Installing required packages (this may take a few minutes)...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed
    echo.
) else (
    echo ✅ All dependencies already installed
    echo.
)

REM Download spaCy model if not present
echo 🧠 Checking spaCy model...
python -c "import spacy; spacy.load('en_core_web_sm')" >nul 2>&1
if errorlevel 1 (
    echo 📥 Downloading spaCy language model (this may take 1-2 minutes)...
    python -m spacy download en_core_web_sm
    if errorlevel 1 (
        echo ⚠️  Warning: spaCy model download had issues, but trying to continue...
    ) else (
        echo ✅ spaCy model downloaded
    )
    echo.
) else (
    echo ✅ spaCy model already present
    echo.
)

REM Check if app.py exists
if not exist "app.py" (
    echo ❌ ERROR: app.py not found in %cd%
    echo Please ensure you're in the correct project directory
    pause
    exit /b 1
)

REM Launch Streamlit app
echo ===============================================
echo ✨ Starting Streamlit application...
echo ===============================================
echo.
echo The app will open in your default browser at:
echo 👉 http://localhost:8501
echo.
echo Press Ctrl+C in this window to stop the server
echo.
timeout /t 2

streamlit run app.py --logger.level=debug

pause
