#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端报告生成器 - 扩展现有batch_stock_analysis的输出能力
生成可部署到Vercel的静态HTML文件，包含预计算的预测数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from batch_stock_analysis import BatchStockAnalyzer
import json
from datetime import datetime
from pathlib import Path

class MobileReportBuilder:
    """构建移动端静态报告"""
    
    def __init__(self):
        self.analyzer = BatchStockAnalyzer(use_kronos_model=False)
        self.reports_dir = Path('mobile_reports')
        self.reports_dir.mkdir(exist_ok=True)
    
    def build_stock_report(self, ticker_code, period_type='daily', forecast_steps=5):
        """为单个股票生成移动端HTML报告"""
        
        print(f"正在为 {ticker_code} 生成移动端报告...")
        
        # 使用现有的export_mobile_json方法获取数据
        prediction_data = self.analyzer.export_mobile_json(ticker_code, period_type, forecast_steps)
        
        if prediction_data.get('status') == 'error':
            print(f"  错误: {prediction_data.get('message')}")
            return None
        
        # 生成HTML内容
        html_content = self._generate_mobile_html(prediction_data, ticker_code)
        
        # 保存文件
        output_filename = f"{ticker_code}_{period_type}_mobile.html"
        output_path = self.reports_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  报告已生成: {output_path}")
        return str(output_path)
    
    def _generate_mobile_html(self, data, ticker):
        """生成移动优化的HTML内容"""
        
        # 提取数据
        current = data.get('current_price', 0)
        predictions = data.get('predictions', [])
        recommendation = data.get('recommendation', {})
        confidence = data.get('model_confidence', 0)
        
        # 计算涨跌趋势
        if predictions:
            final_price = predictions[-1].get('price', current)
            total_change_pct = predictions[-1].get('change_percent', 0)
            trend_color = '#e74c3c' if total_change_pct < 0 else '#27ae60'
            trend_symbol = '↓' if total_change_pct < 0 else '↑'
        else:
            final_price = current
            total_change_pct = 0
            trend_color = '#95a5a6'
            trend_symbol = '→'
        
        # 构建预测卡片HTML
        prediction_cards_html = ""
        for pred in predictions:
            step_num = pred.get('period', 0)
            price_val = pred.get('price', 0)
            change_val = pred.get('change', 0)
            change_pct_val = pred.get('change_percent', 0)
            
            card_bg = 'rgba(231, 76, 60, 0.1)' if change_pct_val < 0 else 'rgba(39, 174, 96, 0.1)'
            arrow = '↓' if change_pct_val < 0 else '↑'
            
            prediction_cards_html += f"""
            <div class="pred-card" style="background: {card_bg};">
                <div class="pred-step">第{step_num}期</div>
                <div class="pred-price">¥{price_val}</div>
                <div class="pred-change">{arrow} {change_val:+.2f} ({change_pct_val:+.2f}%)</div>
            </div>
            """
        
        # 完整HTML模板
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Kronos预测 - {ticker}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .stock-code {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .current-price {{
            font-size: 48px;
            font-weight: bold;
            color: #2c3e50;
            margin: 15px 0;
        }}
        .price-symbol {{
            font-size: 24px;
            color: #7f8c8d;
        }}
        .trend-indicator {{
            font-size: 28px;
            font-weight: bold;
            color: {trend_color};
            margin-top: 10px;
        }}
        .predictions {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .pred-card {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .pred-step {{
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 8px;
        }}
        .pred-price {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin: 8px 0;
        }}
        .pred-change {{
            font-size: 16px;
            font-weight: 600;
        }}
        .recommendation {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .rec-title {{
            font-size: 18px;
            color: #7f8c8d;
            margin-bottom: 10px;
        }}
        .rec-action {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .confidence-bar {{
            width: 100%;
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 15px;
        }}
        .confidence-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s ease;
        }}
        .timestamp {{
            text-align: center;
            color: white;
            font-size: 14px;
            opacity: 0.8;
            margin-top: 20px;
        }}
        @media (max-width: 480px) {{
            .current-price {{ font-size: 36px; }}
            .stock-code {{ font-size: 24px; }}
            .pred-price {{ font-size: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="stock-code">{ticker}</div>
            <div class="price-symbol">当前价格</div>
            <div class="current-price">¥{current:.2f}</div>
            <div class="trend-indicator">{trend_symbol} 预测变化: {total_change_pct:+.2f}%</div>
        </div>
        
        <div class="predictions">
            {prediction_cards_html}
        </div>
        
        <div class="recommendation">
            <div class="rec-title">交易建议</div>
            <div class="rec-action">{recommendation.get('action', '持有')}</div>
            <div class="rec-title">信心度: {recommendation.get('confidence', '中')}</div>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {confidence}%"></div>
            </div>
            <div class="rec-title" style="margin-top: 10px;">模型信心: {confidence}%</div>
        </div>
        
        <div class="timestamp">
            生成时间: {data.get('timestamp', '')}
        </div>
    </div>
</body>
</html>"""
        
        return html_template
    
    def build_index_page(self, stock_list):
        """生成移动端首页，包含多个股票的快速访问"""
        
        print("正在生成移动端首页...")
        
        # 为每个股票生成报告
        generated_reports = []
        for stock_code in stock_list:
            report_path = self.build_stock_report(stock_code, 'daily', 5)
            if report_path:
                generated_reports.append({
                    'code': stock_code,
                    'path': Path(report_path).name
                })
        
        # 生成首页HTML
        stock_links_html = ""
        for report in generated_reports:
            stock_links_html += f"""
            <a href="{report['path']}" class="stock-link">
                <div class="stock-code-display">{report['code']}</div>
                <div class="view-arrow">查看预测 →</div>
            </a>
            """
        
        index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kronos移动端 - 股票预测</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 36px;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .stock-link {{
            display: block;
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            text-decoration: none;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }}
        .stock-link:active {{
            transform: scale(0.98);
        }}
        .stock-code-display {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .view-arrow {{
            font-size: 16px;
            color: #7f8c8d;
        }}
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 14px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Kronos预测系统</h1>
            <p>移动端智能股票预测</p>
        </div>
        
        {stock_links_html}
        
        <div class="footer">
            由Kronos AI驱动 | {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
</body>
</html>"""
        
        index_path = self.reports_dir / 'index.html'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print(f"首页已生成: {index_path}")
        return str(index_path)


def main():
    """主函数：生成移动端报告示例"""
    
    builder = MobileReportBuilder()
    
    # 热门股票列表
    popular_stocks = ['600519', '600036', '000858', '601318', '000001']
    
    # 生成包含所有股票的移动端站点
    builder.build_index_page(popular_stocks)
    
    print("\n✅ 移动端报告生成完成！")
    print(f"📱 打开 {builder.reports_dir}/index.html 查看")
    print("🚀 可将 mobile_reports 文件夹部署到 Vercel")


if __name__ == '__main__':
    main()
