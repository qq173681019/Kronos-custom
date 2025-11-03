@echo off
echo ========================================
echo   Kronos 股票预测系统 - 依赖安装脚本
echo ========================================
echo.

echo 正在检查 Python 环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python 环境！
    echo 请先安装 Python 3.8+ 版本
    pause
    exit /b 1
)

echo.
echo 正在升级 pip...
python -m pip install --upgrade pip

echo.
echo 正在安装核心依赖包...
python -m pip install -r requirements.txt

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 现在您可以运行以下程序:
echo   1. python prediction_gui.py     (主程序)
echo   2. python analyze_csv_stocks.py (CSV分析工具)
echo   3. python demo_csv_formats.py   (演示样例)
echo.
echo 或者运行编译好的EXE文件:
echo   dist\KronosPredictor_Lite.exe
echo.
pause