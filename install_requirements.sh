#!/bin/bash

echo "========================================"
echo "  Kronos 股票预测系统 - 依赖安装脚本"
echo "========================================"
echo

echo "正在检查 Python 环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到 Python 环境！"
    echo "请先安装 Python 3.8+ 版本"
    exit 1
fi

echo
echo "正在升级 pip..."
python3 -m pip install --upgrade pip

echo
echo "正在安装核心依赖包..."
python3 -m pip install -r requirements.txt

echo
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo
echo "现在您可以运行以下程序:"
echo "  1. python3 prediction_gui.py     (主程序)"
echo "  2. python3 analyze_csv_stocks.py (CSV分析工具)"
echo "  3. python3 demo_csv_formats.py   (演示样例)"
echo
echo "注意: GUI程序在Linux/Mac上需要安装图形界面支持"
echo