#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型集成预测模块
实现技术指标、机器学习、支撑阻力位三种方法的短期预测
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class MultiModelPredictor:
    """多模型集成预测器"""
    
    def __init__(self, weights=None):
        """
        初始化预测器
        weights: dict, 各模型权重 {'technical': 0.3, 'ml': 0.4, 'support_resistance': 0.3}
        """
        self.weights = weights or {'technical': 0.3, 'ml': 0.4, 'support_resistance': 0.3}
        self.scaler = StandardScaler()
        
    def predict_short_term(self, stock_data, pred_days=5):
        """
        短期预测主函数
        stock_data: DataFrame, 股票历史数据
        pred_days: int, 预测天数
        返回: dict, 包含各模型预测结果和集成结果
        """
        results = {}
        
        try:
            # 方法1: 技术指标预测
            tech_pred = self._technical_indicator_prediction(stock_data, pred_days)
            results['technical'] = tech_pred
            
            # 方法2: 机器学习预测
            ml_pred = self._machine_learning_prediction(stock_data, pred_days)
            results['machine_learning'] = ml_pred
            
            # 方法3: 支撑阻力位预测
            sr_pred = self._support_resistance_prediction(stock_data, pred_days)
            results['support_resistance'] = sr_pred
            
            # 集成预测
            ensemble_pred = self._ensemble_prediction(tech_pred, ml_pred, sr_pred)
            results['ensemble'] = ensemble_pred
            
            # 计算预测信心度
            confidence = self._calculate_confidence(tech_pred, ml_pred, sr_pred)
            results['confidence'] = confidence
            
            return results
            
        except Exception as e:
            print(f"多模型预测失败: {str(e)}")
            return self._fallback_prediction(stock_data, pred_days)
    
    def _technical_indicator_prediction(self, data, pred_days):
        """方法1: 基于技术指标的预测"""
        try:
            # 计算技术指标
            data = data.copy()
            
            # MACD
            ema12 = data['close'].ewm(span=12).mean()
            ema26 = data['close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            macd_hist = macd - signal
            
            # RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 移动平均线
            ma5 = data['close'].rolling(window=5).mean()
            ma20 = data['close'].rolling(window=20).mean()
            
            # 布林带
            bb_middle = data['close'].rolling(window=20).mean()
            bb_std = data['close'].rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            # 获取最新指标值
            latest_close = data['close'].iloc[-1]
            latest_macd = macd.iloc[-1]
            latest_signal = signal.iloc[-1]
            latest_rsi = rsi.iloc[-1]
            latest_ma5 = ma5.iloc[-1]
            latest_ma20 = ma20.iloc[-1]
            latest_bb_upper = bb_upper.iloc[-1]
            latest_bb_lower = bb_lower.iloc[-1]
            
            # 预测逻辑
            predictions = []
            current_price = latest_close
            
            for i in range(pred_days):
                # MACD信号
                macd_signal = 1 if latest_macd > latest_signal else -1
                
                # RSI信号
                if latest_rsi > 70:
                    rsi_signal = -1  # 超买
                elif latest_rsi < 30:
                    rsi_signal = 1   # 超卖
                else:
                    rsi_signal = 0   # 中性
                
                # 均线信号
                ma_signal = 1 if latest_ma5 > latest_ma20 else -1
                
                # 布林带信号
                if current_price > latest_bb_upper:
                    bb_signal = -1  # 接近上轨，可能回调
                elif current_price < latest_bb_lower:
                    bb_signal = 1   # 接近下轨，可能反弹
                else:
                    bb_signal = 0   # 在带内
                
                # 综合信号
                total_signal = (macd_signal * 0.3 + rsi_signal * 0.2 + 
                               ma_signal * 0.3 + bb_signal * 0.2)
                
                # 预测价格变动（保守估计）
                change_rate = total_signal * 0.01  # 最大1%的日变动
                current_price = current_price * (1 + change_rate)
                predictions.append(current_price)
            
            return {
                'prices': predictions,
                'method': 'technical_indicators',
                'signals': {
                    'macd': macd_signal,
                    'rsi': rsi_signal,
                    'ma': ma_signal,
                    'bollinger': bb_signal
                }
            }
            
        except Exception as e:
            print(f"技术指标预测失败: {str(e)}")
            return self._simple_trend_prediction(data, pred_days)
    
    def _machine_learning_prediction(self, data, pred_days):
        """方法2: 机器学习预测"""
        try:
            # 准备特征
            features = []
            targets = []
            window_size = 10  # 使用10天的数据作为特征
            
            # 计算技术指标作为特征
            data = data.copy()
            data['ma5'] = data['close'].rolling(window=5).mean()
            data['ma10'] = data['close'].rolling(window=10).mean()
            data['rsi'] = self._calculate_rsi(data['close'], 14)
            data['volume_ma'] = data['volume'].rolling(window=5).mean()
            
            # 价格变化率
            data['price_change'] = data['close'].pct_change()
            data['volume_change'] = data['volume'].pct_change()
            
            # 构建训练数据
            for i in range(window_size, len(data) - pred_days):
                # 特征：过去window_size天的数据
                feature_row = []
                for j in range(window_size):
                    idx = i - window_size + j
                    feature_row.extend([
                        data['close'].iloc[idx],
                        data['volume'].iloc[idx],
                        data['ma5'].iloc[idx] if not np.isnan(data['ma5'].iloc[idx]) else data['close'].iloc[idx],
                        data['ma10'].iloc[idx] if not np.isnan(data['ma10'].iloc[idx]) else data['close'].iloc[idx],
                        data['rsi'].iloc[idx] if not np.isnan(data['rsi'].iloc[idx]) else 50,
                        data['price_change'].iloc[idx] if not np.isnan(data['price_change'].iloc[idx]) else 0
                    ])
                
                features.append(feature_row)
                # 目标：未来第1天的收盘价
                targets.append(data['close'].iloc[i + 1])
            
            if len(features) < 10:  # 数据不足
                return self._simple_trend_prediction(data, pred_days)
            
            # 训练模型
            X = np.array(features)
            y = np.array(targets)
            
            # 标准化
            X_scaled = self.scaler.fit_transform(X)
            
            # 使用随机森林
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X_scaled, y)
            
            # 预测
            predictions = []
            current_data = data.tail(window_size).copy()
            
            for i in range(pred_days):
                # 准备预测特征
                feature_row = []
                for j in range(window_size):
                    idx = -window_size + j
                    feature_row.extend([
                        current_data['close'].iloc[idx],
                        current_data['volume'].iloc[idx],
                        current_data['ma5'].iloc[idx] if not np.isnan(current_data['ma5'].iloc[idx]) else current_data['close'].iloc[idx],
                        current_data['ma10'].iloc[idx] if not np.isnan(current_data['ma10'].iloc[idx]) else current_data['close'].iloc[idx],
                        current_data['rsi'].iloc[idx] if not np.isnan(current_data['rsi'].iloc[idx]) else 50,
                        current_data['price_change'].iloc[idx] if not np.isnan(current_data['price_change'].iloc[idx]) else 0
                    ])
                
                X_pred = np.array([feature_row])
                X_pred_scaled = self.scaler.transform(X_pred)
                pred_price = model.predict(X_pred_scaled)[0]
                predictions.append(pred_price)
                
                # 更新数据用于下一次预测
                new_row = current_data.iloc[-1].copy()
                new_row['close'] = pred_price
                new_row['price_change'] = (pred_price - current_data['close'].iloc[-1]) / current_data['close'].iloc[-1]
                current_data = pd.concat([current_data.iloc[1:], pd.DataFrame([new_row])], ignore_index=True)
            
            return {
                'prices': predictions,
                'method': 'machine_learning',
                'model_type': 'RandomForest'
            }
            
        except Exception as e:
            print(f"机器学习预测失败: {str(e)}")
            return self._simple_trend_prediction(data, pred_days)
    
    def _support_resistance_prediction(self, data, pred_days):
        """方法3: 支撑阻力位预测"""
        try:
            # 识别支撑阻力位
            highs = data['high'].values
            lows = data['low'].values
            closes = data['close'].values
            
            # 找到局部高点和低点
            resistance_levels = self._find_resistance_levels(highs, closes)
            support_levels = self._find_support_levels(lows, closes)
            
            current_price = closes[-1]
            
            # 找到最近的支撑阻力位
            nearby_resistance = [r for r in resistance_levels if r > current_price]
            nearby_support = [s for s in support_levels if s < current_price]
            
            next_resistance = min(nearby_resistance) if nearby_resistance else current_price * 1.05
            next_support = max(nearby_support) if nearby_support else current_price * 0.95
            
            # 计算趋势
            recent_trend = np.polyfit(range(10), closes[-10:], 1)[0]  # 最近10天的趋势
            
            predictions = []
            current = current_price
            
            for i in range(pred_days):
                # 趋势延续
                trend_price = current + recent_trend
                
                # 支撑阻力位约束
                if trend_price > next_resistance:
                    # 触及阻力位，可能回调
                    predicted = current + (next_resistance - current) * 0.8
                elif trend_price < next_support:
                    # 触及支撑位，可能反弹
                    predicted = current + (next_support - current) * 0.8
                else:
                    # 在支撑阻力位之间，跟随趋势
                    predicted = trend_price
                
                predictions.append(predicted)
                current = predicted
            
            return {
                'prices': predictions,
                'method': 'support_resistance',
                'support_levels': support_levels,
                'resistance_levels': resistance_levels,
                'next_support': next_support,
                'next_resistance': next_resistance
            }
            
        except Exception as e:
            print(f"支撑阻力位预测失败: {str(e)}")
            return self._simple_trend_prediction(data, pred_days)
    
    def _ensemble_prediction(self, tech_pred, ml_pred, sr_pred):
        """集成预测"""
        try:
            tech_prices = tech_pred['prices']
            ml_prices = ml_pred['prices']
            sr_prices = sr_pred['prices']
            
            # 加权平均
            ensemble_prices = []
            for i in range(len(tech_prices)):
                weighted_price = (
                    tech_prices[i] * self.weights['technical'] +
                    ml_prices[i] * self.weights['ml'] +
                    sr_prices[i] * self.weights['support_resistance']
                )
                ensemble_prices.append(weighted_price)
            
            return {
                'prices': ensemble_prices,
                'method': 'ensemble',
                'weights': self.weights
            }
            
        except Exception as e:
            print(f"集成预测失败: {str(e)}")
            # 返回简单平均
            tech_prices = tech_pred.get('prices', [])
            ml_prices = ml_pred.get('prices', [])
            sr_prices = sr_pred.get('prices', [])
            
            if tech_prices and ml_prices and sr_prices:
                ensemble_prices = [(t + m + s) / 3 for t, m, s in zip(tech_prices, ml_prices, sr_prices)]
                return {'prices': ensemble_prices, 'method': 'simple_average'}
            
            return tech_pred  # 返回技术指标预测作为后备
    
    def _calculate_confidence(self, tech_pred, ml_pred, sr_pred):
        """计算预测信心度"""
        try:
            tech_prices = tech_pred['prices']
            ml_prices = ml_pred['prices']
            sr_prices = sr_pred['prices']
            
            # 计算预测一致性
            price_matrix = np.array([tech_prices, ml_prices, sr_prices])
            std_dev = np.std(price_matrix, axis=0)
            mean_prices = np.mean(price_matrix, axis=0)
            
            # 相对标准差作为不确定性指标
            relative_std = std_dev / mean_prices
            confidence = 1 - np.mean(relative_std)  # 标准差越小，信心度越高
            confidence = max(0, min(1, confidence))  # 限制在0-1之间
            
            return {
                'overall_confidence': confidence,
                'price_consistency': 1 - np.mean(relative_std),
                'std_deviation': np.mean(std_dev)
            }
            
        except Exception as e:
            return {'overall_confidence': 0.5, 'error': str(e)}
    
    def _calculate_rsi(self, prices, window=14):
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _find_resistance_levels(self, highs, closes, window=5):
        """找到阻力位"""
        resistance_levels = []
        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i-window:i+window+1]):
                resistance_levels.append(highs[i])
        return sorted(set(resistance_levels), reverse=True)[:5]  # 返回前5个阻力位
    
    def _find_support_levels(self, lows, closes, window=5):
        """找到支撑位"""
        support_levels = []
        for i in range(window, len(lows) - window):
            if lows[i] == min(lows[i-window:i+window+1]):
                support_levels.append(lows[i])
        return sorted(set(support_levels))[:5]  # 返回前5个支撑位
    
    def _simple_trend_prediction(self, data, pred_days):
        """简单趋势预测作为后备方案"""
        closes = data['close'].values
        trend = np.polyfit(range(len(closes)), closes, 1)[0]
        
        predictions = []
        current = closes[-1]
        for i in range(pred_days):
            current += trend
            predictions.append(current)
        
        return {
            'prices': predictions,
            'method': 'simple_trend',
            'trend': trend
        }
    
    def _fallback_prediction(self, data, pred_days):
        """失败时的后备预测"""
        last_price = data['close'].iloc[-1]
        return {
            'technical': {'prices': [last_price] * pred_days, 'method': 'fallback'},
            'machine_learning': {'prices': [last_price] * pred_days, 'method': 'fallback'},
            'support_resistance': {'prices': [last_price] * pred_days, 'method': 'fallback'},
            'ensemble': {'prices': [last_price] * pred_days, 'method': 'fallback'},
            'confidence': {'overall_confidence': 0.3}
        }

# 使用示例
if __name__ == "__main__":
    # 示例数据
    dates = pd.date_range('2025-01-01', periods=100)
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    volumes = np.random.randint(1000000, 5000000, 100)
    
    sample_data = pd.DataFrame({
        'date': dates,
        'open': prices + np.random.randn(100) * 0.1,
        'high': prices + np.abs(np.random.randn(100) * 0.2),
        'low': prices - np.abs(np.random.randn(100) * 0.2),
        'close': prices,
        'volume': volumes
    })
    
    # 测试预测
    predictor = MultiModelPredictor()
    results = predictor.predict_short_term(sample_data, pred_days=5)
    
    print("多模型预测结果:")
    for method, result in results.items():
        if isinstance(result, dict) and 'prices' in result:
            print(f"{method}: {[f'{p:.2f}' for p in result['prices']]}")
        elif method == 'confidence':
            print(f"信心度: {result.get('overall_confidence', 0):.2%}")