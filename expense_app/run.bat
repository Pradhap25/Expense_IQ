@echo off
echo.
echo ==========================================
echo   ExpenseIQ - Setup and Run
echo ==========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo Virtual environment activated.

echo Installing dependencies...
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo Dependencies installed.

if not exist instance\expense_manager.db (
    echo Seeding demo data...
    python seed_data.py
) else (
    echo Database already exists.
)

echo.
echo ==========================================
echo   ExpenseIQ is ready!
echo   Open: http://localhost:5000
echo   Demo: demo@example.com / demo1234
echo ==========================================
echo.

python app.py
pause
