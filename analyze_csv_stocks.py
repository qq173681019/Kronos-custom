#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV股票分析工具
从用户提供的CSV文件读取股票代码，进行批量预测分析
"""

import os
import sys
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置控制台编码和颜色支持
import locale
if sys.platform.startswith('win'):
    try:
        import codecs
        # 尝试设置UTF-8编码
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
        
        # 启用Windows控制台ANSI颜色支持
        import os
        os.system('color')
        
        # 尝试启用虚拟终端处理（Windows 10+）
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass
            
    except:
        try:
            # 备用方案
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
        except:
            # 如果都失败，至少确保不会崩溃
            pass

# ANSI颜色码定义
class Colors:
    RED = '\033[91m'       # 红色 - 买入
    LIGHT_RED = '\033[31m' # 淡红色
    GREEN = '\033[92m'     # 绿色 - 卖出
    YELLOW = '\033[93m'    # 黄色 - 少量买入
    BLUE = '\033[94m'      # 蓝色
    PURPLE = '\033[95m'    # 紫色
    CYAN = '\033[96m'      # 青色
    WHITE = '\033[97m'     # 白色
    BOLD = '\033[1m'       # 粗体
    UNDERLINE = '\033[4m'  # 下划线
    RESET = '\033[0m'      # 重置颜色

def test_color_support():
    """测试终端是否支持颜色显示"""
    try:
        # 简单的颜色测试
        test_output = f"{Colors.RED}TEST{Colors.RESET}"
        return True
    except:
        return False

def get_recommendation_color(recommendation):
    """根据交易建议获取对应颜色"""
    if recommendation in ['强烈买入', '买入']:
        return Colors.RED        # 红色 - 买入
    elif recommendation in ['少量买入']:
        return Colors.YELLOW     # 黄色 - 少量买入
    elif recommendation in ['强烈卖出', '卖出', '少量卖出']:
        return Colors.GREEN      # 绿色 - 卖出
    elif recommendation in ['观望']:
        return ''                # 观望不标记颜色（默认）
    else:
        return ''                # 其他情况也不标记颜色

def format_stock_code(code):
    """确保股票代码为完整的6位格式"""
    if code.isdigit():
        return code.zfill(6)
    return code

# 添加模型路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'model'))

from batch_stock_analysis import BatchStockAnalyzer

def analyze_stocks_from_csv(csv_file_path, output_dir=None, timeframe="daily", pred_days=5, use_kronos=False):
    """
    从CSV文件分析股票
    
    Args:
        csv_file_path: str, CSV文件路径
        output_dir: str, 输出目录，如果为None则自动生成
        timeframe: str, 时间框架 ("daily", "15min", "5min") 
        pred_days: int, 预测天数
        use_kronos: bool, 是否使用Kronos深度学习模型
    
    Returns:
        dict: 分析结果
    """
    
    print(f"=== CSV股票批量分析工具 ===")
    print(f"输入文件: {csv_file_path}")
    print(f"时间框架: {timeframe}")
    print(f"预测天数: {pred_days}")
    print(f"使用Kronos模型: {use_kronos}")
    
    # 🆕 测试颜色支持
    print("🎨 颜色支持测试:", end=" ")
    if test_color_support():
        print(f"{Colors.GREEN}✓ 支持颜色显示{Colors.RESET}")
    else:
        print("❌ 当前终端不支持颜色显示")
    
    print("="*50)
    
    # 检查文件是否存在
    if not os.path.exists(csv_file_path):
        print(f"错误: 文件 {csv_file_path} 不存在！")
        return None
    
    # 初始化分析器
    analyzer = BatchStockAnalyzer(
        use_kronos_model=use_kronos,
        model_path=None  # 如果有训练好的模型，可以在这里指定路径
    )
    
    # 从CSV加载股票代码
    print("正在加载股票代码...")
    stock_codes = analyzer.load_stock_codes_from_csv(csv_file_path)
    
    if not stock_codes:
        print("错误: 未能从CSV文件中加载到有效的股票代码！")
        print("请确保CSV文件包含股票代码列（支持列名：股票代码、stock_code、code、代码、symbol）")
        return None
    
    print(f"成功加载 {len(stock_codes)} 个股票代码: {stock_codes}")
    
    # 设置输出目录
    if output_dir is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"analysis_results_{timestamp}"
    
    # 开始批量分析
    print(f"\n开始批量分析，结果将保存到: {output_dir}")
    results = analyzer.batch_analyze(
        stock_codes=stock_codes,
        data_dir="data",
        timeframe=timeframe,
        pred_days=pred_days,
        output_dir=output_dir
    )
    
    # 显示结果摘要
    print("\n" + "="*50)
    print("分析完成摘要:")
    print(f"总股票数: {results['total_stocks']}")
    print(f"成功分析: {results['successful_predictions']}")
    print(f"失败分析: {results['failed_predictions']}")
    print(f"成功率: {results['successful_predictions']/results['total_stocks']*100:.1f}%")
    print(f"结果保存在: {output_dir}")
    
    # 显示成功分析的股票预测摘要
    if results['successful_predictions'] > 0:
        print("\n✅ 成功预测的股票:")
        print("-" * 120)
        print(f"{'股票代码':<20} {'当前价格':<10} {'预测1天':<10} {'预测3天':<10} {'预测5天':<10} {'涨跌幅%':<10} {'交易建议':<20}")
        print("-" * 120)
        
        for result in results['results']:
            if result and 'summary' in result:
                code = format_stock_code(result['stock_code'])  # 🆕 确保股票代码为6位
                summary = result['summary']
                current = summary['current_price']
                pred_prices = summary['predicted_prices']
                change_pct = summary['price_change_pcts'][0] if summary['price_change_pcts'] else 0
                
                pred_1 = pred_prices[0] if len(pred_prices) > 0 else 0
                pred_3 = pred_prices[2] if len(pred_prices) > 2 else 0  
                pred_5 = pred_prices[4] if len(pred_prices) > 4 else 0
                
                # 🆕 获取交易建议和颜色
                trading_rec = "未计算"
                if 'trading_signal' in result:
                    trading_rec = result['trading_signal'].get('recommendation', '观望')
                
                # 🆕 应用颜色格式
                color = get_recommendation_color(trading_rec)
                if color:  # 只有当有颜色时才添加重置码
                    colored_rec = f"{color}{trading_rec}{Colors.RESET}"
                    colored_code = f"{color}{code}{Colors.RESET}"
                else:  # 观望等不标记颜色的情况
                    colored_rec = trading_rec
                    colored_code = code
                
                print(f"{colored_code:<20} {current:<10.2f} {pred_1:<10.2f} {pred_3:<10.2f} {pred_5:<10.2f} {change_pct:<10.2f} {colored_rec:<20}")
        
        # 🆕 显示交易建议统计
        print("-" * 120)
        rec_counts = {}
        for result in results['results']:
            if result and 'trading_signal' in result:
                rec = result['trading_signal'].get('recommendation', '观望')
                rec_counts[rec] = rec_counts.get(rec, 0) + 1
        
        if rec_counts:
            print("交易建议统计:", end=" ")
            rec_parts = []
            for rec, count in sorted(rec_counts.items()):
                color = get_recommendation_color(rec)
                if color:  # 只有当有颜色时才添加重置码
                    colored_part = f"{color}{rec}({count}只){Colors.RESET}"
                else:  # 观望等不标记颜色的情况
                    colored_part = f"{rec}({count}只)"
                rec_parts.append(colored_part)
            print(" | ".join(rec_parts))
    
    # 显示跳过的股票列表
    if results['failed_predictions'] > 0:
        print(f"\n❌ 跳过的股票 ({results['failed_predictions']} 只):")
        print("-" * 60)
        print(f"{'股票代码':<10} {'跳过原因':<50}")
        print("-" * 60)
        
        for result in results['results']:
            if result and 'error' in result:
                code = format_stock_code(result['stock_code'])  # 🆕 确保股票代码为6位
                error_msg = result['error']
                # 简化错误信息显示
                if '未找到' in error_msg and '历史数据文件' in error_msg:
                    simple_error = "无历史数据"
                else:
                    simple_error = error_msg[:45] + "..." if len(error_msg) > 45 else error_msg
                
                print(f"{code:<10} {simple_error:<50}")
    
    print("="*50)
    return results

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSV股票批量分析工具')
    parser.add_argument('csv_file', help='包含股票代码的CSV文件路径')
    parser.add_argument('--output', '-o', help='输出目录路径')
    parser.add_argument('--timeframe', '-t', default='daily', 
                       choices=['daily', '15min', '5min'],
                       help='时间框架 (default: daily)')
    parser.add_argument('--pred-days', '-p', type=int, default=5,
                       help='预测天数 (default: 5)')
    parser.add_argument('--use-kronos', action='store_true',
                       help='使用Kronos深度学习模型')
    
    args = parser.parse_args()
    
    # 执行分析
    results = analyze_stocks_from_csv(
        csv_file_path=args.csv_file,
        output_dir=args.output,
        timeframe=args.timeframe,
        pred_days=args.pred_days,
        use_kronos=args.use_kronos
    )
    
    if results:
        print(f"\n分析完成！详细结果请查看输出目录中的文件。")
    else:
        print(f"\n分析失败，请检查输入文件和参数。")

if __name__ == "__main__":
    # 如果没有命令行参数，使用交互模式
    if len(sys.argv) == 1:
        print("=== 交互式CSV股票分析 ===")
        
        # 获取CSV文件路径
        csv_file = input("请输入CSV文件路径 (默认: sample_stock_list.csv): ").strip()
        if not csv_file:
            csv_file = "sample_stock_list.csv"
        
        # 获取时间框架
        timeframe = input("请选择时间框架 (daily/15min/5min, 默认: daily): ").strip()
        if not timeframe:
            timeframe = "daily"
        
        # 获取预测天数
        pred_days_input = input("请输入预测天数 (默认: 5): ").strip()
        try:
            pred_days = int(pred_days_input) if pred_days_input else 5
        except ValueError:
            pred_days = 5
        
        # 是否使用Kronos模型
        use_kronos_input = input("是否使用Kronos深度学习模型? (y/n, 默认: n): ").strip().lower()
        use_kronos = use_kronos_input in ['y', 'yes', '是']
        
        # 执行分析
        results = analyze_stocks_from_csv(
            csv_file_path=csv_file,
            timeframe=timeframe,
            pred_days=pred_days,
            use_kronos=use_kronos
        )
    else:
        main()