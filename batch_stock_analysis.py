#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量股票分析工具
从CSV文件读取股票代码列表，批量进行股票预测分析并保存结果
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置控制台编码
import locale
if sys.platform.startswith('win'):
    try:
        import codecs
        # 尝试设置UTF-8编码
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        try:
            # 备用方案
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
        except:
            # 如果都失败，至少确保不会崩溃
            pass

# 添加模型路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'model'))

from model.multi_model_predictor import MultiModelPredictor
from model.kronos import KronosPredictor, Kronos, KronosTokenizer
import torch

class BatchStockAnalyzer:
    """批量股票分析器"""
    
    def __init__(self, use_kronos_model=False, model_path=None):
        """
        初始化分析器
        
        Args:
            use_kronos_model: bool, 是否使用Kronos深度学习模型
            model_path: str, Kronos模型路径
        """
        self.use_kronos_model = use_kronos_model
        self.model_path = model_path
        
        # 初始化多模型预测器
        self.multi_predictor = MultiModelPredictor()
        
        # 如果使用Kronos模型，初始化相关组件
        self.kronos_predictor = None
        if use_kronos_model and model_path:
            self._init_kronos_model()
    
    def format_stock_code(self, code):
        """确保股票代码为完整的6位格式"""
        if isinstance(code, str) and code.isdigit():
            return code.zfill(6)
        return str(code)
    
    def _init_kronos_model(self):
        """初始化Kronos模型"""
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # 这里需要根据实际模型参数进行配置
            # 示例参数，实际使用时需要根据训练的模型调整
            model_config = {
                's1_bits': 8,
                's2_bits': 8,
                'n_layers': 6,
                'd_model': 512,
                'n_heads': 8,
                'ff_dim': 2048,
                'ffn_dropout_p': 0.1,
                'attn_dropout_p': 0.1,
                'resid_dropout_p': 0.1,
                'token_dropout_p': 0.1,
                'learn_te': True
            }
            
            tokenizer_config = {
                'd_in': 6,  # open, high, low, close, volume, amount
                'd_model': 512,
                'n_heads': 8,
                'ff_dim': 2048,
                'n_enc_layers': 4,
                'n_dec_layers': 4,
                'ffn_dropout_p': 0.1,
                'attn_dropout_p': 0.1,
                'resid_dropout_p': 0.1,
                's1_bits': 8,
                's2_bits': 8,
                'beta': 1.0,
                'gamma0': 1.0,
                'gamma': 1.0,
                'zeta': 1.0,
                'group_size': 1
            }
            
            # 如果模型文件存在，加载预训练模型
            if os.path.exists(self.model_path):
                model = Kronos.from_pretrained(self.model_path)
                tokenizer = KronosTokenizer.from_pretrained(self.model_path)
            else:
                # 否则创建新模型
                model = Kronos(**model_config)
                tokenizer = KronosTokenizer(**tokenizer_config)
            
            self.kronos_predictor = KronosPredictor(
                model=model,
                tokenizer=tokenizer,
                device=device
            )
            print(f"Kronos模型初始化成功，使用设备: {device}")
            
        except Exception as e:
            print(f"Kronos模型初始化失败: {str(e)}")
            print("将仅使用多模型预测器")
            self.use_kronos_model = False
    
    def load_stock_codes_from_csv(self, csv_file):
        """
        从CSV文件加载股票代码列表
        
        Args:
            csv_file: str, CSV文件路径
            
        Returns:
            list: 股票代码列表
        """
        try:
            # 先尝试读取文件来判断是否有表头
            df_test = pd.read_csv(csv_file, encoding='utf-8', nrows=1)
            first_row_value = str(df_test.iloc[0, 0]).strip()
            
            # 判断第一行是否为股票代码（数字）
            has_header = True
            if first_row_value.replace('.', '').isdigit() or df_test.columns[0].isdigit():
                # 第一行是数字，说明没有表头
                has_header = False
            
            # 根据是否有表头来读取文件
            if has_header:
                df = pd.read_csv(csv_file, encoding='utf-8')
            else:
                df = pd.read_csv(csv_file, encoding='utf-8', header=None, names=['stock_code'])
                print("检测到CSV文件没有表头，自动处理为股票代码列")
            
            # 尝试识别股票代码列
            stock_code_columns = ['股票代码', 'stock_code', 'code', '代码', 'symbol']
            stock_code_col = None
            
            for col in stock_code_columns:
                if col in df.columns:
                    stock_code_col = col
                    break
            
            if stock_code_col is None:
                # 如果没找到明确的股票代码列，使用第一列
                stock_code_col = df.columns[0]
                if has_header:
                    print(f"未找到明确的股票代码列，使用第一列: {stock_code_col}")
            
            stock_codes = df[stock_code_col].astype(str).tolist()
            
            # 清理股票代码（去除空格、转换格式等）
            cleaned_codes = []
            for code in stock_codes:
                code = str(code).strip()
                if code and code != 'nan':
                    # 处理不同格式的股票代码
                    if '.' in code:
                        # 处理带后缀的股票代码（如 000001.SZ）
                        code = code.split('.')[0]
                    
                    # 确保是数字
                    if code.isdigit():
                        # 自动补齐前导零到6位
                        formatted_code = code.zfill(6)
                        cleaned_codes.append(formatted_code)
                        if len(code) < 6:
                            print(f"  股票代码格式化: {code} -> {formatted_code}")
                    else:
                        print(f"  跳过无效代码: {code}")
            
            print(f"从 {csv_file} 加载了 {len(cleaned_codes)} 个有效股票代码")
            return cleaned_codes
            
        except Exception as e:
            print(f"加载股票代码失败: {str(e)}")
            return []
    
    def load_historical_data(self, stock_code, data_dir="data", timeframe="daily"):
        """
        在线获取股票历史数据（不使用本地缓存）
        
        Args:
            stock_code: str, 股票代码
            data_dir: str, 数据目录（保留参数以保持接口兼容性，但不使用）
            timeframe: str, 时间框架 ("daily", "15min", "5min")
            
        Returns:
            pd.DataFrame: 历史数据，如果失败返回None
        """
        print(f"开始在线获取股票 {stock_code} 的历史数据...")
        
        # 首先尝试使用AkShare获取A股数据
        akshare_df = self._try_akshare_data(stock_code, timeframe)
        if akshare_df is not None:
            return akshare_df
        
        # 如果AkShare失败，尝试使用yfinance
        yfinance_df = self._try_yfinance_data(stock_code, timeframe)
        if yfinance_df is not None:
            return yfinance_df
        
        # 所有数据源都失败
        print(f"❌ 无法从任何数据源获取股票 {stock_code} 的历史数据")
        print(f"   请检查：1)网络连接 2)股票代码是否正确 3)股票是否已退市")
        return None
    
    def _try_akshare_data(self, stock_code, timeframe):
        """尝试使用AkShare获取数据"""
        try:
            import akshare as ak
            print(f"  🔍 尝试使用 AkShare 获取 {stock_code} 的数据...")
            
            # 计算日期范围
            from datetime import datetime, timedelta
            today = datetime.now()
            
            if timeframe == "daily":
                start_date = (today - timedelta(days=365)).strftime('%Y%m%d')
                end_date = today.strftime('%Y%m%d')
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period='daily',
                    start_date=start_date,
                    end_date=end_date,
                    adjust=""
                )
            elif timeframe == "5min":
                start_date = (today - timedelta(days=3)).strftime('%Y%m%d')
                end_date = today.strftime('%Y%m%d')
                df = ak.stock_zh_a_hist_min_em(
                    symbol=stock_code,
                    start_date=start_date + " 09:30:00",
                    end_date=end_date + " 15:00:00",
                    period='5',
                    adjust=''
                )
            elif timeframe == "15min":
                start_date = (today - timedelta(days=7)).strftime('%Y%m%d')
                end_date = today.strftime('%Y%m%d')
                df = ak.stock_zh_a_hist_min_em(
                    symbol=stock_code,
                    start_date=start_date + " 09:30:00",
                    end_date=end_date + " 15:00:00",
                    period='15',
                    adjust=''
                )
            else:
                return None
            
            if df is None or df.empty:
                print(f"  ⚠️ AkShare 返回空数据")
                return None
            
            # 规范化列名
            rename_map = {
                '开盘': 'open',
                '收盘': 'close', 
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '日期': 'timestamps',
                '时间': 'timestamps'
            }
            df = df.rename(columns=rename_map)
            
            # 处理时间列
            if 'timestamps' in df.columns:
                df['timestamps'] = pd.to_datetime(df['timestamps'])
            else:
                df['timestamps'] = df.index
            
            # 添加缺失的amount列
            if 'amount' not in df.columns and 'volume' in df.columns:
                df['amount'] = df['volume'] * df[['open', 'high', 'low', 'close']].mean(axis=1)
            
            print(f"  ✅ AkShare 成功获取 {len(df)} 条数据")
            return df
            
        except ImportError:
            print(f"  ⚠️ AkShare 未安装，跳过")
            return None
        except Exception as e:
            print(f"  ❌ AkShare 获取失败: {str(e)}")
            return None
    
    def _try_yfinance_data(self, stock_code, timeframe):
        """尝试使用yfinance获取数据"""
        try:
            import yfinance as yf
            print(f"  🔍 尝试使用 yfinance 获取 {stock_code} 的数据...")
            
            # 尝试常见市场后缀
            variants = [f"{stock_code}.SS", f"{stock_code}.SZ", f"{stock_code}.HK", stock_code]
            
            for sym in variants:
                try:
                    if timeframe == 'daily':
                        data = yf.download(sym, period='1y', interval='1d', progress=False)
                    elif timeframe == '15min':
                        data = yf.download(sym, period='60d', interval='15m', progress=False)
                    elif timeframe == '5min':
                        data = yf.download(sym, period='60d', interval='5m', progress=False)
                    else:
                        data = yf.download(sym, period='1y', interval='1d', progress=False)

                    if data is not None and (not data.empty) and len(data) >= 5:
                        # 规范化列名和数据格式
                        data = data.reset_index()
                        col_map = {
                            'Date': 'timestamps', 
                            'Datetime': 'timestamps', 
                            'Open': 'open', 
                            'High': 'high', 
                            'Low': 'low', 
                            'Close': 'close', 
                            'Volume': 'volume'
                        }
                        for old, new in col_map.items():
                            if old in data.columns:
                                data = data.rename(columns={old: new})

                        if 'timestamps' not in data.columns:
                            data['timestamps'] = data.index

                        # 确保时间戳为datetime
                        data['timestamps'] = pd.to_datetime(data['timestamps'])

                        # 添加amount列
                        if 'amount' not in data.columns and 'volume' in data.columns:
                            data['amount'] = data['volume'] * data[['open', 'high', 'low', 'close']].mean(axis=1)

                        print(f"  ✅ yfinance 成功获取 {sym} 的数据，共 {len(data)} 条")
                        return data
                        
                except Exception:
                    continue
            
            print(f"  ❌ yfinance 所有格式都无法获取数据")
            return None
            
        except ImportError:
            print(f"  ⚠️ yfinance 未安装，跳过")
            return None
        except Exception as e:
            print(f"  ❌ yfinance 获取失败: {str(e)}")
            return None
    
    def predict_single_stock(self, stock_code, data_dir="data", timeframe="daily", pred_days=5):
        """
        对单个股票进行预测
        
        Args:
            stock_code: str, 股票代码
            data_dir: str, 数据目录
            timeframe: str, 时间框架
            pred_days: int, 预测天数
            
        Returns:
            dict: 预测结果
        """
        print(f"\n开始分析股票: {stock_code}")
        
        # 在线获取历史数据
        df = self.load_historical_data(stock_code, data_dir, timeframe)
        if df is None:
            return {
                'stock_code': stock_code,
                'timeframe': timeframe,
                'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'historical_data_points': 0,
                'pred_days': pred_days,
                'error': f'无法从网络获取股票 {stock_code} 的历史数据，请检查网络连接或股票代码是否正确'
            }
        
        results = {
            'stock_code': stock_code,
            'timeframe': timeframe,
            'prediction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'historical_data_points': len(df),
            'pred_days': pred_days
        }
        
        try:
            # 使用多模型预测器
            multi_results = self.multi_predictor.predict_short_term(df, pred_days)
            results['multi_model'] = multi_results
            
            # 如果启用了Kronos模型
            if self.use_kronos_model and self.kronos_predictor:
                try:
                    # 准备Kronos模型需要的数据格式
                    if 'timestamps' in df.columns:
                        x_timestamp = pd.to_datetime(df['timestamps'])
                        
                        # 生成未来时间戳
                        if timeframe == "daily":
                            freq = 'D'
                        elif timeframe == "15min":
                            freq = '15T'
                        elif timeframe == "5min":
                            freq = '5T'
                        else:
                            freq = 'D'
                        
                        last_time = x_timestamp.iloc[-1]
                        y_timestamp = pd.date_range(
                            start=last_time + pd.Timedelta(freq), 
                            periods=pred_days, 
                            freq=freq
                        )
                        
                        # 使用Kronos预测
                        kronos_result = self.kronos_predictor.predict(
                            df=df,
                            x_timestamp=x_timestamp,
                            y_timestamp=y_timestamp,
                            pred_len=pred_days,
                            T=1.0,
                            top_k=0,
                            top_p=0.9,
                            sample_count=3,
                            verbose=False
                        )
                        
                        results['kronos_model'] = {
                            'prediction_df': kronos_result,
                            'method': 'kronos_deep_learning'
                        }
                        
                except Exception as e:
                    print(f"Kronos模型预测失败: {str(e)}")
                    results['kronos_model'] = {'error': str(e)}
            
            # 计算综合预测（如果有多个模型结果）
            if 'ensemble' in multi_results:
                ensemble_prices = multi_results['ensemble']['prices']
                last_price = df['close'].iloc[-1]
                
                results['summary'] = {
                    'current_price': last_price,
                    'predicted_prices': ensemble_prices,
                    'price_changes': [p - last_price for p in ensemble_prices],
                    'price_change_pcts': [(p - last_price) / last_price * 100 for p in ensemble_prices],
                    'confidence': multi_results.get('confidence', {}).get('overall_confidence', 0.5)
                }
                
                # 🆕 计算交易建议信号
                try:
                    trading_signal = self.calculate_trading_recommendation(df, ensemble_prices)
                    results['trading_signal'] = trading_signal
                except Exception as e:
                    print(f"计算交易建议失败: {str(e)}")
                    results['trading_signal'] = {
                        'recommendation': '观望',
                        'confidence': '未知',
                        'score': 0,
                        'error': str(e)
                    }
            
            print(f"股票 {stock_code} 分析完成")
            return results
            
        except Exception as e:
            print(f"股票 {stock_code} 预测过程中出错: {str(e)}")
            results['error'] = str(e)
            return results
    
    def batch_analyze(self, stock_codes, data_dir="data", timeframe="daily", pred_days=5, output_dir="analysis_results"):
        """
        批量分析股票
        
        Args:
            stock_codes: list, 股票代码列表
            data_dir: str, 数据目录
            timeframe: str, 时间框架
            pred_days: int, 预测天数
            output_dir: str, 输出目录
            
        Returns:
            dict: 批量分析结果
        """
        print(f"开始批量分析 {len(stock_codes)} 只股票...")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        batch_results = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stocks': len(stock_codes),
            'successful_predictions': 0,
            'failed_predictions': 0,
            'timeframe': timeframe,
            'pred_days': pred_days,
            'results': []
        }
        
        # 逐个分析股票
        for i, stock_code in enumerate(stock_codes, 1):
            print(f"\n进度: {i}/{len(stock_codes)}")
            
            result = self.predict_single_stock(stock_code, data_dir, timeframe, pred_days)
            
            if result and 'error' not in result:
                batch_results['successful_predictions'] += 1
                
                # 保存单个股票的详细结果
                stock_output_file = os.path.join(output_dir, f"{stock_code}_analysis_{timeframe}.json")
                try:
                    import json
                    
                    # 处理DataFrame对象以便JSON序列化
                    json_result = result.copy()
                    if 'kronos_model' in json_result and 'prediction_df' in json_result['kronos_model']:
                        df = json_result['kronos_model']['prediction_df']
                        json_result['kronos_model']['prediction_data'] = {
                            'index': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                            'data': df.to_dict('records')
                        }
                        del json_result['kronos_model']['prediction_df']
                    
                    with open(stock_output_file, 'w', encoding='utf-8') as f:
                        json.dump(json_result, f, ensure_ascii=False, indent=2, default=str)
                    
                except Exception as e:
                    print(f"保存股票 {stock_code} 详细结果失败: {str(e)}")
            else:
                batch_results['failed_predictions'] += 1
            
            batch_results['results'].append(result)
        
        # 保存批量分析总结
        self._save_batch_summary(batch_results, output_dir)
        
        print(f"\n批量分析完成!")
        print(f"成功: {batch_results['successful_predictions']} 只股票")
        print(f"失败: {batch_results['failed_predictions']} 只股票")
        print(f"结果保存在: {output_dir}")
        
        return batch_results
    
    def _save_batch_summary(self, batch_results, output_dir):
        """保存批量分析总结"""
        try:
            # 创建总结DataFrame
            summary_data = []
            
            for result in batch_results['results']:
                if result is None:
                    continue
                    
                row = {
                    '股票代码': self.format_stock_code(result['stock_code']),  # 🆕 确保6位格式
                    '数据点数': result.get('historical_data_points', 0),
                    '预测状态': '成功' if 'error' not in result else '失败',
                    '错误信息': result.get('error', ''),
                }
                
                if 'summary' in result:
                    summary = result['summary']
                    row.update({
                        '当前价格': round(summary['current_price'], 2),
                        '预测1天': round(summary['predicted_prices'][0], 2) if summary['predicted_prices'] else '',
                        '预测涨跌幅(%)': round(summary['price_change_pcts'][0], 2) if summary['price_change_pcts'] else '',
                        '信心度': round(summary['confidence'], 2),
                    })
                    
                    # 🆕 添加交易建议
                    if 'trading_signal' in result:
                        trading = result['trading_signal']
                        row.update({
                            '建议': trading.get('recommendation', '观望'),
                            '建议信心度': trading.get('confidence', '未知'),
                            '建议评分': trading.get('score', 0)
                        })
                    else:
                        row.update({
                            '建议': '未计算',
                            '建议信心度': '未知',
                            '建议评分': 0
                        })
                else:
                    # 失败的股票填充空值
                    row.update({
                        '当前价格': '',
                        '预测1天': '',
                        '预测涨跌幅(%)': '',
                        '信心度': '',
                        '建议': '失败',
                        '建议信心度': '未知',
                        '建议评分': 0
                    })
                
                summary_data.append(row)
            
            # 保存总结CSV
            summary_df = pd.DataFrame(summary_data)
            summary_file = os.path.join(output_dir, f"batch_analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
            
            # 保存详细JSON
            detail_file = os.path.join(output_dir, f"batch_analysis_detail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # 处理不可序列化的对象
            import json
            json_results = batch_results.copy()
            for result in json_results['results']:
                if result and 'kronos_model' in result and 'prediction_df' in result['kronos_model']:
                    df = result['kronos_model']['prediction_df']
                    result['kronos_model']['prediction_data'] = {
                        'index': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        'data': df.to_dict('records')
                    }
                    del result['kronos_model']['prediction_df']
            
            with open(detail_file, 'w', encoding='utf-8') as f:
                json.dump(json_results, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"总结报告保存至: {summary_file}")
            print(f"详细结果保存至: {detail_file}")
            
        except Exception as e:
            print(f"保存总结报告失败: {str(e)}")

    def calculate_kdj(self, data, n=9, m1=3, m2=3):
        """
        计算KDJ随机指标
        参数：
        - data: 包含high, low, close列的DataFrame  
        - n: RSV计算周期，默认9
        - m1: K值平滑因子，默认3
        - m2: D值平滑因子，默认3
        
        返回：添加了K、D、J列的DataFrame
        """
        try:
            data = data.copy()
            if len(data) < n:
                # 数据不足时，返回中性值
                data['RSV'] = 50.0
                data['K'] = 50.0  
                data['D'] = 50.0
                data['J'] = 50.0
                return data
            
            # 计算RSV (Raw Stochastic Value)
            # RSV = (收盘价 - n日内最低价) / (n日内最高价 - n日内最低价) * 100
            data['lowest_low'] = data['low'].rolling(window=n).min()
            data['highest_high'] = data['high'].rolling(window=n).max()
            
            # 避免除零错误
            price_range = data['highest_high'] - data['lowest_low']
            price_range = price_range.replace(0, 1e-8)  # 将0替换为很小的数值
            
            data['RSV'] = ((data['close'] - data['lowest_low']) / price_range * 100).fillna(50.0)
            
            # 初始化K、D值
            data['K'] = 50.0  # K值初始值50
            data['D'] = 50.0  # D值初始值50
            
            # 计算K值 (K值 = 2/3 * 前一日K值 + 1/3 * 当日RSV)
            # 等价于 K = (m1-1)/m1 * 前K + 1/m1 * RSV，其中m1=3
            alpha_k = 1.0 / m1  # 平滑因子
            
            for i in range(1, len(data)):
                if pd.notna(data['RSV'].iloc[i]):
                    data.iloc[i, data.columns.get_loc('K')] = (
                        (1 - alpha_k) * data['K'].iloc[i-1] + alpha_k * data['RSV'].iloc[i]
                    )
                else:
                    data.iloc[i, data.columns.get_loc('K')] = data['K'].iloc[i-1]
            
            # 计算D值 (D值 = 2/3 * 前一日D值 + 1/3 * 当日K值)
            alpha_d = 1.0 / m2  # 平滑因子
            
            for i in range(1, len(data)):
                if pd.notna(data['K'].iloc[i]):
                    data.iloc[i, data.columns.get_loc('D')] = (
                        (1 - alpha_d) * data['D'].iloc[i-1] + alpha_d * data['K'].iloc[i]
                    )
                else:
                    data.iloc[i, data.columns.get_loc('D')] = data['D'].iloc[i-1]
            
            # 计算J值 (J = 3K - 2D)
            data['J'] = 3 * data['K'] - 2 * data['D']
            
            # 清理临时列
            data = data.drop(columns=['lowest_low', 'highest_high'], errors='ignore')
            
            # 确保数值在合理范围内
            for col in ['K', 'D', 'J']:
                data[col] = data[col].clip(0, 100)  # KDJ值通常在0-100之间
            
            return data
            
        except Exception as e:
            print(f"⚠️ KDJ计算失败: {str(e)}")
            # 失败时返回中性值
            for col in ['RSV', 'K', 'D', 'J']:
                if col not in data.columns:
                    data[col] = 50.0
            return data

    def calculate_atr(self, data, period=14):
        """
        计算ATR (Average True Range) 平均真实范围
        参数：
        - data: 包含high, low, close列的DataFrame
        - period: ATR计算周期，默认14
        
        返回：添加了ATR列的DataFrame
        """
        try:
            data = data.copy()
            if len(data) < 2:
                data['ATR'] = data['close'] * 0.02  # 默认2%作为ATR
                return data
            
            # 计算True Range (TR)
            # TR = MAX(H-L, ABS(H-PC), ABS(L-PC))
            # 其中：H=最高价, L=最低价, PC=前收盘价
            
            data['prev_close'] = data['close'].shift(1)
            
            # 三个候选值
            data['tr1'] = data['high'] - data['low']  # 当日高低价差
            data['tr2'] = abs(data['high'] - data['prev_close'])  # 当日最高价与前日收盘价差的绝对值
            data['tr3'] = abs(data['low'] - data['prev_close'])   # 当日最低价与前日收盘价差的绝对值
            
            # True Range = 三者的最大值
            data['TR'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # 第一天的ATR = 第一天的TR
            data['ATR'] = data['TR']
            
            # 从第二天开始，ATR = (前一天ATR * (period-1) + 当天TR) / period
            for i in range(1, len(data)):
                if pd.notna(data['TR'].iloc[i]) and pd.notna(data['ATR'].iloc[i-1]):
                    data.iloc[i, data.columns.get_loc('ATR')] = (
                        (data['ATR'].iloc[i-1] * (period - 1) + data['TR'].iloc[i]) / period
                    )
                else:
                    data.iloc[i, data.columns.get_loc('ATR')] = data['ATR'].iloc[i-1]
            
            # 清理临时列
            data = data.drop(columns=['prev_close', 'tr1', 'tr2', 'tr3', 'TR'], errors='ignore')
            
            return data
            
        except Exception as e:
            print(f"⚠️ ATR计算失败: {str(e)}")
            # 失败时返回默认值
            if 'ATR' not in data.columns:
                data['ATR'] = data['close'] * 0.02
            return data

    def calculate_trading_recommendation(self, historical_data, predicted_prices):
        """
        计算交易建议（基于与单股预测相同的算法）
        
        Args:
            historical_data: DataFrame，历史数据
            predicted_prices: list，预测价格列表
            
        Returns:
            dict: 包含交易建议的字典
        """
        try:
            current_price = historical_data['close'].iloc[-1]
            
            # 计算预测趋势
            if len(predicted_prices) >= 2:
                pred_start = predicted_prices[0]
                pred_end = predicted_prices[-1]
                if pred_start > 0:
                    pred_trend = (pred_end - pred_start) / pred_start * 100
                else:
                    pred_trend = 0
            else:
                pred_trend = 0
            
            # 计算技术指标
            data_with_indicators = historical_data.copy()
            data_with_indicators = self.calculate_kdj(data_with_indicators, n=9, m1=3, m2=3)
            data_with_indicators = self.calculate_atr(data_with_indicators, period=14)
            
            # 获取最新KDJ值
            current_k = data_with_indicators['K'].iloc[-1] if len(data_with_indicators) > 0 else 50
            current_d = data_with_indicators['D'].iloc[-1] if len(data_with_indicators) > 0 else 50
            current_j = data_with_indicators['J'].iloc[-1] if len(data_with_indicators) > 0 else 50
            
            # KDJ信号分析
            kdj_score = 0
            
            if current_k < 20 and current_d < 20:
                kdj_score = 2  # 强烈超卖
            elif current_k < 30 and current_d < 30:
                kdj_score = 1  # 超卖
            elif current_k > 80 and current_d > 80:
                kdj_score = -2  # 强烈超买
            elif current_k > 70 and current_d > 70:
                kdj_score = -1  # 超买
            else:
                kdj_score = 0  # 中性
            
            # KDJ金叉死叉分析
            if len(data_with_indicators) >= 2:
                prev_k = data_with_indicators['K'].iloc[-2]
                prev_d = data_with_indicators['D'].iloc[-2]
                
                if prev_k <= prev_d and current_k > current_d:
                    kdj_score += 1  # 金叉
                elif prev_k >= prev_d and current_k < current_d:
                    kdj_score -= 1  # 死叉
            
            # J值极端情况
            if current_j < 10:
                kdj_score += 1  # J值极度超卖
            elif current_j > 90:
                kdj_score -= 1  # J值极度超买
            
            # 简化的MACD计算
            macd_score = 0
            if len(historical_data) >= 26:
                prices = historical_data['close']
                ema12 = prices.ewm(span=12).mean()
                ema26 = prices.ewm(span=26).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9).mean()
                
                current_macd = macd_line.iloc[-1]
                current_signal = signal_line.iloc[-1]
                
                # MACD信号判断
                if len(macd_line) >= 2:
                    prev_macd = macd_line.iloc[-2]
                    prev_signal = signal_line.iloc[-2]
                    
                    if prev_macd <= prev_signal and current_macd > current_signal:
                        macd_score = 2  # MACD金叉
                    elif prev_macd >= prev_signal and current_macd < current_signal:
                        macd_score = -2  # MACD死叉
                    elif current_macd > 0:
                        macd_score = 1  # MACD多头
                    elif current_macd < 0:
                        macd_score = -1  # MACD空头
            
            # 趋势评分
            trend_score = 0
            if pred_trend > 2:
                trend_score = 2  # 强势上涨
            elif pred_trend > 0.5:
                trend_score = 1  # 温和上涨
            elif pred_trend > -0.5:
                trend_score = 0  # 横盘
            elif pred_trend > -2:
                trend_score = -1  # 温和下跌
            else:
                trend_score = -2  # 下跌
            
            # 综合评分
            total_score = macd_score + trend_score + kdj_score
            
            # 生成建议
            if total_score >= 4:
                recommendation = "强烈买入"
                confidence = "极高"
            elif total_score >= 2:
                recommendation = "买入"
                confidence = "较高"
            elif total_score >= 0:
                recommendation = "少量买入"
                confidence = "中等"
            elif total_score >= -1:
                recommendation = "观望"
                confidence = "谨慎"
            elif total_score >= -3:
                recommendation = "少量卖出"
                confidence = "中等"
            else:
                recommendation = "强烈卖出"
                confidence = "极高"
            
            return {
                'recommendation': recommendation,
                'confidence': confidence,
                'score': total_score,
                'details': {
                    'kdj_score': kdj_score,
                    'macd_score': macd_score,
                    'trend_score': trend_score,
                    'pred_trend': pred_trend,
                    'current_k': current_k,
                    'current_d': current_d,
                    'current_j': current_j
                }
            }
            
        except Exception as e:
            print(f"计算交易建议失败: {str(e)}")
            return {
                'recommendation': '观望',
                'confidence': '未知',
                'score': 0,
                'error': str(e)
            }


def main():
    """主函数 - 示例用法"""
    
    # 示例：从CSV文件读取股票代码并批量分析
    
    # 1. 创建示例股票代码CSV文件
    sample_stocks = ['000001', '002174', '002497', '002624', '002878', 
                    '600326', '600498', '600977', '601606', '603936', '688981']
    
    sample_df = pd.DataFrame({
        '股票代码': sample_stocks,
        '股票名称': [f'股票{code}' for code in sample_stocks]
    })
    
    sample_csv = 'sample_stock_list.csv'
    sample_df.to_csv(sample_csv, index=False, encoding='utf-8-sig')
    print(f"创建示例股票列表文件: {sample_csv}")
    
    # 2. 初始化分析器
    analyzer = BatchStockAnalyzer(
        use_kronos_model=False,  # 设为True如果要使用Kronos模型
        model_path=None
    )
    
    # 3. 从CSV加载股票代码
    stock_codes = analyzer.load_stock_codes_from_csv(sample_csv)
    
    if not stock_codes:
        print("未能加载股票代码，退出程序")
        return
    
    # 4. 批量分析
    results = analyzer.batch_analyze(
        stock_codes=stock_codes,
        data_dir="data",
        timeframe="daily",
        pred_days=5,
        output_dir="analysis_results"
    )
    
    print("\n批量分析完成!")
    print(f"处理了 {results['total_stocks']} 只股票")
    print(f"成功: {results['successful_predictions']} 只")
    print(f"失败: {results['failed_predictions']} 只")


if __name__ == "__main__":
    main()