@echo off
title Hikyuu Backtest GUI

set PYTHON_PATH=C:\Users\123\AppData\Local\Programs\Python\Python311\python.exe
set HKU_DLL_PATH=C:\Users\123\AppData\Local\Programs\Python\Python311\Lib\site-packages\hikyuu\cpp

echo ========================================
echo   Hikyuu Strategy Backtest Tool
echo ========================================
echo.

REM -- Add hikyuu DLL path to system PATH --
if exist "%HKU_DLL_PATH%" (
    echo [INFO] Hikyuu DLL path: %HKU_DLL_PATH%
    set "PATH=%HKU_DLL_PATH%;%PATH%"
    echo [INFO] DLL path added to PATH.
) else (
    echo [WARNING] Hikyuu DLL path not found: %HKU_DLL_PATH%
    echo           Please check if hikyuu is installed correctly.
)
echo.

REM -- Check if Python exists --
if not exist "%PYTHON_PATH%" (
    echo [ERROR] Python not found at: %PYTHON_PATH%
    pause
    exit /b 1
)

REM -- Start app --
echo [INFO] Starting... Browser will open automatically.
echo [INFO] If browser doesn't open, visit the URL shown below.
echo.

cd /d "%~dp0"
"%PYTHON_PATH%" app.py

pause
