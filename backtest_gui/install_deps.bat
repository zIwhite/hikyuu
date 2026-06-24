@echo off
title Install Dependencies

echo ========================================
echo   Install Dependencies
echo ========================================
echo.
echo This will install: gradio, matplotlib, pandas
echo It may take 1-3 minutes.
echo.

REM -- Upgrade pip first --
echo [1/3] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM -- Install gradio --
echo [2/3] Installing gradio...
python -m pip install gradio
echo.

REM -- Install matplotlib and pandas --
echo [3/3] Installing matplotlib and pandas...
python -m pip install matplotlib pandas
echo.

echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Now you can double-click start.bat to run.
echo.
pause
