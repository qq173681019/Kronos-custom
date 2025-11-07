#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版数据获取功能
"""

import sys
import os

# 模拟数据获取测试
def test_symbol_variants():
    """测试股票代码变体生成"""
    
    def generate_symbol_variants(code):
        """生成多种可能的股票代码格式"""
        variants = []
        
        # 如果已经包含后缀，直接使用并生成变体
        if '.' in code:
            variants.append(code)
            # 也尝试不带后缀的版本
            base_code = code.split('.')[0]
            variants.extend(generate_symbol_variants(base_code))
            return list(dict.fromkeys(variants))  # 去重
            
        # A股代码处理
        if len(code) == 6 and code.isdigit():
            if code.startswith('6'):
                # 上海证券交易所
                variants.extend([f"{code}.SS", f"{code}.SH"])
            elif code.startswith(('0', '3')):
                # 深圳证券交易所  
                variants.extend([f"{code}.SZ", f"{code}.SS"])
            elif code.startswith('4'):
                # 北京证券交易所
                variants.extend([f"{code}.BJ", f"{code}.SS", f"{code}.SZ"])
        
        # 港股代码处理
        elif len(code) <= 5 and code.isdigit():
            # 港股代码通常是1-5位数字
            padded_code = code.zfill(4)
            variants.extend([f"{padded_code}.HK", f"{code}.HK"])
        
        # 美股等其他市场，直接使用原代码
        else:
            variants.append(code)
        
        # 如果以上都不匹配，添加一些通用尝试
        if not variants:
            variants = [code, f"{code}.SS", f"{code}.SZ", f"{code}.HK"]
        
        return variants
    
    test_codes = [
        '000713',  # 您测试的代码
        '000001',  # 平安银行
        '600519',  # 茅台
        '300001',  # 创业板
        '688981',  # 科创板
        '0700',    # 港股腾讯
        'AAPL'     # 美股苹果
    ]
    
    print("🧪 股票代码变体生成测试")
    print("=" * 50)
    
    for code in test_codes:
        variants = generate_symbol_variants(code)
        print(f"{code:8} → {', '.join(variants)}")
    
    print("\n" + "=" * 50)

def test_yfinance_multiple_codes():
    """测试yfinance多种代码格式"""
    try:
        import yfinance as yf
        
        # 测试000713的多种格式
        variants = ['000713.SZ', '000713.SS', '000713.SH']
        
        print("\n🔍 测试000713的多种格式:")
        print("-" * 30)
        
        for symbol in variants:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='5d')
                
                if not data.empty:
                    latest_close = data['Close'].iloc[-1]
                    print(f"✅ {symbol:12} → {len(data)}条数据, 最新价格: {latest_close:.2f}")
                else:
                    print(f"❌ {symbol:12} → 空数据")
                    
            except Exception as e:
                print(f"❌ {symbol:12} → 错误: {str(e)}")
        
    except ImportError:
        print("❌ yfinance未安装")

if __name__ == "__main__":
    test_symbol_variants()
    test_yfinance_multiple_codes()