@echo off
cd /d "%~dp0"
echo Starting Soccer Edge Engine...
python soccer_gui.py
if errorlevel 1 (
    echo.
    echo Error: Could not start Soccer Edge Engine
    pause
)
