@echo off
echo ========================================
echo   Kronos股票预测系统 - 数据源配置工具
echo ========================================
echo.

echo 📦 正在安装数据源依赖包...
echo.

:: 安装基础依赖
echo 1/4 安装基础依赖...
pip install pandas numpy matplotlib requests

:: 安装AkShare（主要数据源）
echo 2/4 安装AkShare（主要数据源）...
pip install akshare

:: 安装yfinance（备用数据源）
echo 3/4 安装yfinance（备用数据源）...
pip install yfinance

:: 安装TuShare（可选数据源）
echo 4/4 安装TuShare（可选数据源）...
pip install tushare

echo.
echo ✅ 依赖包安装完成！
echo.

:: 创建配置目录
if not exist "config" mkdir config

echo 📝 配置API密钥...
echo.
echo 请选择要配置的数据源（可选）:
echo [1] TuShare (免费注册，支持A股)
echo [2] Alpha Vantage (免费注册，支持全球股票)
echo [3] 跳过API配置
echo.
set /p choice="请输入选择 (1-3): "

if "%choice%"=="1" goto setup_tushare
if "%choice%"=="2" goto setup_alphavantage
if "%choice%"=="3" goto finish
goto invalid_choice

:setup_tushare
echo.
echo 🔑 配置TuShare:
echo 1. 访问 https://tushare.pro/register 注册账户
echo 2. 登录后在用户中心获取token
echo.
set /p tushare_token="请输入您的TuShare token (或按回车跳过): "
if not "%tushare_token%"=="" (
    echo %tushare_token% > config\tushare_token.txt
    echo ✅ TuShare token 已保存到 config\tushare_token.txt
) else (
    echo ⏭️ 跳过TuShare配置
)
echo.
goto ask_alphavantage

:ask_alphavantage
set /p alpha_choice="是否继续配置Alpha Vantage? (y/n): "
if /i "%alpha_choice%"=="y" goto setup_alphavantage
goto finish

:setup_alphavantage
echo.
echo 🔑 配置Alpha Vantage:
echo 1. 访问 https://www.alphavantage.co/support/#api-key 免费注册
echo 2. 获取免费API key
echo.
set /p alpha_key="请输入您的Alpha Vantage API key (或按回车跳过): "
if not "%alpha_key%"=="" (
    echo %alpha_key% > config\alpha_vantage_key.txt
    echo ✅ Alpha Vantage API key 已保存到 config\alpha_vantage_key.txt
) else (
    echo ⏭️ 跳过Alpha Vantage配置
)
goto finish

:invalid_choice
echo ❌ 无效选择，跳过API配置
goto finish

:finish
echo.
echo ========================================
echo 🎉 配置完成！
echo ========================================
echo.
echo 📊 可用数据源:
echo   ✅ AkShare (主要) - 支持A股/港股/美股
echo   ✅ yfinance (备用) - 支持全球股票
if exist "config\tushare_token.txt" (
    echo   ✅ TuShare (已配置) - 支持A股专业数据
) else (
    echo   ⚠️ TuShare (未配置) - 可选择配置
)
if exist "config\alpha_vantage_key.txt" (
    echo   ✅ Alpha Vantage (已配置) - 支持全球股票
) else (
    echo   ⚠️ Alpha Vantage (未配置) - 可选择配置
)
echo.
echo 💡 使用建议:
echo   - AkShare为主要数据源，网络良好时使用
echo   - yfinance作为备用，适合获取美股数据
echo   - TuShare提供更专业的A股数据分析
echo   - Alpha Vantage适合国际市场数据
echo.
echo 🚀 现在可以启动Kronos系统，享受多数据源的稳定体验！
echo.
pause