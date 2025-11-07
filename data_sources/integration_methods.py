#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kronos系统数据获取模块集成版
将多数据源功能集成到现有的prediction_gui.py中
"""

def create_enhanced_data_methods():
    """
    返回可直接集成到KronosPredictor类中的增强数据获取方法
    """
    
    enhanced_methods = """
    def init_multi_data_sources(self):
        \"\"\"初始化多数据源支持\"\"\"
        self.data_sources = {}
        self.source_priority = []
        
        # AkShare (主要数据源)
        if AKSHARE_AVAILABLE:
            self.data_sources['akshare'] = True
            self.source_priority.append('akshare')
            self.log_message("✅ AkShare数据源可用")
        
        # yfinance (备用数据源)
        try:
            import yfinance as yf
            self.data_sources['yfinance'] = yf
            self.source_priority.append('yfinance')
            self.log_message("✅ yfinance数据源加载成功")
        except ImportError:
            self.log_message("⚠️ yfinance未安装，建议安装: pip install yfinance")
        
        # TuShare (需要token)
        try:
            import tushare as ts
            token = self.get_tushare_token()
            if token:
                ts.set_token(token)
                self.data_sources['tushare'] = ts
                self.source_priority.append('tushare')
                self.log_message("✅ TuShare数据源加载成功")
            else:
                self.log_message("⚠️ TuShare token未配置")
        except ImportError:
            self.log_message("⚠️ TuShare未安装，可选安装: pip install tushare")
        
        # Alpha Vantage (需要API key)
        alpha_key = self.get_alpha_vantage_key()
        if alpha_key:
            self.data_sources['alphavantage'] = alpha_key
            self.source_priority.append('alphavantage')
            self.log_message("✅ Alpha Vantage数据源配置成功")
    
    def get_tushare_token(self):
        \"\"\"获取TuShare token\"\"\"
        import os
        # 从环境变量获取
        token = os.environ.get('TUSHARE_TOKEN')
        if not token:
            try:
                with open('config/tushare_token.txt', 'r') as f:
                    token = f.read().strip()
            except:
                pass
        return token
    
    def get_alpha_vantage_key(self):
        \"\"\"获取Alpha Vantage API key\"\"\"
        import os
        # 从环境变量获取
        key = os.environ.get('ALPHA_VANTAGE_KEY')
        if not key:
            try:
                with open('config/alpha_vantage_key.txt', 'r') as f:
                    key = f.read().strip()
            except:
                pass
        return key
    
    def get_stock_data_enhanced(self, code, chart_type, hist_days, pred_days):
        \"\"\"
        增强版股票数据获取，支持多数据源自动切换
        \"\"\"
        if not hasattr(self, 'data_sources'):
            self.init_multi_data_sources()
        
        # 按优先级尝试各个数据源
        for source_name in self.source_priority:
            try:
                self.log_message(f"🔍 尝试使用 {source_name} 获取 {code} 数据...")
                
                if source_name == 'akshare':
                    return self.get_real_stock_data(code, chart_type, hist_days, pred_days)
                elif source_name == 'yfinance':
                    return self.get_yfinance_data(code, chart_type, hist_days, pred_days)
                elif source_name == 'tushare':
                    return self.get_tushare_data(code, chart_type, hist_days, pred_days)
                elif source_name == 'alphavantage':
                    return self.get_alphavantage_data(code, chart_type, hist_days, pred_days)
                    
            except Exception as e:
                self.log_message(f"❌ {source_name} 获取失败: {str(e)}")
                continue
        
        # 所有数据源都失败
        self.log_message("❌ 所有数据源都无法获取数据")
        return None, None
    
    def get_yfinance_data(self, code, chart_type, hist_days, pred_days):
        \"\"\"使用yfinance获取股票数据\"\"\"
        import yfinance as yf
        
        # 转换股票代码格式
        symbol = self.convert_code_to_yfinance(code)
        
        if chart_type == "daily":
            interval = '1d'
            period = '1y'
        elif chart_type == "5min":
            interval = '5m'
            period = '60d'
        else:
            interval = '15m'
            period = '60d'
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        
        if data.empty:
            raise Exception(f"yfinance未能获取到 {code} 的数据")
        
        # 转换为标准格式
        data.reset_index(inplace=True)
        data = data.rename(columns={
            'Date': 'timestamps' if 'Date' in data.columns else 'timestamps',
            'Datetime': 'timestamps' if 'Datetime' in data.columns else 'timestamps',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # 确保timestamps列存在
        if 'timestamps' not in data.columns and 'Date' in data.columns:
            data['timestamps'] = data['Date']
        elif 'timestamps' not in data.columns and 'Datetime' in data.columns:
            data['timestamps'] = data['Datetime']
        
        return self.process_stock_data(data, chart_type, hist_days, pred_days)
    
    def get_tushare_data(self, code, chart_type, hist_days, pred_days):
        \"\"\"使用TuShare获取股票数据\"\"\"
        import tushare as ts
        from datetime import datetime, timedelta
        
        # 转换代码格式
        ts_code = self.convert_code_to_tushare(code)
        
        # 计算日期范围
        today = datetime.now()
        if chart_type == "daily":
            start_date = (today - timedelta(days=365)).strftime('%Y%m%d')
            end_date = today.strftime('%Y%m%d')
            
            pro = ts.pro_api()
            data = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        else:
            raise NotImplementedError("TuShare分钟数据暂未实现")
        
        if data.empty:
            raise Exception(f"TuShare未能获取到 {code} 的数据")
        
        # 转换为标准格式
        data = data.rename(columns={
            'trade_date': 'timestamps',
            'vol': 'volume'
        })
        
        # 转换日期格式
        data['timestamps'] = pd.to_datetime(data['timestamps'])
        data = data.sort_values('timestamps')
        
        return self.process_stock_data(data, chart_type, hist_days, pred_days)
    
    def get_alphavantage_data(self, code, chart_type, hist_days, pred_days):
        \"\"\"使用Alpha Vantage获取股票数据\"\"\"
        import requests
        
        api_key = self.data_sources['alphavantage']
        base_url = "https://www.alphavantage.co/query"
        
        # 主要支持美股，A股支持有限
        symbol = code  # 可能需要转换格式
        
        if chart_type == "daily":
            function = "TIME_SERIES_DAILY"
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': api_key,
                'outputsize': 'full'
            }
        else:
            function = "TIME_SERIES_INTRADAY"
            interval = "5min" if chart_type == "5min" else "15min"
            params = {
                'function': function,
                'symbol': symbol,
                'interval': interval,
                'apikey': api_key,
                'outputsize': 'full'
            }
        
        response = requests.get(base_url, params=params, timeout=30)
        data_json = response.json()
        
        # 检查错误
        if 'Error Message' in data_json:
            raise Exception(f"Alpha Vantage错误: {data_json['Error Message']}")
        
        if 'Note' in data_json:
            raise Exception(f"Alpha Vantage限制: {data_json['Note']}")
        
        # 解析数据
        if chart_type == "daily":
            time_series_key = "Time Series (Daily)"
        else:
            interval = "5min" if chart_type == "5min" else "15min"
            time_series_key = f"Time Series ({interval})"
        
        if time_series_key not in data_json:
            raise Exception(f"Alpha Vantage返回格式错误: {list(data_json.keys())}")
        
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
        
        if not data_list:
            raise Exception("Alpha Vantage返回空数据")
        
        data = pd.DataFrame(data_list)
        data = data.sort_values('timestamps')
        
        return self.process_stock_data(data, chart_type, hist_days, pred_days)
    
    def convert_code_to_yfinance(self, code):
        \"\"\"转换股票代码为yfinance格式\"\"\"
        # A股代码转换
        if len(code) == 6 and code.isdigit():
            if code.startswith('6'):
                return f"{code}.SS"  # 上海
            elif code.startswith(('0', '3')):
                return f"{code}.SZ"  # 深圳
        
        # 如果已经带有后缀，直接返回
        if '.' in code:
            return code
        
        return code
    
    def convert_code_to_tushare(self, code):
        \"\"\"转换股票代码为TuShare格式\"\"\"
        if len(code) == 6 and code.isdigit():
            if code.startswith('6'):
                return f"{code}.SH"
            elif code.startswith(('0', '3')):
                return f"{code}.SZ"
        return code
    
    def test_data_sources(self):
        \"\"\"测试所有数据源的可用性\"\"\"
        if not hasattr(self, 'data_sources'):
            self.init_multi_data_sources()
        
        test_code = '000001'
        results = {}
        
        for source_name in self.source_priority:
            try:
                self.log_message(f"🧪 测试 {source_name}...")
                start_time = pd.Timestamp.now()
                
                if source_name == 'akshare':
                    data, _ = self.get_real_stock_data(test_code, 'daily', 20, 5)
                elif source_name == 'yfinance':
                    data, _ = self.get_yfinance_data(test_code, 'daily', 20, 5)
                elif source_name == 'tushare':
                    data, _ = self.get_tushare_data(test_code, 'daily', 20, 5)
                elif source_name == 'alphavantage':
                    data, _ = self.get_alphavantage_data(test_code, 'daily', 20, 5)
                
                end_time = pd.Timestamp.now()
                response_time = (end_time - start_time).total_seconds()
                
                if data is not None and len(data) > 0:
                    results[source_name] = {
                        'status': '✅ 成功',
                        'data_count': len(data),
                        'response_time': f"{response_time:.2f}秒"
                    }
                    self.log_message(f"✅ {source_name} 测试成功，获取 {len(data)} 条数据")
                else:
                    results[source_name] = {
                        'status': '⚠️ 空数据',
                        'data_count': 0,
                        'response_time': f"{response_time:.2f}秒"
                    }
                    self.log_message(f"⚠️ {source_name} 返回空数据")
                    
            except Exception as e:
                results[source_name] = {
                    'status': f'❌ 失败: {str(e)[:50]}...',
                    'data_count': 0,
                    'response_time': '0秒'
                }
                self.log_message(f"❌ {source_name} 测试失败: {str(e)}")
        
        # 显示测试结果
        self.log_message("\\n📊 数据源测试结果:")
        for source, result in results.items():
            self.log_message(f"  {source}: {result['status']} ({result['data_count']}条数据, {result['response_time']})")
        
        return results
    """
    
    return enhanced_methods


if __name__ == "__main__":
    print("Kronos数据获取模块集成版")
    print("请将enhanced_methods内容复制到KronosPredictor类中")
    print("\\n使用方法:")
    print("1. 将方法添加到类中")
    print("2. 在__init__方法中调用 self.init_multi_data_sources()")
    print("3. 将 get_stock_data_simple 方法替换为 get_stock_data_enhanced")
    print("4. 可选：添加数据源测试按钮调用 self.test_data_sources()")