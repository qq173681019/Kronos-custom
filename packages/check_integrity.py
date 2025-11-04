#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kronos系统完整性检查工具
检查解压后的文件是否完整
"""

import os
import sys
from pathlib import Path

def check_system_integrity():
    """检查系统文件完整性"""
    print("🔍 Kronos系统完整性检查")
    print("=" * 50)
    
    current_dir = Path.cwd()
    print(f"📁 检查目录: {current_dir}")
    print()
    
    # 必需的核心文件
    core_files = [
        "prediction_gui_lite.py",
        "prediction_gui.py", 
        "batch_stock_analysis.py",
        "start_gui_lite.bat",
        "start_gui.bat",
        "requirements.txt",
        "README.md"
    ]
    
    # 必需的目录
    required_dirs = [
        "model",
        "data"
    ]
    
    # 模型文件
    model_files = [
        "model/__init__.py",
        "model/multi_model_predictor.py",
        "model/kronos.py",
        "model/module.py"
    ]
    
    missing_files = []
    missing_dirs = []
    
    print("📋 检查核心文件:")
    for file in core_files:
        file_path = current_dir / file
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - 缺失!")
            missing_files.append(file)
    
    print("\n📂 检查必需目录:")
    for dir_name in required_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ - 缺失!")
            missing_dirs.append(dir_name)
    
    print("\n🧠 检查模型文件:")
    for file in model_files:
        file_path = current_dir / file
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - 缺失!")
            missing_files.append(file)
    
    print("\n" + "=" * 50)
    
    if not missing_files and not missing_dirs:
        print("🎉 系统完整性检查通过!")
        print("✅ 所有必需文件都存在")
        print("\n🚀 可以开始使用Kronos系统:")
        print("   - 双击 start_gui_lite.bat 启动轻量版")
        print("   - 双击 start_gui.bat 启动完整版")
        print("   - 或运行 install_requirements.bat 安装依赖")
        return True
    else:
        print("❌ 系统不完整!")
        if missing_files:
            print(f"   缺失文件: {len(missing_files)} 个")
            for file in missing_files:
                print(f"     - {file}")
        if missing_dirs:
            print(f"   缺失目录: {len(missing_dirs)} 个")
            for dir_name in missing_dirs:
                print(f"     - {dir_name}/")
        
        print("\n💡 解决方案:")
        print("   1. 确保所有5个压缩包都已解压到同一目录")
        print("   2. 重新解压所有压缩包")
        print("   3. 检查是否有解压错误")
        return False

def main():
    """主函数"""
    try:
        is_complete = check_system_integrity()
        
        print(f"\n{'='*50}")
        if is_complete:
            print("🎊 检查完成 - 系统就绪!")
        else:
            print("⚠️ 检查完成 - 需要修复")
        
        input("\n按任意键继续...")
        
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        input("按任意键继续...")

if __name__ == "__main__":
    main()