@echo off
echo Activating virtual environment...

REM Check if the activate script exists
if not exist ".venv\scripts\activate.bat" (
    echo ERROR: Virtual environment activation script not found at .venv\scripts\activate.bat
    echo Please ensure the virtual environment exists and you are running this script from the project root directory.
    pause
    exit /b 1
)

REM Activate the virtual environment using 'call' so control returns to this script
call .venv\scripts\activate.bat

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found in the current directory.
    pause
    exit /b 1
)

echo Starting the Prompt Manager application (main.py)...
REM Run the Python script
python main.py

echo.
echo Application exited. Press any key to close this window.
pause