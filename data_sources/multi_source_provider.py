#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据源股票数据提供器
支持多种数据源的自动切换和备用机制
"""

import pandas as pd
import numpy as np
import warnings
import time
from datetime import datetime, timedelta
import logging

warnings.filterwarnings('ignore')

class MultiSourceDataProvider:
    """多数据源股票数据提供器"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.sources = {}
        self.source_priority = []
        self._init_sources()
    
    def _init_sources(self):
        """初始化所有可用的数据源"""
        # AkShare (主要数据源)
        try:
            import akshare as ak
            self.sources['akshare'] = AkShareProvider()
            self.source_priority.append('akshare')
            self.log("✅ AkShare数据源加载成功")
        except ImportError:
            self.log("❌ AkShare未安装")
        
        # yfinance (备用数据源)
        try:
            import yfinance as yf
            self.sources['yfinance'] = YFinanceProvider()
            self.source_priority.append('yfinance')
            self.log("✅ yfinance数据源加载成功")
        except ImportError:
            self.log("⚠️ yfinance未安装，建议安装: pip install yfinance")
        
        # TuShare (需要token)
        try:
            import tushare as ts
            # 检查是否有token配置
            token = self._get_tushare_token()
            if token:
                ts.set_token(token)
                self.sources['tushare'] = TuShareProvider()
                self.source_priority.append('tushare')
                self.log("✅ TuShare数据源加载成功")
            else:
                self.log("⚠️ TuShare token未配置")
        except ImportError:
            self.log("⚠️ TuShare未安装，可选安装: pip install tushare")
        
        # Alpha Vantage (需要API key)
        alpha_key = self._get_alpha_vantage_key()
        if alpha_key:
            try:
                self.sources['alphavantage'] = AlphaVantageProvider(alpha_key)
                self.source_priority.append('alphavantage')
                self.log("✅ Alpha Vantage数据源加载成功")
            except Exception as e:
                self.log(f"⚠️ Alpha Vantage加载失败: {e}")
    
    def _get_tushare_token(self):
        """获取TuShare token"""
        import os
        # 从环境变量或配置文件获取
        token = os.environ.get('TUSHARE_TOKEN')
        if not token:
            try:
                with open('config/tushare_token.txt', 'r') as f:
                    token = f.read().strip()
            except:
                pass
        return token
    
    def _get_alpha_vantage_key(self):
        """获取Alpha Vantage API key"""
        import os
        # 从环境变量或配置文件获取
        key = os.environ.get('ALPHA_VANTAGE_KEY')
        if not key:
            try:
                with open('config/alpha_vantage_key.txt', 'r') as f:
                    key = f.read().strip()
            except:
                pass
        return key
    
    def log(self, message):
        """日志记录"""
        if self.logger:
            self.logger.info(message)
        print(f"[DataProvider] {message}")
    
    def get_stock_data(self, code, period='daily', start_date=None, end_date=None):
        """
        获取股票数据，自动尝试多个数据源
        
        Args:
            code: 股票代码
            period: 时间周期 ('daily', '5min', '15min')
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            pandas.DataFrame: 股票数据
        """
        last_error = None
        
        for source_name in self.source_priority:
            if source_name not in self.sources:
                continue
                
            try:
                self.log(f"🔍 尝试使用 {source_name} 获取 {code} 数据...")
                
                source = self.sources[source_name]
                data = source.get_data(code, period, start_date, end_date)
                
                if data is not None and not data.empty:
                    self.log(f"✅ {source_name} 成功获取 {len(data)} 条数据")
                    return self._standardize_data(data)
                else:
                    self.log(f"⚠️ {source_name} 返回空数据")
                    
            except Exception as e:
                last_error = e
                self.log(f"❌ {source_name} 获取失败: {str(e)}")
                # 继续尝试下一个数据源
                continue
        
        # 所有数据源都失败
        error_msg = f"所有数据源都无法获取 {code} 的数据"
        if last_error:
            error_msg += f"，最后错误: {str(last_error)}"
        
        self.log(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    def _standardize_data(self, data):
        """标准化数据格式"""
        # 确保列名统一
        column_mapping = {
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high', 
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '日期': 'timestamps',
            '时间': 'timestamps',
            'Open': 'open',
            'Close': 'close',
            'High': 'high',
            'Low': 'low',
            'Volume': 'volume'
        }
        
        # 重命名列
        for old_name, new_name in column_mapping.items():
            if old_name in data.columns:
                data = data.rename(columns={old_name: new_name})
        
        # 确保时间列存在
        if 'timestamps' not in data.columns:
            if data.index.name in ['date', 'Date', '日期']:
                data['timestamps'] = data.index
            else:
                data['timestamps'] = pd.date_range(
                    start=datetime.now() - timedelta(days=len(data)), 
                    periods=len(data), 
                    freq='D'
                )
        
        # 确保必要的价格列存在
        required_columns = ['open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in data.columns:
                if 'close' in data.columns:
                    data[col] = data['close']  # 用收盘价填充缺失的价格列
        
        # 确保成交量列存在
        if 'volume' not in data.columns:
            data['volume'] = 1000000  # 默认成交量
        
        # 数据类型转换
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        if 'volume' in data.columns:
            data['volume'] = pd.to_numeric(data['volume'], errors='coerce')
        
        # 移除无效数据
        data = data.dropna(subset=['close'])
        
        return data
    
    def get_available_sources(self):
        """获取可用的数据源列表"""
        return list(self.sources.keys())
    
    def test_all_sources(self, test_code='000001'):
        """测试所有数据源的可用性"""
        results = {}
        
        for source_name in self.sources:
            try:
                start_time = time.time()
                data = self.sources[source_name].get_data(test_code, 'daily')
                end_time = time.time()
                
                if data is not None and not data.empty:
                    results[source_name] = {
                        'status': 'success',
                        'data_count': len(data),
                        'response_time': round(end_time - start_time, 2)
                    }
                else:
                    results[source_name] = {
                        'status': 'empty_data',
                        'data_count': 0,
                        'response_time': round(end_time - start_time, 2)
                    }
                    
            except Exception as e:
                results[source_name] = {
                    'status': 'error',
                    'error': str(e),
                    'data_count': 0,
                    'response_time': 0
                }
        
        return results


class BaseDataProvider:
    """数据提供器基类"""
    
    def get_data(self, code, period='daily', start_date=None, end_date=None):
        """获取股票数据的抽象方法"""
        raise NotImplementedError


class AkShareProvider(BaseDataProvider):
    """AkShare数据提供器"""
    
    def __init__(self):
        import akshare as ak
        self.ak = ak
    
    def get_data(self, code, period='daily', start_date=None, end_date=None):
        """使用AkShare获取股票数据"""
        if period == 'daily':
            return self._get_daily_data(code, start_date, end_date)
        elif period in ['5min', '15min']:
            return self._get_minute_data(code, period, start_date, end_date)
        else:
            raise ValueError(f"不支持的时间周期: {period}")
    
    def _get_daily_data(self, code, start_date, end_date):
        """获取日线数据"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        return self.ak.stock_zh_a_hist(
            symbol=code,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )
    
    def _get_minute_data(self, code, period, start_date, end_date):
        """获取分钟级数据"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d') + " 09:30:00"
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d') + " 15:00:00"
        
        return self.ak.stock_zh_a_hist_min_em(
            symbol=code,
            start_date=start_date,
            end_date=end_date,
            period=period.replace('min', ''),
            adjust=''
        )


class YFinanceProvider(BaseDataProvider):
    """Yahoo Finance数据提供器"""
    
    def __init__(self):
        import yfinance as yf
        self.yf = yf
    
    def get_data(self, code, period='daily', start_date=None, end_date=None):
        """使用yfinance获取股票数据"""
        # 转换股票代码格式
        symbol = self._convert_code_format(code)
        
        if period == 'daily':
            interval = '1d'
            period_range = '1y'
        elif period == '5min':
            interval = '5m'
            period_range = '60d'
        elif period == '15min':
            interval = '15m'
            period_range = '60d'
        else:
            raise ValueError(f"不支持的时间周期: {period}")
        
        ticker = self.yf.Ticker(symbol)
        data = ticker.history(period=period_range, interval=interval)
        
        if not data.empty:
            data.reset_index(inplace=True)
            if 'Date' in data.columns:
                data['timestamps'] = data['Date']
            elif 'Datetime' in data.columns:
                data['timestamps'] = data['Datetime']
        
        return data
    
    def _convert_code_format(self, code):
        """转换股票代码格式为yfinance支持的格式"""
        # A股代码转换
        if len(code) == 6 and code.isdigit():
            if code.startswith('6'):
                return f"{code}.SS"  # 上海
            elif code.startswith(('0', '3')):
                return f"{code}.SZ"  # 深圳
        
        # 如果已经带有后缀，直接返回
        if '.' in code:
            return code
        
        # 默认返回原代码
        return code


class TuShareProvider(BaseDataProvider):
    """TuShare数据提供器"""
    
    def __init__(self):
        import tushare as ts
        self.ts = ts
        self.pro = ts.pro_api()
    
    def get_data(self, code, period='daily', start_date=None, end_date=None):
        """使用TuShare获取股票数据"""
        # 转换代码格式
        ts_code = self._convert_code_format(code)
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        if period == 'daily':
            data = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
        else:
            # TuShare分钟数据需要更复杂的处理
            raise NotImplementedError("TuShare分钟数据暂未实现")
        
        if not data.empty:
            # 重命名列
            data = data.rename(columns={
                'trade_date': 'timestamps',
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'vol': 'volume'
            })
            
            # 转换日期格式
            data['timestamps'] = pd.to_datetime(data['timestamps'])
            
            # 按日期排序
            data = data.sort_values('timestamps')
        
        return data
    
    def _convert_code_format(self, code):
        """转换为TuShare代码格式"""
        if len(code) == 6 and code.isdigit():
            if code.startswith('6'):
                return f"{code}.SH"
            elif code.startswith(('0', '3')):
                return f"{code}.SZ"
        return code


class AlphaVantageProvider(BaseDataProvider):
    """Alpha Vantage数据提供器"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_data(self, code, period='daily', start_date=None, end_date=None):
        """使用Alpha Vantage获取股票数据"""
        import requests
        
        # Alpha Vantage主要支持美股，A股支持有限
        symbol = self._convert_code_format(code)
        
        if period == 'daily':
            function = "TIME_SERIES_DAILY"
        elif period == '5min':
            function = "TIME_SERIES_INTRADAY"
            interval = "5min"
        elif period == '15min':
            function = "TIME_SERIES_INTRADAY"
            interval = "15min"
        else:
            raise ValueError(f"不支持的时间周期: {period}")
        
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full'
        }
        
        if period != 'daily':
            params['interval'] = interval
        
        response = requests.get(self.base_url, params=params)
        data_json = response.json()
        
        # 解析数据
        if period == 'daily':
            time_series_key = "Time Series (Daily)"
        else:
            time_series_key = f"Time Series ({interval})"
        
        if time_series_key not in data_json:
            raise Exception(f"Alpha Vantage返回错误: {data_json}")
        
        time_series = data_json[time_series_key]
        
        # 转换为DataFrame
        data_list = []
        for date_str, values in time_series.items():
            row = {
                'timestamps': pd.to_datetime(date_str),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(values['5. volume'])
            }
            data_list.append(row)
        
        data = pd.DataFrame(data_list)
        data = data.sort_values('timestamps')
        
        return data
    
    def _convert_code_format(self, code):
        """转换股票代码格式"""
        # Alpha Vantage主要支持美股
        # A股需要特殊处理或不支持
        return code


# 使用示例
if __name__ == "__main__":
    provider = MultiSourceDataProvider()
    
    # 测试获取数据
    try:
        data = provider.get_stock_data('000001', 'daily')
        print(f"获取数据成功，共 {len(data)} 条记录")
        print(data.head())
    except Exception as e:
        print(f"获取数据失败: {e}")
    
    # 测试所有数据源
    print("\n测试所有数据源:")
    results = provider.test_all_sources()
    for source, result in results.items():
        print(f"{source}: {result}")