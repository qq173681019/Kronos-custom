@echo off
REM 一键启动 Kronos 股票预测系统
REM 自动激活虚拟环境，处理依赖和错误

setlocal enabledelayedexpansion

REM 设置编码为 UTF-8
chcp 65001 > nul

echo.
echo ============================================
echo  Kronos 股票预测系统
echo  AI股票预测分析平台
echo ============================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo 📍 工作目录: %SCRIPT_DIR%
echo.

REM 检查虚拟环境是否存在
if exist ".venv\Scripts\activate.bat" (
    echo ✅ 虚拟环境已找到
    call .venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
) else (
    echo ⚠️  虚拟环境不存在，尝试使用系统 Python
)

echo.
echo 🔍 检查 Python 环境...
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 找不到 Python!
    echo.
    echo 请确保:
    echo   1. Python已安装
    echo   2. Python已添加到系统路径
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set "PYTHON_VERSION=%%i"
echo ✅ Python 版本: %PYTHON_VERSION%

echo.
echo 📦 检查必要的依赖...

REM 检查关键依赖
python -c "import tkinter; print('  ✅ tkinter 已安装')" 2>nul
if errorlevel 1 (
    echo   ❌ tkinter 未安装 (Tkinter 是 Python 内置的，请重新安装 Python)
)

python -c "import pandas; print('  ✅ pandas 已安装')" 2>nul
if errorlevel 1 (
    echo   ⚠️  pandas 未安装，尝试安装...
    pip install pandas -q
)

python -c "import numpy; print('  ✅ numpy 已安装')" 2>nul
if errorlevel 1 (
    echo   ⚠️  numpy 未安装，尝试安装...
    pip install numpy -q
)

python -c "import matplotlib; print('  ✅ matplotlib 已安装')" 2>nul
if errorlevel 1 (
    echo   ⚠️  matplotlib 未安装，尝试安装...
    pip install matplotlib -q
)

echo.
echo 🚀 启动 Kronos 预测系统...
echo.
echo ============================================
echo.

REM 启动主程序
python prediction_gui.py

REM 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo ❌ 程序异常退出 (错误码: %errorlevel%)
    echo.
    echo 🔧 故障排除:
    echo   1. 检查 prediction_gui.py 是否存在
    echo   2. 运行 verify_dark_theme.py 验证配置
    echo   3. 查看错误日志
    echo.
    pause
)

endlocal
