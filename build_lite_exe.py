#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kronos股票预测系统 - 轻量版EXE打包脚本
移除PyTorch依赖，仅保留技术分析功能
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build_folders():
    """清理之前的构建文件夹"""
    print("🧹 清理构建文件夹...")
    
    folders_to_clean = ['build', 'dist', '__pycache__']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"   ✅ 删除 {folder}")
    
    # 删除spec文件
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        os.remove(spec_file)
        print(f"   ✅ 删除 {spec_file}")

def create_lightweight_version():
    """创建轻量版本 - 移除PyTorch依赖"""
    print("📝 创建轻量版本...")
    
    # 读取原始文件
    with open('prediction_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换导入和相关代码
    lightweight_content = content.replace(
        "from model.multi_model_predictor import MultiModelPredictor",
        "# from model.multi_model_predictor import MultiModelPredictor  # 轻量版移除"
    )
    
    # 创建轻量版文件
    with open('prediction_gui_lite.py', 'w', encoding='utf-8') as f:
        f.write(lightweight_content)
    
    print("   ✅ 创建 prediction_gui_lite.py")
    return True

def create_build_script():
    """创建PyInstaller构建脚本"""
    print("📝 创建构建脚本...")
    
    # 版本信息
    version_info = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 0, 1, 0),
    prodvers=(2, 0, 1, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Kronos AI Team'),
        StringStruct(u'FileDescription', u'Kronos股票预测系统 - 轻量版'),
        StringStruct(u'FileVersion', u'2.0.1'),
        StringStruct(u'InternalName', u'KronosPredictor_Lite'),
        StringStruct(u'LegalCopyright', u'Copyright © 2024 Kronos AI Team. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'KronosPredictor_Lite.exe'),
        StringStruct(u'ProductName', u'Kronos股票预测系统'),
        StringStruct(u'ProductVersion', u'2.0.1 轻量版')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    # 创建版本文件
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    # PyInstaller命令 - 轻量版
    build_command = [
        'pyinstaller',
        '--onefile',  # 打包成单个EXE文件
        '--windowed',  # 不显示控制台窗口
        '--name=KronosPredictor_Lite',  # EXE文件名
        '--icon=icon.ico',  # 如果有图标文件
        '--version-file=version_info.txt',  # 版本信息文件
        '--add-data=data;data',  # 包含data文件夹
        
        # 基础依赖 - 排除PyTorch
        '--hidden-import=akshare',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=matplotlib',
        '--hidden-import=tkinter',
        '--hidden-import=sklearn',
        
        # 排除重量级模块
        '--exclude-module=torch',
        '--exclude-module=torchvision', 
        '--exclude-module=torchaudio',
        '--exclude-module=tensorflow',
        '--exclude-module=model.multi_model_predictor',
        '--exclude-module=model.kronos',
        '--exclude-module=model.module',
        
        # 收集所需模块
        '--collect-all=akshare',
        '--collect-all=matplotlib',
        
        # 其他优化
        '--noconfirm',  # 不询问覆盖
        '--clean',      # 清理缓存
        'prediction_gui_lite.py'
    ]
    
    return build_command

def build_exe():
    """执行打包"""
    print("🚀 开始打包轻量版EXE文件...")
    
    # 先创建轻量版
    if not create_lightweight_version():
        print("❌ 创建轻量版失败")
        return False
    
    build_command = create_build_script()
    
    # 移除图标参数如果图标文件不存在
    if not os.path.exists('icon.ico'):
        build_command = [cmd for cmd in build_command if not cmd.startswith('--icon')]
        print("   ⚠️  未找到icon.ico，跳过图标设置")
    
    try:
        # 执行PyInstaller命令
        print("📦 执行打包命令...")
        print(f"   命令: pyinstaller (轻量版)")
        
        result = subprocess.run(build_command, check=True, capture_output=True, text=True)
        
        print("✅ 打包成功！")
        
        # 检查输出文件
        exe_path = os.path.join('dist', 'KronosPredictor_Lite.exe')
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"📁 EXE文件位置: {exe_path}")
            print(f"📏 文件大小: {file_size:.2f} MB")
            return True
        else:
            print("❌ EXE文件未生成")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def update_prediction_gui():
    """更新prediction_gui.py，简化模型预测部分"""
    print("🔧 更新预测GUI，移除PyTorch依赖...")
    
    try:
        with open('prediction_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 注释掉模型相关的导入
        updated_content = content.replace(
            "from model.multi_model_predictor import MultiModelPredictor",
            "# from model.multi_model_predictor import MultiModelPredictor  # 轻量版移除"
        )
        
        # 找到并简化预测方法
        # 我们可以使用基于技术指标的简单预测
        
        with open('prediction_gui_lite.py', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("   ✅ 创建轻量版GUI文件")
        return True
        
    except Exception as e:
        print(f"   ❌ 更新失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 Kronos股票预测系统 - 轻量版EXE打包工具")
    print("=" * 60)
    print("💡 轻量版特性：")
    print("   - 移除PyTorch重型依赖")
    print("   - 保留完整技术分析功能")
    print("   - 大幅减小文件体积")
    print("   - 提高启动速度")
    print("=" * 60)
    
    # 1. 清理构建文件夹
    clean_build_folders()
    
    # 2. 执行打包
    success = build_exe()
    
    # 3. 后处理
    if success:
        print("\n" + "=" * 60)
        print("🎉 轻量版打包完成！")
        print("💡 使用说明：")
        print("   1. EXE文件位于 dist/KronosPredictor_Lite.exe")
        print("   2. 文件大小显著减小，启动更快")
        print("   3. 包含完整的KDJ+MACD+ATR技术分析")
        print("   4. 基于技术指标的智能预测算法")
        print("\n🔧 功能特点：")
        print("   ✅ KDJ随机指标分析")
        print("   ✅ MACD趋势分析")
        print("   ✅ ATR动态止损")
        print("   ✅ 基于技术指标的预测")
        print("   ❌ 深度学习模型（为减小体积）")
    else:
        print("\n❌ 轻量版打包失败！")
        print("💡 建议：")
        print("   1. 检查Python环境和依赖包")
        print("   2. 尝试普通版本打包")

if __name__ == "__main__":
    main()