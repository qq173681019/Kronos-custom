#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Kronos系统的数据获取功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_data_sources():
    """测试各种数据源"""
    
    print("🧪 Kronos数据源测试")
    print("=" * 50)
    
    # 测试yfinance
    print("\n1. 测试yfinance...")
    try:
        import yfinance as yf
        
        # 测试A股
        codes_to_test = [
            ('000001', '000001.SZ', 'A股-平安银行'),
            ('600519', '600519.SS', 'A股-贵州茅台'),
            ('AAPL', 'AAPL', '美股-苹果'),
            ('0700', '0700.HK', '港股-腾讯')
        ]
        
        for code, symbol, name in codes_to_test:
            try:
                print(f"  测试 {name} ({code} → {symbol})...")
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='5d', interval='1d')
                
                if len(data) > 0:
                    latest_close = data['Close'].iloc[-1]
                    print(f"    ✅ 成功获取 {len(data)} 条数据，最新收盘价: {latest_close:.2f}")
                else:
                    print(f"    ⚠️ 获取到空数据")
                    
            except Exception as e:
                print(f"    ❌ 失败: {str(e)}")
                
    except ImportError:
        print("  ❌ yfinance未安装")
    
    # 测试AkShare
    print("\n2. 测试AkShare...")
    try:
        import akshare as ak
        
        # 测试A股数据
        test_code = '000001'
        print(f"  测试A股数据 ({test_code})...")
        
        try:
            data = ak.stock_zh_a_hist(symbol=test_code, period="daily", start_date="20241001", end_date="20241107", adjust="")
            if len(data) > 0:
                print(f"    ✅ 成功获取 {len(data)} 条数据")
            else:
                print(f"    ⚠️ 获取到空数据")
        except Exception as e:
            print(f"    ❌ 失败: {str(e)}")
            
    except ImportError:
        print("  ❌ AkShare未安装")
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    test_data_sources()