@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
"C:\Program Files\Python313\python.exe" prediction_gui.py
pause
