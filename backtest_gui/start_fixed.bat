@echo off
title Hikyuu Backtest GUI

set PYTHON_PATH=C:\Users\123\AppData\Local\Programs\Python\Python311\python.exe

echo ========================================
echo   Hikyuu Strategy Backtest Tool
echo ========================================
echo.
echo Using Python: %PYTHON_PATH%
echo.

REM -- Check if Python exists --
if not exist "%PYTHON_PATH%" (
    echo [ERROR] Python not found at: %PYTHON_PATH%
    echo.
    echo Please edit this bat file and set the correct Python path.
    echo Or run: where python
    echo to find your Python location.
    echo.
    pause
    exit /b 1
)

REM -- Install dependencies if needed --
echo [INFO] Checking dependencies...
"%PYTHON_PATH%" -c "import gradio" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages: gradio, matplotlib, pandas
    echo        This may take 1-3 minutes, please wait...
    echo.
    "%PYTHON_PATH%" -m pip install --upgrade pip
    "%PYTHON_PATH%" -m pip install gradio matplotlib pandas
    if errorlevel 1 (
        echo.
        echo [ERROR] Installation failed!
        echo Please check your internet connection.
        pause
        exit /b 1
    )
    echo.
    echo [INFO] Dependencies installed successfully!
    echo.
)

REM -- Check hikyuu --
"%PYTHON_PATH%" -c "import hikyuu" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] hikyuu package not found.
    echo           Trying to install hikyuu...
    echo.
    "%PYTHON_PATH%" -m pip install hikyuu
    if errorlevel 1 (
        echo.
        echo [WARNING] hikyuu installation failed.
        echo           GUI will start but backtest will not work.
        echo.
    )
)

REM -- Start app --
echo [INFO] Starting... Browser will open automatically.
echo [INFO] If browser doesn't open, visit the URL shown below.
echo.

cd /d "%~dp0"
"%PYTHON_PATH%" app.py

pause
