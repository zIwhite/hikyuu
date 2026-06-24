@echo off
title Hikyuu Backtest GUI

echo ========================================
echo   Hikyuu Strategy Backtest Tool
echo ========================================
echo.

REM -- Check Python --
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10 or 3.11 first.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM -- Install dependencies if needed --
echo [INFO] Checking dependencies...
python -c "import gradio" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages: gradio, matplotlib, pandas
    echo        This may take 1-3 minutes, please wait...
    echo.
    python -m pip install --upgrade pip
    python -m pip install gradio matplotlib pandas
    if errorlevel 1 (
        echo.
        echo [ERROR] Installation failed!
        echo Please check your internet connection.
        echo Or run manually: pip install gradio matplotlib pandas
        pause
        exit /b 1
    )
    echo.
    echo [INFO] Dependencies installed successfully!
    echo.
)

REM -- Check hikyuu --
python -c "import hikyuu" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] hikyuu package not found.
    echo           GUI will start but backtest will not work.
    echo           Install hikyuu first: pip install hikyuu
    echo.
)

REM -- Start app --
echo [INFO] Starting... Browser will open automatically.
echo [INFO] If browser doesn't open, visit the URL shown below.
echo.

cd /d "%~dp0"
python app.py

pause
