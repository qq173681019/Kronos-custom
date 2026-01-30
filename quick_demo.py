#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速演示脚本 - 分析单个股票
"""

import sys
from batch_stock_analysis import BatchStockAnalyzer

def main():
    print("=" * 60)
    print("Kronos 股票预测系统 - 快速演示")
    print("=" * 60)
    
    # 创建分析器
    print("\n正在初始化分析器...")
    analyzer = BatchStockAnalyzer(use_kronos_model=False)
    
    # 使用演示股票代码
    stock_code = "600977"
    print(f"\n正在分析股票: {stock_code}")
    print("时间框架: daily")
    print("预测天数: 3")
    
    # 运行分析
    try:
        result = analyzer.predict_single_stock(
            stock_code=stock_code,
            timeframe='daily',
            pred_days=3
        )
        
        if 'error' not in result:
            print("\n✓ 分析成功!")
            print(f"历史数据: {result.get('historical_data_points', 0)} 天")
            
            # 从 summary 中提取预测
            if 'summary' in result:
                summary = result['summary']
                print(f"当前价格: {summary.get('current_price', 0):.2f}")
                print(f"\n预测价格 (综合模型):")
                for i, price in enumerate(summary.get('predicted_prices', [])[:3], 1):
                    change_pct = summary.get('price_change_pcts', [0]*3)[i-1]
                    print(f"  第{i}天: {price:.2f} ({change_pct:+.2f}%)")
            
            if 'trading_signal' in result:
                signal = result['trading_signal']
                print(f"\n交易建议: {signal.get('recommendation', 'N/A')}")
                print(f"建议信心: {signal.get('confidence', 'N/A')}")
        else:
            print(f"\n✗ 分析失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"\n✗ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
