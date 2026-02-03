# 一键启动 Kronos 股票预测系统 (PowerShell版)
# 支持虚拟环境、依赖检查、错误处理

param(
    [switch]$NoVenv = $false
)

# 设置脚本编码
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Kronos 股票预测系统" -ForegroundColor Cyan
Write-Host "  AI股票预测分析平台" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "📍 工作目录: $scriptDir" -ForegroundColor Green
Write-Host ""

# 激活虚拟环境
if (-not $NoVenv -and (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "✅ 虚拟环境已找到" -ForegroundColor Green
    & ".\.venv\Scripts\Activate.ps1"
    Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "⚠️  使用系统 Python 环境" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔍 检查 Python 环境..." -ForegroundColor Cyan

# 检查 Python 是否存在
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: 找不到 Python!" -ForegroundColor Red
    Write-Host ""
    Write-Host "请确保:" -ForegroundColor Yellow
    Write-Host "  1. Python已安装" -ForegroundColor Yellow
    Write-Host "  2. Python已添加到系统路径" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按 Enter 键退出"
    exit 1
}

Write-Host ""
Write-Host "📦 检查必要的依赖..." -ForegroundColor Cyan

# 检查关键依赖
$packages = @{
    'tkinter' = '✅ tkinter 已安装'
    'pandas' = '✅ pandas 已安装'
    'numpy' = '✅ numpy 已安装'
    'matplotlib' = '✅ matplotlib 已安装'
}

foreach ($package in $packages.Keys) {
    try {
        python -c "import $package" 2>$null
        Write-Host "  $($packages[$package])" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  $package 未安装，尝试安装..." -ForegroundColor Yellow
        pip install $package -q 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $package 安装成功" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $package 安装失败" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "🚀 启动 Kronos 预测系统..." -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 启动主程序
try {
    python prediction_gui.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "⚠️  程序异常退出 (错误码: $LASTEXITCODE)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "🔧 故障排除:" -ForegroundColor Yellow
        Write-Host "  1. 检查 prediction_gui.py 是否存在" -ForegroundColor Yellow
        Write-Host "  2. 运行 python verify_dark_theme.py 验证配置" -ForegroundColor Yellow
        Write-Host "  3. 查看错误日志" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "按 Enter 键退出"
    }
} catch {
    Write-Host ""
    Write-Host "❌ 启动失败: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "按 Enter 键退出"
    exit 1
}
