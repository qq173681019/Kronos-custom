import sys
import os
import pandas as pd

# Add current directory to path so we can import batch_stock_analysis
sys.path.append(os.getcwd())

from batch_stock_analysis import BatchStockAnalyzer

def test_fallbacks():
    print("=== Testing Data Source Fallbacks ===")
    analyzer = BatchStockAnalyzer()
    stock_code = "600036" # China Merchants Bank
    
    print(f"\nTesting Tencent data for {stock_code}...")
    df_tencent = analyzer._try_tencent_data(stock_code, "daily")
    if df_tencent is not None and not df_tencent.empty:
        print("✅ Tencent data fetch successful!")
        print(df_tencent.head())
        print(df_tencent.tail())
    else:
        print("❌ Tencent data fetch failed.")

    print(f"\nTesting Baostock data for {stock_code}...")
    df_baostock = analyzer._try_baostock_data(stock_code, "daily")
    if df_baostock is not None and not df_baostock.empty:
        print("✅ Baostock data fetch successful!")
        print(df_baostock.head())
        print(df_baostock.tail())
    else:
        print("❌ Baostock data fetch failed.")

if __name__ == "__main__":
    test_fallbacks()
