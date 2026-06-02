@echo off
echo ==================================================
echo       Starting School & Exam Management API        
echo ==================================================
echo.

:: Check if virtual environment exists
if not exist ".venv" (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please install dependencies first.
    pause
    exit /b
)

:: Activate Virtual Environment
echo [1/3] Activating virtual environment...
call .venv\Scripts\activate.bat

:: Check if database exists, otherwise run database initializer
if not exist "instance\school.db" if not exist "school.db" (
    echo [2/3] Database not found. Initializing database and default accounts...
    python init_db.py
) else (
    echo [2/3] Database found. Skipping initialization.
)

:: Run Flask App
echo [3/3] Launching Flask Server...
echo Server running at http://localhost:5000/docs/
echo Press Ctrl+C to stop the server.
echo.
python app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server stopped unexpectedly.
    pause
)
