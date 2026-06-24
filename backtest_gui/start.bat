@echo off
chcp 65001 >nul
title Hikyuu策略回测可视化工具

echo ========================================
echo   Hikyuu 策略回测可视化工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.10或3.11版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查gradio是否安装
python -c "import gradio" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖库 gradio...
    python -m pip install gradio matplotlib pandas
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [提示] 依赖安装完成！
)

REM 检查hikyuu是否安装
python -c "import hikyuu" >nul 2>&1
if errorlevel 1 (
    echo [警告] 未检测到hikyuu库，界面可启动但无法进行回测
    echo [提示] 请先安装hikyuu: pip install hikyuu
    echo.
)

echo [提示] 正在启动回测工具...
echo [提示] 浏览器将自动打开，如果没有打开，请手动访问下方地址
echo.

python "%~dp0app.py"

pause
