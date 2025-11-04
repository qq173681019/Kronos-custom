@echo off
chcp 65001 >nul
echo.
echo ==========================================
echo   Kronos股票预测系统 - 智能分散打包工具
echo ==========================================
echo.
echo 正在启动打包程序...
echo 默认每个压缩包不超过100MB
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

python smart_packer.py

echo.
echo 打包完成! 请查看 packages 目录
pause