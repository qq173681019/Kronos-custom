#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kronos股票预测系统 - 智能分散打包工具
将项目文件按大小智能分配到多个压缩包中，确保每个文件不超过100MB
"""

import os
import sys
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

class SmartPacker:
    def __init__(self, source_dir=None, max_size_mb=100):
        """
        初始化智能打包器
        
        Args:
            source_dir: 源目录路径，默认为当前目录
            max_size_mb: 每个压缩包的最大大小（MB）
        """
        self.source_dir = Path(source_dir) if source_dir else Path.cwd()
        self.max_size_bytes = max_size_mb * 1024 * 1024  # 转换为字节
        self.output_dir = self.source_dir / "packages"
        self.exclude_patterns = {
            '.git', '__pycache__', '*.pyc', '.gitignore', 
            'packages', '*.zip', '*.rar', '*.7z'
        }
        
    def should_exclude(self, file_path):
        """判断文件是否应该被排除"""
        file_path = Path(file_path)
        
        # 检查是否匹配排除模式
        for pattern in self.exclude_patterns:
            if pattern.startswith('*'):
                if file_path.name.endswith(pattern[1:]):
                    return True
            elif pattern in str(file_path):
                return True
        
        return False
    
    def get_file_info(self):
        """获取所有文件的信息"""
        file_info = []
        
        for root, dirs, files in os.walk(self.source_dir):
            # 排除不需要的目录
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.exclude_patterns)]
            
            for file in files:
                file_path = Path(root) / file
                
                if self.should_exclude(file_path):
                    continue
                
                try:
                    size = file_path.stat().st_size
                    relative_path = file_path.relative_to(self.source_dir)
                    
                    file_info.append({
                        'path': file_path,
                        'relative_path': relative_path,
                        'size': size,
                        'category': self.categorize_file(file_path)
                    })
                except (OSError, ValueError):
                    continue
        
        return sorted(file_info, key=lambda x: x['size'], reverse=True)
    
    def categorize_file(self, file_path):
        """对文件进行分类"""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        if suffix == '.py':
            if 'gui' in name:
                return 'gui'
            elif 'model' in str(file_path):
                return 'model'
            elif 'batch' in name or 'analyze' in name:
                return 'analysis'
            else:
                return 'core'
        elif suffix in ['.csv', '.json']:
            return 'data'
        elif suffix in ['.png', '.jpg', '.jpeg']:
            return 'images'
        elif suffix in ['.md', '.txt', '.bat', '.sh']:
            return 'docs'
        else:
            return 'misc'
    
    def create_package_plan(self, file_info):
        """创建打包计划"""
        packages = []
        current_package = {
            'name': 'kronos-core-01',
            'files': [],
            'size': 0,
            'categories': set()
        }
        
        # 按类别和大小智能分配
        for file_data in file_info:
            file_size = file_data['size']
            category = file_data['category']
            
            # 如果单个文件就超过限制，单独打包
            if file_size > self.max_size_bytes * 0.8:  # 留20%余量
                if current_package['files']:
                    packages.append(current_package)
                    current_package = {
                        'name': f'kronos-{category}-{len(packages)+1:02d}',
                        'files': [],
                        'size': 0,
                        'categories': set()
                    }
                
                # 大文件单独打包
                large_file_package = {
                    'name': f'kronos-{category}-large-{len(packages)+1:02d}',
                    'files': [file_data],
                    'size': file_size,
                    'categories': {category}
                }
                packages.append(large_file_package)
                continue
            
            # 检查是否可以添加到当前包
            if (current_package['size'] + file_size <= self.max_size_bytes and
                (not current_package['categories'] or 
                 category in current_package['categories'] or
                 len(current_package['categories']) < 3)):
                
                current_package['files'].append(file_data)
                current_package['size'] += file_size
                current_package['categories'].add(category)
            else:
                # 创建新包
                packages.append(current_package)
                current_package = {
                    'name': f'kronos-{category}-{len(packages)+1:02d}',
                    'files': [file_data],
                    'size': file_size,
                    'categories': {category}
                }
        
        # 添加最后一个包
        if current_package['files']:
            packages.append(current_package)
        
        return packages
    
    def create_packages(self):
        """执行打包"""
        print("🚀 Kronos股票预测系统 - 智能分散打包工具")
        print("=" * 60)
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        
        # 获取文件信息
        print("📋 正在扫描文件...")
        file_info = self.get_file_info()
        total_size = sum(f['size'] for f in file_info)
        
        print(f"📁 找到 {len(file_info)} 个文件，总大小: {total_size / 1024 / 1024:.2f} MB")
        
        # 创建打包计划
        print("🎯 正在制定打包计划...")
        packages = self.create_package_plan(file_info)
        
        print(f"📦 计划创建 {len(packages)} 个压缩包")
        print("-" * 60)
        
        # 执行打包
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, package in enumerate(packages, 1):
            package_name = f"{package['name']}_{timestamp}.zip"
            package_path = self.output_dir / package_name
            
            print(f"📦 创建包 {i}/{len(packages)}: {package_name}")
            print(f"   📂 类别: {', '.join(package['categories'])}")
            print(f"   📄 文件数: {len(package['files'])}")
            print(f"   💾 大小: {package['size'] / 1024 / 1024:.2f} MB")
            
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                for file_data in package['files']:
                    try:
                        zf.write(file_data['path'], file_data['relative_path'])
                    except Exception as e:
                        print(f"   ⚠️ 警告: 无法添加 {file_data['relative_path']}: {e}")
            
            # 验证压缩包大小
            actual_size = package_path.stat().st_size
            print(f"   ✅ 压缩后大小: {actual_size / 1024 / 1024:.2f} MB")
            
            if actual_size > self.max_size_bytes:
                print(f"   ⚠️ 警告: 压缩包超过限制大小!")
            
            print()
        
        # 创建说明文件
        self.create_readme(packages, timestamp)
        
        print("=" * 60)
        print(f"✅ 打包完成! 输出目录: {self.output_dir}")
        print(f"📦 共创建 {len(packages)} 个压缩包")
        print(f"📋 详细信息请查看: packages/打包说明_{timestamp}.txt")
    
    def create_readme(self, packages, timestamp):
        """创建打包说明文件"""
        readme_path = self.output_dir / f"打包说明_{timestamp}.txt"
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"Kronos股票预测系统 - 分散打包说明\n")
            f.write(f"打包时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("📦 压缩包列表:\n")
            f.write("-" * 40 + "\n")
            
            total_files = 0
            total_size = 0
            
            for i, package in enumerate(packages, 1):
                package_name = f"{package['name']}_{timestamp}.zip"
                f.write(f"{i:2d}. {package_name}\n")
                f.write(f"    类别: {', '.join(package['categories'])}\n")
                f.write(f"    文件数: {len(package['files'])}\n")
                f.write(f"    大小: {package['size'] / 1024 / 1024:.2f} MB\n")
                f.write(f"    主要文件:\n")
                
                # 列出主要文件
                for file_data in package['files'][:5]:
                    f.write(f"      - {file_data['relative_path']}\n")
                
                if len(package['files']) > 5:
                    f.write(f"      ... 等{len(package['files']) - 5}个文件\n")
                
                f.write("\n")
                total_files += len(package['files'])
                total_size += package['size']
            
            f.write("-" * 40 + "\n")
            f.write(f"总计: {len(packages)} 个压缩包, {total_files} 个文件, {total_size / 1024 / 1024:.2f} MB\n\n")
            
            f.write("📋 使用说明:\n")
            f.write("1. 下载所有压缩包到同一目录\n")
            f.write("2. 按序号顺序解压所有压缩包\n")
            f.write("3. 运行 start_gui_lite.bat 或 start_gui.bat 启动程序\n\n")
            
            f.write("🔧 系统要求:\n")
            f.write("- Python 3.8+\n")
            f.write("- 运行 install_requirements.bat 安装依赖\n")
            f.write("- Windows系统推荐使用批处理文件启动\n\n")
            
            f.write("📞 技术支持:\n")
            f.write("如有问题，请参考 README.md 文件或联系开发者\n")

def main():
    """主函数"""
    print("Kronos股票预测系统 - 智能分散打包工具")
    print("确保每个压缩包不超过100MB\n")
    
    # 检查是否有命令行参数
    max_size = 100
    if len(sys.argv) > 1:
        try:
            max_size = int(sys.argv[1])
            print(f"使用自定义大小限制: {max_size}MB")
        except ValueError:
            print("无效的大小参数，使用默认值: 100MB")
    
    # 创建打包器并执行
    packer = SmartPacker(max_size_mb=max_size)
    
    try:
        packer.create_packages()
        print("\n🎉 打包完成!")
        input("按任意键继续...")
        
    except KeyboardInterrupt:
        print("\n❌ 打包被用户中断")
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        input("按任意键继续...")

if __name__ == "__main__":
    main()