@echo off
chcp 65001 >nul
echo.
echo ==========================================
echo   Kronos股票预测系统 - 解压安装指导
echo ==========================================
echo.
echo 📋 解压步骤:
echo 1. 确保所有5个压缩包都在同一目录中
echo 2. 按顺序解压所有压缩包到同一个目录
echo 3. 运行环境配置和启动程序
echo.
echo 📦 需要解压的文件:
echo    kronos-core-01_xxxxxxxx_xxxxxx.zip     (主要文件 - 最大)
echo    kronos-analysis-02_xxxxxxxx_xxxxxx.zip (分析模块)
echo    kronos-docs-03_xxxxxxxx_xxxxxx.zip     (文档)
echo    kronos-data-04_xxxxxxxx_xxxxxx.zip     (数据文件)
echo    kronos-model-05_xxxxxxxx_xxxxxx.zip    (启动脚本)
echo.
echo 🚀 启动程序:
echo.
echo 方式1: 双击 start_gui_lite.bat (推荐 - 轻量版)
echo 方式2: 双击 start_gui.bat (完整版)
echo 方式3: 运行 install_requirements.bat 安装依赖后手动启动
echo.
echo 💡 第一次使用建议:
echo 1. 运行 install_requirements.bat 安装Python依赖
echo 2. 使用 start_gui_lite.bat 启动轻量版GUI
echo 3. 输入股票代码测试功能
echo.
echo ⚠️ 注意事项:
echo - 需要Python 3.8+环境
echo - 需要网络连接获取股票数据
echo - 确保所有文件都在同一目录下
echo.
pause