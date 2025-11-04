@echo off
chcp 65001 >nul
echo.
echo ==========================================
echo   Kronos系统完整性检查
echo ==========================================
echo.

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

python check_integrity.py

pause