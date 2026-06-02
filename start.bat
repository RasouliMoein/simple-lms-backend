@echo off
:: Ensure the working directory is always the folder where this batch file is located
cd /d "%~dp0"

echo ==================================================
echo       Starting School & Exam Management API        
echo ==================================================
echo.

:: Check if virtual environment exists
if not exist ".venv" (
    echo [ERROR] Virtual environment (.venv) not found.
    echo Please make sure you are running this from the project root folder.
    echo.
    pause
    exit /b
)

:: Activate Virtual Environment
echo [1/3] Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment activate script not found at .venv\Scripts\activate.bat.
    echo.
    pause
    exit /b
)

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

:: If the server exits for any reason (success or failure), pause so the user can read the console
echo.
echo ==================================================
echo Server has stopped.
echo ==================================================
pause
