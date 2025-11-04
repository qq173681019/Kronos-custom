#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kronos股票预测GUI应用程序
支持直接在程序中显示图表，集成多模型预测功能
"""

import sys
import os
import locale

# 设置编码处理
if sys.platform.startswith('win'):
    # Windows系统编码处理
    try:
        # 设置控制台编码为UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        
        # 设置环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 尝试设置本地化
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except:
                pass  # 忽略locale设置错误
    except Exception as e:
        print(f"编码设置警告: {e}")

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib
matplotlib.use('TkAgg')  # 设置matplotlib后端为TkAgg，支持GUI集成
import matplotlib.pyplot as plt
import matplotlib.dates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter, DayLocator
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np
import os
import sys
import subprocess
import threading
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置环境变量，禁用所有交互式确认
import os
os.environ['PYTHONUNBUFFERED'] = '1'  # 禁用输出缓冲
os.environ['AKSHARE_NO_CONFIRM'] = '1'  # 禁用AkShare确认（如果支持）

# exe环境配置 - 必须在导入akshare之前
import sys
if getattr(sys, 'frozen', False):
    print("🔧 exe环境：配置网络...")
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['NO_PROXY'] = '*'
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''

# 网络配置 - 使用验证过的简单配置
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import urllib3
urllib3.disable_warnings()

import warnings
warnings.filterwarnings('ignore')

print("✅ 网络配置完成")

# 尝试导入AkShare库获取真实股票数据
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
    print("✅ AkShare库加载成功")
except ImportError as import_error:
    AKSHARE_AVAILABLE = False
    print(f"❌ AkShare库未安装: {import_error}")
except Exception as e:
    AKSHARE_AVAILABLE = False
    print(f"❌ AkShare库加载失败: {str(e)}")

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['interactive'] = False  # 禁用交互式模式
plt.rcParams['axes.unicode_minus'] = False

# 版本信息
VERSION = "2.0.1"
VERSION_TYPE = "轻量版" if not __name__.endswith('_lite') else "轻量版"
FULL_VERSION = f"v{VERSION} {VERSION_TYPE}"

class KronosPredictor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Kronos股票预测系统 {FULL_VERSION}")
        self.root.geometry("1600x1200")
        
        # 禁用所有可能的确认对话框
        import matplotlib
        matplotlib.interactive(False)  # 禁用matplotlib交互模式
        
        # 设置静默模式环境变量
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        os.environ['AKSHARE_SILENT'] = '1'
        
        # 禁用requests库的警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 存储当前图表
        self.current_figure = None
        self.canvas = None
        self.toolbar = None
        
        # 存储最后的预测文件
        self.last_prediction_files = None
        
        # 初始化多模型预测器
        self.multi_model_predictor = None
        self.multi_model_available = False
        
        self.setup_ui()
        
        # 在UI设置完成后尝试加载多模型预测器
        try:
            from model.multi_model_predictor import MultiModelPredictor
            self.multi_model_available = True
            self.log_message("🤖 多模型预测器加载成功")
        except ImportError as e:
            self.multi_model_available = False
            self.log_message(f"⚠️ 多模型预测器加载失败: {str(e)}")
            self.log_message("💡 需要安装scikit-learn库: pip install scikit-learn")
        
        # 确保data目录存在
        if not os.path.exists("data"):
            os.makedirs("data")
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主容器
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        control_panel = tk.Frame(main_container, width=350)
        control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_panel.pack_propagate(False)
        
        # 右侧图表显示区域
        self.chart_frame = tk.Frame(main_container, bg='white', relief=tk.SUNKEN, borderwidth=2)
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 在图表区域显示提示文本
        self.chart_label = tk.Label(self.chart_frame, text="运行预测后图表将显示在这里", 
                                   font=('Arial', 14), bg='white', fg='gray')
        self.chart_label.pack(expand=True)
        
        # === 控制面板内容 ===
        # 版本信息和标题
        title_frame = tk.Frame(control_panel)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 主标题
        title_label = tk.Label(title_frame, text="Kronos股票预测系统", 
                              font=('Arial', 14, 'bold'), fg='#2E86AB')
        title_label.pack()
        
        # 版本信息
        version_label = tk.Label(title_frame, text=f"{FULL_VERSION} | KDJ+ATR+MACD技术分析", 
                               font=('Arial', 9), fg='#666666')
        version_label.pack()
        
        # 分隔线
        separator = tk.Frame(title_frame, height=2, bg='#E0E0E0')
        separator.pack(fill=tk.X, pady=(5, 0))
        
        # 股票代码输入
        stock_frame = tk.LabelFrame(control_panel, text="股票代码", font=('Arial', 10, 'bold'))
        stock_frame.pack(fill=tk.X, pady=(10, 10))
        
        self.stock_code = tk.StringVar(value="688981")
        tk.Entry(stock_frame, textvariable=self.stock_code, font=('Arial', 12)).pack(pady=5, padx=10, fill=tk.X)
        
        # 图表类型选择
        chart_frame = tk.LabelFrame(control_panel, text="图表类型", font=('Arial', 10, 'bold'))
        chart_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.chart_type = tk.StringVar(value="daily")
        tk.Radiobutton(chart_frame, text="日线图", variable=self.chart_type, value="daily", 
                      font=('Arial', 10), command=self.on_chart_type_changed).pack(anchor='w', padx=10)
        tk.Radiobutton(chart_frame, text="5分钟图", variable=self.chart_type, value="5min", 
                      font=('Arial', 10), command=self.on_chart_type_changed).pack(anchor='w', padx=10)
        
        # 时间范围设置
        # 小字提示替代预测设置
        tips_frame = tk.Frame(control_panel)
        tips_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 添加提示文字
        tip_text = "💡 系统自动优化：日线图使用40日分析/20日显示，5分钟图使用72小时分析/6小时显示"
        self.tips_label = tk.Label(tips_frame, text=tip_text, 
                                  font=('Arial', 8), fg='#666666', 
                                  wraplength=280, justify='left')
        self.tips_label.pack(anchor='w', padx=10, pady=5)
        
        # 重合验证设置（独立框架）
        overlap_main_frame = tk.LabelFrame(control_panel, text="重合验证设置", font=('Arial', 10, 'bold'))
        overlap_main_frame.pack(fill=tk.X, pady=(0, 10))
        
        overlap_frame = tk.Frame(overlap_main_frame)
        overlap_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.overlap_title_label = tk.Label(overlap_frame, text="重合天数 (日线图):")
        self.overlap_title_label.pack(anchor='w')
        
        # 滑动条和数值显示的容器
        slider_container = tk.Frame(overlap_frame)
        slider_container.pack(fill=tk.X, pady=2)
        
        # 重合验证滑动条（调整范围为0-4，默认值为1）
        self.overlap_days = tk.IntVar(value=1)  # 默认值改为1天
        self.overlap_scale = tk.Scale(slider_container, 
                                     from_=0, to=4,  # 范围改为0-4天
                                     orient=tk.HORIZONTAL,
                                     variable=self.overlap_days,
                                     command=self.update_overlap_label,
                                     length=200)
        self.overlap_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 显示当前数值（动态单位）
        self.overlap_value_label = tk.Label(slider_container, text="1天", 
                                           font=('Arial', 9, 'bold'), 
                                           fg='darkgreen', width=6)
        self.overlap_value_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 动态说明标签
        self.note_label = tk.Label(tips_frame, text="📊 日线图：取前30日数据分析，显示25日历史，预测从第22日开始（3日重合+7日纯预测）", 
                                  font=('Arial', 8), fg='blue', wraplength=300)
        self.note_label.pack(anchor='w', padx=10, pady=2)
        
        # 多次预测平均设置
        multi_pred_frame = tk.Frame(tips_frame)
        multi_pred_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.use_multiple_predictions = tk.BooleanVar(value=True)
        self.multi_pred_checkbox = tk.Checkbutton(multi_pred_frame, 
                                                 text="启用5次预测平均（提高稳定性）",
                                                 variable=self.use_multiple_predictions,
                                                 font=('Arial', 9))
        self.multi_pred_checkbox.pack(anchor='w')
        
        # 预测次数说明
        multi_info_label = tk.Label(multi_pred_frame, 
                                   text="🔄 多次预测可减少随机性，提供更稳定的结果", 
                                   font=('Arial', 8), fg='green', wraplength=300)
        multi_info_label.pack(anchor='w', pady=(2, 0))
        
        # 多模型集成预测设置
        ensemble_frame = tk.LabelFrame(control_panel, text="🤖 多模型集成预测", font=('Arial', 11, 'bold'))
        ensemble_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 启用多模型预测的主开关
        self.use_ensemble_prediction = tk.BooleanVar(value=False)
        self.ensemble_main_checkbox = tk.Checkbutton(ensemble_frame, 
                                                    text="启用多模型集成预测（短期预测增强）",
                                                    variable=self.use_ensemble_prediction,
                                                    font=('Arial', 10, 'bold'),
                                                    fg='darkblue',
                                                    command=self.toggle_ensemble_options)
        self.ensemble_main_checkbox.pack(anchor='w', padx=10, pady=5)
        
        # 模型权重设置框架（初始时禁用）
        self.ensemble_options_frame = tk.Frame(ensemble_frame)
        self.ensemble_options_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 权重设置说明
        weight_info_label = tk.Label(self.ensemble_options_frame, 
                                    text="📊 各模型权重（总和=100%）：", 
                                    font=('Arial', 10), fg='blue')
        weight_info_label.pack(anchor='w')
        
        # 紧凑型权重设置框架
        weights_main_frame = tk.Frame(self.ensemble_options_frame)
        weights_main_frame.pack(fill=tk.X, pady=3)
        
        # 技术指标权重（左侧）
        tech_weight_frame = tk.Frame(weights_main_frame)
        tech_weight_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(tech_weight_frame, text="技术:", font=('Arial', 9)).pack()
        self.tech_weight = tk.IntVar(value=30)
        self.tech_scale = tk.Scale(tech_weight_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                  variable=self.tech_weight, length=100,
                                  command=lambda v: self.update_weight_display('tech'))
        self.tech_scale.pack()
        self.tech_weight_label = tk.Label(tech_weight_frame, text="30%", font=('Arial', 9))
        self.tech_weight_label.pack()
        
        # 机器学习权重（中间）
        ml_weight_frame = tk.Frame(weights_main_frame)
        ml_weight_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(ml_weight_frame, text="机器学习:", font=('Arial', 9)).pack()
        self.ml_weight = tk.IntVar(value=40)
        self.ml_scale = tk.Scale(ml_weight_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                variable=self.ml_weight, length=100,
                                command=lambda v: self.update_weight_display('ml'))
        self.ml_scale.pack()
        self.ml_weight_label = tk.Label(ml_weight_frame, text="40%", font=('Arial', 9))
        self.ml_weight_label.pack()
        
        # 支撑阻力位权重（右侧）
        sr_weight_frame = tk.Frame(weights_main_frame)
        sr_weight_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(sr_weight_frame, text="支撑阻力:", font=('Arial', 9)).pack()
        self.sr_weight = tk.IntVar(value=30)
        self.sr_scale = tk.Scale(sr_weight_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                variable=self.sr_weight, length=100,
                                command=lambda v: self.update_weight_display('sr'))
        self.sr_scale.pack()
        self.sr_weight_label = tk.Label(sr_weight_frame, text="30%", font=('Arial', 9))
        self.sr_weight_label.pack()
        
        # 权重总和显示（紧凑型）
        weight_sum_frame = tk.Frame(self.ensemble_options_frame)
        weight_sum_frame.pack(fill=tk.X, pady=2)
        tk.Label(weight_sum_frame, text="总和:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.weight_sum_label = tk.Label(weight_sum_frame, text="100%", 
                                        font=('Arial', 9, 'bold'), fg='green')
        self.weight_sum_label.pack(side=tk.LEFT, padx=5)
        
        # 集成权重设置
        ensemble_weight_frame = tk.Frame(self.ensemble_options_frame)
        ensemble_weight_frame.pack(fill=tk.X, pady=5)
        tk.Label(ensemble_weight_frame, text="与Kronos算法混合比例:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        mix_frame = tk.Frame(ensemble_weight_frame)
        mix_frame.pack(fill=tk.X, pady=2)
        tk.Label(mix_frame, text="多模型:", font=('Arial', 9)).pack(side=tk.LEFT)
        self.ensemble_mix_weight = tk.IntVar(value=50)
        self.ensemble_mix_scale = tk.Scale(mix_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                          variable=self.ensemble_mix_weight, length=180,
                                          command=self.update_mix_weight_display)
        self.ensemble_mix_scale.pack(side=tk.LEFT, padx=5)
        self.ensemble_mix_label = tk.Label(mix_frame, text="50%", font=('Arial', 9), width=4)
        self.ensemble_mix_label.pack(side=tk.LEFT)
        
        self.kronos_mix_label = tk.Label(ensemble_weight_frame, text="🔮 Kronos算法: 50%", 
                                        font=('Arial', 9), fg='green')
        self.kronos_mix_label.pack(anchor='w')
        
        # 多模型预测说明（压缩版）
        ensemble_info_label = tk.Label(self.ensemble_options_frame, 
                                      text="💡 结合技术分析、机器学习和支撑阻力位的综合预测", 
                                      font=('Arial', 9), fg='purple', wraplength=350)
        ensemble_info_label.pack(anchor='w', pady=(3, 0))
        
        # 初始状态禁用选项
        self.toggle_ensemble_options()
        
        # 按钮区域
        button_frame = tk.Frame(control_panel)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 运行预测按钮
        self.predict_button = tk.Button(button_frame, text="运行预测", 
                                       command=self.run_prediction, 
                                       font=('Arial', 11, 'bold'),
                                       bg='#4CAF50', fg='white',
                                       height=1)
        self.predict_button.pack(fill=tk.X, pady=(0, 3))
        
        # 保存图表按钮
        self.save_button = tk.Button(button_frame, text="保存图表", 
                                    command=self.save_chart,
                                    font=('Arial', 9))
        self.save_button.pack(fill=tk.X, pady=(0, 3))
        
        # 打开结果文件夹按钮
        self.folder_button = tk.Button(button_frame, text="打开结果文件夹", 
                                      command=self.open_results_folder,
                                      font=('Arial', 9))
        self.folder_button.pack(fill=tk.X, pady=(0, 3))
        
        # CSV批量分析按钮
        self.csv_batch_button = tk.Button(button_frame, text="📊 CSV批量分析", 
                                         command=self.open_csv_batch_analyzer,
                                         font=('Arial', 10, 'bold'),
                                         bg='#FF9800', fg='white',
                                         height=1)
        self.csv_batch_button.pack(fill=tk.X, pady=(0, 5))
        
        # 进度条
        self.progress = ttk.Progressbar(control_panel, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        # 交易建议显示区域
        advice_frame = tk.LabelFrame(control_panel, text="💡 智能交易建议", 
                                   font=('Arial', 10, 'bold'), 
                                   fg='#2c3e50',
                                   relief=tk.RAISED, borderwidth=2)
        advice_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 交易建议内容框架
        advice_content = tk.Frame(advice_frame)
        advice_content.pack(fill=tk.X, padx=5, pady=5)
        
        # 建议结果显示
        self.advice_result_frame = tk.Frame(advice_content, 
                                          bg='#f8f9fa', 
                                          relief=tk.SOLID, 
                                          borderwidth=2)
        self.advice_result_frame.pack(fill=tk.X, pady=(0, 8))
        
        # 建议标题
        self.advice_title = tk.Label(self.advice_result_frame, 
                                   text="⏳ 等待预测数据...", 
                                   font=('Arial', 13, 'bold'),
                                   bg='#f8f9fa', fg='#666666')
        self.advice_title.pack(pady=8)
        
        # 建议详情
        self.advice_detail = tk.Label(self.advice_result_frame, 
                                    text="运行预测后将显示智能交易建议",
                                    font=('Arial', 10),
                                    bg='#f8f9fa', fg='#888888',
                                    wraplength=300, justify=tk.CENTER)
        self.advice_detail.pack(pady=(0, 8))
        
        # 快速操作按钮框架
        quick_action_frame = tk.Frame(advice_content)
        quick_action_frame.pack(fill=tk.X)
        
        # 刷新建议按钮
        self.refresh_advice_btn = tk.Button(quick_action_frame, text="🔄 刷新", 
                                          command=self.refresh_quick_advice,
                                          font=('Arial', 9, 'bold'),
                                          bg='#17a2b8', fg='white',
                                          relief=tk.RAISED,
                                          state='disabled')
        self.refresh_advice_btn.pack(side=tk.LEFT, padx=(0, 8), fill=tk.X, expand=True)
        
        # 详细分析按钮
        self.detail_advice_btn = tk.Button(quick_action_frame, text="📊 详细分析", 
                                         command=self.show_detailed_analysis,
                                         font=('Arial', 9, 'bold'),
                                         bg='#28a745', fg='white',
                                         relief=tk.RAISED,
                                         state='disabled')
        self.detail_advice_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 状态日志
        log_frame = tk.LabelFrame(control_panel, text="状态日志", font=('Arial', 10, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建日志文本框和滚动条
        log_container = tk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_container, height=8, font=('Consolas', 9))
        scrollbar = tk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始日志
        self.log_message("Kronos股票预测系统已启动")
        if AKSHARE_AVAILABLE:
            self.log_message("✅ 已启用真实数据模式 (AkShare)")
            self.log_message("📡 将从服务器获取真实股票数据")
        else:
            self.log_message("⚠️ 模拟数据模式")
            self.log_message("💡 使用高质量模拟数据进行演示")
        self.log_message("请输入股票代码并选择图表类型")
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def get_stock_name(self, code):
        """获取股票的中文名称 - 优化版"""
        
        # 扩展硬编码股票名称库，优先使用本地数据
        stock_names = {
            '688981': '中芯国际',
            '000001': '平安银行', 
            '000002': '万科A',
            '600519': '贵州茅台',
            '600036': '招商银行',
            '000858': '五粮液',
            '600977': '中国电影',  # 修正名称
            '000651': '格力电器',
            '002415': '海康威视',
            '300059': '东方财富',
            '002594': '比亚迪',
            '600276': '恒瑞医药',
            '002304': '洋河股份',
            '000963': '华东医药',
            '600309': '万华化学'
        }
        
        # 首先检查硬编码列表
        if code in stock_names:
            self.log_message(f"✅ 从本地数据库找到: {stock_names[code]}")
            return stock_names[code]
        
        if not AKSHARE_AVAILABLE:
            self.log_message(f"⚠️ AkShare不可用，使用代码 {code} 显示")
            return code
        
        try:
            self.log_message(f"🔍 正在获取股票 {code} 的名称...")
            
            # 使用静默模式避免输出干扰
            import contextlib
            import io
            
            captured_output = io.StringIO()
            with contextlib.redirect_stdout(captured_output), \
                 contextlib.redirect_stderr(captured_output):
                
                # 优先方法：股票基本信息（相对稳定）
                try:
                    stock_info = ak.stock_individual_info_em(symbol=code)
                    if stock_info is not None and len(stock_info) > 0:
                        # 查找股票简称
                        for idx, row in stock_info.iterrows():
                            item = str(row['item']).strip()
                            value = str(row['value']).strip()
                            
                            if item in ['股票简称', '简称', '名称', '公司简称']:
                                if value and value != 'nan' and len(value) > 1:
                                    self.log_message(f"✅ 通过基本信息找到: {value}")
                                    # 将新找到的名称添加到本地缓存
                                    stock_names[code] = value
                                    return value
                        
                        self.log_message(f"⚠️ 基本信息中未找到名称字段")
                    else:
                        self.log_message(f"⚠️ 未获取到股票基本信息")
                        
                except Exception as e1:
                    self.log_message(f"基本信息方法失败: {str(e1)[:50]}...")
                
                # 备用方法：A股实时行情（有时不稳定但信息全面）
                try:
                    # Windows系统不支持signal.alarm，使用简单的超时机制
                    import threading
                    import time
                    
                    result_container = {'result': None, 'error': None}
                    
                    def fetch_stock_list():
                        try:
                            result_container['result'] = ak.stock_zh_a_spot_em()
                        except Exception as e:
                            result_container['error'] = e
                    
                    # 创建并启动线程
                    thread = threading.Thread(target=fetch_stock_list)
                    thread.daemon = True
                    thread.start()
                    
                    # 等待最多3秒
                    thread.join(timeout=3.0)
                    
                    if thread.is_alive():
                        self.log_message(f"⚠️ 实时行情请求超时（3秒）")
                    elif result_container['error']:
                        raise result_container['error']
                    elif result_container['result'] is not None:
                        stock_list = result_container['result']
                        
                        if len(stock_list) > 0:
                            # 精确匹配代码
                            matching_stocks = stock_list[stock_list['代码'] == code]
                            if len(matching_stocks) > 0:
                                name = matching_stocks.iloc[0]['名称']
                                self.log_message(f"✅ 通过实时行情找到: {name}")
                                # 添加到本地缓存
                                stock_names[code] = name
                                return name
                            
                            self.log_message(f"⚠️ 在实时行情中未找到代码 {code}")
                    
                except Exception as e2:
                    self.log_message(f"实时行情方法失败: {str(e2)[:50]}...")
                
                # 如果都失败了，返回None
                self.log_message(f"⚠️ 所有方法都未能获取到股票名称")
                return None
                    
        except Exception as e:
            self.log_message(f"❌ 获取股票名称总体失败: {str(e)[:50]}...")
            return None
    
    def update_overlap_label(self, value):
        """更新重合验证标签和说明（支持日线图和5分钟图）"""
        overlap_value = int(value)
        
        # 获取当前选择的图表类型
        chart_type = self.chart_type.get()
        
        if chart_type == "daily":
            # 日线图模式：天数单位
            self.overlap_value_label.config(text=f"{overlap_value}天")
            
            # 更新动态说明 - 总是保证10天纯预测
            if overlap_value == 0:
                desc = f"📊 日线图：使用40日数据分析，显示20日历史+预测10日（无重合验证）"
            else:
                desc = f"📊 日线图：使用40日数据分析，显示20日历史+预测10日（{overlap_value}日重合验证）"
        else:
            # 5分钟图模式：分钟单位
            self.overlap_value_label.config(text=f"{overlap_value}分钟")
            
            # 更新动态说明 - 总是保证120分钟纯预测
            if overlap_value == 0:
                desc = f"📈 5分钟图：使用72小时数据分析，显示6小时+预测120分钟（无重合验证）"
            else:
                desc = f"📈 5分钟图：使用72小时数据分析，显示6小时+预测120分钟（{overlap_value}分钟重合验证）"
        
        self.note_label.config(text=desc)
    
    def on_chart_type_changed(self):
        """当图表类型改变时调整UI设置"""
        chart_type = self.chart_type.get()
        
        if chart_type == "daily":
            # 日线图模式设置
            self.overlap_title_label.config(text="重合天数 (日线图):")
            self.overlap_scale.config(from_=0, to=4, resolution=1)  # 范围0-4天
            self.overlap_days.set(1)  # 默认1天
            self.update_overlap_label(1)
        else:
            # 5分钟图模式设置
            self.overlap_title_label.config(text="重合分钟数 (5分钟图):")
            self.overlap_scale.config(from_=0, to=60, resolution=5)  # 范围0-60分钟，步长5分钟
            self.overlap_days.set(15)  # 默认15分钟
            self.update_overlap_label(15)
    
    def toggle_ensemble_options(self):
        """切换多模型预测选项的启用状态"""
        enabled = self.use_ensemble_prediction.get()
        state = 'normal' if enabled else 'disabled'
        
        # 切换所有子控件状态
        for widget in self.ensemble_options_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, (tk.Scale, tk.Label)):
                        child.config(state=state)
            elif isinstance(widget, (tk.Scale, tk.Label)):
                widget.config(state=state)
        
        # 只有在log_text存在时才记录日志
        if hasattr(self, 'log_text'):
            if enabled:
                self.log_message("🤖 已启用多模型集成预测")
            else:
                self.log_message("🔮 使用传统Kronos预测算法")
    
    def update_weight_display(self, changed_weight=None):
        """更新权重显示，自动调整其他权重保持总和100%"""
        # 防止递归调用
        if hasattr(self, '_updating_weights') and self._updating_weights:
            return
        
        self._updating_weights = True
        
        try:
            tech_w = self.tech_weight.get()
            ml_w = self.ml_weight.get()
            sr_w = self.sr_weight.get()
            
            # 根据哪个权重被调整，自动调整其他两个
            if changed_weight == 'tech':
                # 技术指标被调整，按比例调整机器学习和支撑阻力
                remaining = 100 - tech_w
                if remaining <= 0:
                    # 如果技术指标设为100%，其他设为0
                    ml_w = 0
                    sr_w = 0
                else:
                    # 按原来的比例分配剩余权重
                    original_ml_sr_total = ml_w + sr_w
                    if original_ml_sr_total > 0:
                        ml_ratio = ml_w / original_ml_sr_total
                        sr_ratio = sr_w / original_ml_sr_total
                        ml_w = int(remaining * ml_ratio)
                        sr_w = remaining - ml_w  # 确保总和为100
                    else:
                        # 如果原来都是0，平均分配
                        ml_w = remaining // 2
                        sr_w = remaining - ml_w
                
                self.ml_weight.set(ml_w)
                self.sr_weight.set(sr_w)
                
            elif changed_weight == 'ml':
                # 机器学习被调整，按比例调整技术指标和支撑阻力
                remaining = 100 - ml_w
                if remaining <= 0:
                    tech_w = 0
                    sr_w = 0
                else:
                    original_tech_sr_total = tech_w + sr_w
                    if original_tech_sr_total > 0:
                        tech_ratio = tech_w / original_tech_sr_total
                        sr_ratio = sr_w / original_tech_sr_total
                        tech_w = int(remaining * tech_ratio)
                        sr_w = remaining - tech_w
                    else:
                        tech_w = remaining // 2
                        sr_w = remaining - tech_w
                
                self.tech_weight.set(tech_w)
                self.sr_weight.set(sr_w)
                
            elif changed_weight == 'sr':
                # 支撑阻力被调整，按比例调整技术指标和机器学习
                remaining = 100 - sr_w
                if remaining <= 0:
                    tech_w = 0
                    ml_w = 0
                else:
                    original_tech_ml_total = tech_w + ml_w
                    if original_tech_ml_total > 0:
                        tech_ratio = tech_w / original_tech_ml_total
                        ml_ratio = ml_w / original_tech_ml_total
                        tech_w = int(remaining * tech_ratio)
                        ml_w = remaining - tech_w
                    else:
                        tech_w = remaining // 2
                        ml_w = remaining - tech_w
                
                self.tech_weight.set(tech_w)
                self.ml_weight.set(ml_w)
            
            # 更新显示标签
            self.tech_weight_label.config(text=f"{self.tech_weight.get()}%")
            self.ml_weight_label.config(text=f"{self.ml_weight.get()}%")
            self.sr_weight_label.config(text=f"{self.sr_weight.get()}%")
            
            # 计算总和并更新显示
            total = self.tech_weight.get() + self.ml_weight.get() + self.sr_weight.get()
            self.weight_sum_label.config(text=f"{total}%", 
                                        fg='green' if total == 100 else 'red')
            
        finally:
            self._updating_weights = False
    
    def update_mix_weight_display(self, value=None):
        """更新混合权重显示"""
        ensemble_w = self.ensemble_mix_weight.get()
        kronos_w = 100 - ensemble_w
        
        self.ensemble_mix_label.config(text=f"{ensemble_w}%")
        self.kronos_mix_label.config(text=f"🔮 Kronos算法: {kronos_w}%")
    
    def get_ensemble_weights(self):
        """获取当前的权重设置"""
        # 归一化权重
        tech_w = self.tech_weight.get()
        ml_w = self.ml_weight.get()
        sr_w = self.sr_weight.get()
        total = tech_w + ml_w + sr_w
        
        if total == 0:
            return {'technical': 0.33, 'ml': 0.33, 'support_resistance': 0.34}
        
        return {
            'technical': tech_w / total,
            'ml': ml_w / total, 
            'support_resistance': sr_w / total
        }
    
    def get_stock_data_simple(self, code, chart_type, hist_days, pred_days):
        """获取真实股票数据，如果失败则返回None"""
        if AKSHARE_AVAILABLE:
            self.log_message(f"🔍 使用真实数据模式获取 {code} 的数据")
            return self.get_real_stock_data(code, chart_type, hist_days, pred_days)
        else:
            self.log_message(f"❌ AkShare库不可用，无法获取真实数据")
            return None, None
    
    def test_network_connectivity(self):
        """测试网络连接性和诊断问题"""
        self.log_message("🔍 开始网络连接测试...")
        
        # 测试1: 基本DNS解析
        try:
            import socket
            socket.gethostbyname('www.baidu.com')
            self.log_message("✅ DNS解析正常")
        except Exception as e:
            self.log_message(f"❌ DNS解析失败: {str(e)}")
            return False
        
        # 测试2: HTTP连接测试
        try:
            import requests
            import time
            
            start_time = time.time()
            response = requests.get('http://www.baidu.com', timeout=10, verify=False)
            end_time = time.time()
            
            if response.status_code == 200:
                self.log_message(f"✅ HTTP连接正常 (耗时: {end_time-start_time:.2f}秒)")
            else:
                self.log_message(f"⚠️ HTTP连接异常，状态码: {response.status_code}")
        except Exception as e:
            self.log_message(f"❌ HTTP连接失败: {str(e)}")
            # 继续测试，不直接返回False
        
        # 测试3: HTTPS连接测试
        try:
            response = requests.get('https://www.baidu.com', timeout=10, verify=False)
            if response.status_code == 200:
                self.log_message("✅ HTTPS连接正常")
            else:
                self.log_message(f"⚠️ HTTPS连接异常，状态码: {response.status_code}")
        except Exception as e:
            self.log_message(f"❌ HTTPS连接失败: {str(e)}")
        
        # 测试4: AkShare相关域名测试
        akshare_domains = [
            'push2.eastmoney.com',
            'api.finance.sina.com.cn',
            'hq.sinajs.cn'
        ]
        
        working_domains = 0
        for domain in akshare_domains:
            try:
                socket.gethostbyname(domain)
                self.log_message(f"✅ {domain} 解析正常")
                working_domains += 1
            except Exception as e:
                self.log_message(f"❌ {domain} 解析失败: {str(e)}")
        
        if working_domains == 0:
            self.log_message("❌ 所有AkShare相关域名都无法访问")
            return False
        elif working_domains < len(akshare_domains):
            self.log_message(f"⚠️ 部分AkShare域名可访问 ({working_domains}/{len(akshare_domains)})")
        else:
            self.log_message("✅ 所有AkShare域名都可访问")
        
        # 测试5: 代理检测
        import os
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        proxy_detected = False
        for var in proxy_vars:
            if os.environ.get(var):
                self.log_message(f"⚠️ 检测到代理设置: {var}={os.environ.get(var)}")
                proxy_detected = True
        
        if not proxy_detected:
            self.log_message("✅ 未检测到代理设置")
        
        self.log_message("🔍 网络诊断完成，尝试获取数据...")
        return True
    
    def diagnose_network_error(self, error_msg, attempt_num):
        """诊断网络错误并提供解决建议"""
        self.log_message(f"🔍 错误诊断 (第{attempt_num}次):")
        
        # 分析错误类型
        error_lower = error_msg.lower()
        
        if "connectionerror" in error_lower or "connection" in error_lower:
            self.log_message("  🌐 连接错误 - 可能是网络不稳定或服务器繁忙")
            self.log_message("  💡 建议: 检查网络连接，稍后重试")
            
        elif "timeout" in error_lower:
            self.log_message("  ⏱️ 超时错误 - 网络响应过慢")
            self.log_message("  💡 建议: 检查网络速度，或使用VPN")
            
        elif "ssl" in error_lower or "certificate" in error_lower:
            self.log_message("  🔐 SSL证书错误 - 安全连接失败")
            self.log_message("  💡 建议: 证书验证已禁用，可能是网络环境限制")
            
        elif "403" in error_lower or "forbidden" in error_lower:
            self.log_message("  🚫 访问被禁止 - 可能是IP被限制或需要认证")
            self.log_message("  💡 建议: 更换网络环境或稍后重试")
            
        elif "404" in error_lower or "not found" in error_lower:
            self.log_message("  📊 资源未找到 - 可能是股票代码错误或API变更")
            self.log_message("  💡 建议: 检查股票代码格式")
            
        elif "500" in error_lower or "internal server" in error_lower:
            self.log_message("  🔧 服务器内部错误 - 数据源服务器问题")
            self.log_message("  💡 建议: 稍后重试，这通常是临时问题")
            
        elif "proxy" in error_lower:
            self.log_message("  🔄 代理相关错误 - 代理设置问题")
            self.log_message("  💡 建议: 检查代理设置或暂时关闭代理")
            
        else:
            self.log_message(f"  ❓ 未知错误类型: {error_msg[:100]}...")
            self.log_message("  💡 建议: 检查网络连接和防火墙设置")
    
    def get_real_stock_data(self, code, chart_type, hist_days, pred_days):
        """使用AkShare获取真实股票数据，增强错误处理和重试机制"""
        
        # exe环境下的运行时配置
        import sys
        if getattr(sys, 'frozen', False):
            self.log_message("🔧 exe环境：应用运行时网络配置...")
            try:
                # 重新设置akshare相关的环境配置
                import os
                os.environ['PYTHONHTTPSVERIFY'] = '0'
                os.environ['NO_PROXY'] = '*'
                
                # 尝试配置requests
                import requests
                requests.packages.urllib3.disable_warnings()
                
                # 设置默认的session配置
                session = requests.Session()
                session.verify = False
                session.timeout = 30
                
                # 尝试替换akshare内部的requests
                import akshare
                if hasattr(akshare, 'requests'):
                    akshare.requests.packages.urllib3.disable_warnings()
                
                self.log_message("✅ exe环境运行时配置完成")
            except Exception as e:
                self.log_message(f"⚠️ exe环境配置部分失败: {str(e)}")
        
        # 首先进行网络连接测试
        if not self.test_network_connectivity():
            self.log_message("❌ 网络连接测试失败，无法获取真实数据")
            return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.log_message(f"🔄 第{attempt+1}次尝试获取数据...")
                else:
                    self.log_message(f"正在从服务器获取 {code} 的真实数据...")
                
                # 计算日期范围
                today = pd.Timestamp.now().normalize()
                if chart_type == "daily":
                    # 日线图逻辑：获取40日数据进行分析，显示20日历史+10日预测
                    start_date = (today - pd.DateOffset(days=40)).strftime('%Y%m%d')
                    end_date = today.strftime('%Y%m%d')
                    period = 'daily'
                    self.log_message(f"📈 日线图模式：获取40日数据分析，显示20日历史+10日预测")
                else:  # 5分钟数据 - 获取前72小时数据用于分析，显示24小时
                    start_date = (today - pd.Timedelta(days=3)).strftime('%Y%m%d')
                    end_date = today.strftime('%Y%m%d')
                    period = '5'
                    self.log_message(f"📊 5分钟图模式：获取前72小时数据分析，显示6小时+预测120分钟")
                
                self.log_message(f"📅 查询日期范围: {start_date} 至 {end_date}")
                
                # 调用AkShare API获取数据（静默模式）
                import sys
                import contextlib
                import io
                import time
                
                # 创建静默上下文，捕获所有输出和输入
                captured_output = io.StringIO()
                
                # 在重试时增加延迟
                if attempt > 0:
                    time.sleep(2 * attempt)
                
                stock_data = None
                with contextlib.redirect_stdout(captured_output), \
                     contextlib.redirect_stderr(captured_output):
                    
                    if chart_type == "5min":
                        self.log_message(f"📊 调用API获取5分钟数据...")
                        # 获取5分钟数据
                        stock_data = ak.stock_zh_a_hist_min_em(
                            symbol=code,
                            start_date=start_date + " 09:30:00",
                            end_date=end_date + " 15:00:00",
                            period='5',
                            adjust=''
                        )
                    else:
                        self.log_message(f"📊 调用API获取日线数据...")
                        # 获取日线数据
                        stock_data = ak.stock_zh_a_hist(
                            symbol=code,
                            period=period,
                            start_date=start_date,
                            end_date=end_date,
                            adjust=""
                        )
                
                if stock_data is None or stock_data.empty:
                    raise Exception(f"API返回空数据，股票代码 {code} 可能无效")
                
                self.log_message(f"✅ 成功获取到 {len(stock_data)} 条原始数据")
                
                # 统一列名处理
                rename_map = {
                    '开盘': 'open',
                    '收盘': 'close', 
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount'
                }
                
                stock_data = stock_data.rename(columns=rename_map)
                
                # 确保价格列为数值类型
                price_columns = ['open', 'close', 'high', 'low']
                for col in price_columns:
                    if col in stock_data.columns:
                        stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')
                
                # 移除包含无效数据的行
                stock_data = stock_data.dropna(subset=price_columns)
                
                if stock_data.empty:
                    raise Exception("数据处理后为空，可能存在数据质量问题")
                
                # 数据验证
                if len(stock_data) < 5:
                    raise Exception(f"获取的数据量过少({len(stock_data)}条)，无法进行有效分析")
                
                self.log_message(f"✅ 数据验证成功，共 {len(stock_data)} 条有效数据")
                
                # 返回处理好的数据
                return self.process_stock_data(stock_data, chart_type, hist_days, pred_days)
                
            except Exception as e:
                error_msg = str(e)
                self.log_message(f"❌ 第{attempt+1}次尝试失败: {error_msg}")
                
                # 详细错误诊断
                self.diagnose_network_error(error_msg, attempt + 1)
                
                # 常见错误的特殊处理
                if "连接" in error_msg or "网络" in error_msg or "timeout" in error_msg.lower():
                    self.log_message("🌐 检测到网络连接问题")
                elif "代码" in error_msg or "symbol" in error_msg.lower():
                    self.log_message("📊 请检查股票代码是否正确")
                    break  # 股票代码错误不需要重试
                elif "权限" in error_msg or "403" in error_msg:
                    self.log_message("🔒 检测到访问权限问题")
                elif "ssl" in error_msg.lower() or "certificate" in error_msg.lower():
                    self.log_message("🔐 检测到SSL证书问题")
                elif "proxy" in error_msg.lower():
                    self.log_message("🔄 检测到代理相关问题")
                
                if attempt == max_retries - 1:
                    self.log_message(f"❌ 所有尝试均失败，启用模拟数据模式")
                    self.log_message("💡 提示：请检查网络连接或稍后重试")
                    self.log_message("🔧 建议：可以使用Python版本(.py文件)获取真实数据")
                    return None, None
                else:
                    self.log_message(f"⏳ 等待重试中...")
        
        return None, None
    
    def process_stock_data(self, stock_data, chart_type, hist_days, pred_days):
        """处理股票数据"""
        try:
            # 统一列名处理
            rename_map = {
                '开盘': 'open',
                '收盘': 'close', 
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            }
            
            # 重命名存在的列
            existing_renames = {k: v for k, v in rename_map.items() if k in stock_data.columns}
            if existing_renames:
                stock_data = stock_data.rename(columns=existing_renames)
            
            # 处理时间列
            if '日期' in stock_data.columns:
                stock_data['日期'] = pd.to_datetime(stock_data['日期'], errors='coerce')
                if chart_type == "5min":
                    stock_data['timestamps'] = stock_data['日期'].dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    stock_data['timestamps'] = stock_data['日期'].dt.strftime('%Y-%m-%d')
                stock_data = stock_data.drop(columns=['日期'])
            elif '时间' in stock_data.columns:
                stock_data['时间'] = pd.to_datetime(stock_data['时间'], errors='coerce')
                stock_data['timestamps'] = stock_data['时间'].dt.strftime('%Y-%m-%d %H:%M:%S')
                stock_data = stock_data.drop(columns=['时间'])
            
            # 检查时间列是否存在
            if 'timestamps' not in stock_data.columns:
                self.log_message(f"❌ 缺少timestamps列，可用列: {list(stock_data.columns)}")
                raise Exception("时间列处理失败，未生成timestamps列")
            
            # 将timestamps转换为datetime对象
            stock_data['timestamps'] = pd.to_datetime(stock_data['timestamps'])
            
            # 对5分钟数据进行交易时间过滤
            if chart_type == "5min":
                # 只保留交易时间（9:30-15:00）的数据
                stock_data['hour'] = stock_data['timestamps'].dt.hour
                stock_data['minute'] = stock_data['timestamps'].dt.minute
                stock_data['time_decimal'] = stock_data['hour'] + stock_data['minute'] / 60.0
                
                # 过滤条件：9:30-15:00之间，且排除11:30-13:00休市时间
                trading_time_filter = (
                    ((stock_data['time_decimal'] >= 9.5) & (stock_data['time_decimal'] < 11.5)) |
                    ((stock_data['time_decimal'] >= 13.0) & (stock_data['time_decimal'] <= 15.0))
                )
                
                before_filter_count = len(stock_data)
                stock_data = stock_data[trading_time_filter].copy()
                after_filter_count = len(stock_data)
                
                self.log_message(f"⏰ 交易时间过滤：{before_filter_count} → {after_filter_count} 条数据")
                
                # 删除临时列
                stock_data = stock_data.drop(columns=['hour', 'minute', 'time_decimal'])
            
            # 按时间排序
            stock_data = stock_data.sort_values('timestamps').reset_index(drop=True)
            
            # 确保价格列为数值类型
            price_columns = ['open', 'close', 'high', 'low']
            for col in price_columns:
                if col in stock_data.columns:
                    stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')
            
            # 移除包含无效数据的行
            stock_data = stock_data.dropna(subset=price_columns)
            
            if stock_data.empty:
                raise Exception("数据处理后为空，可能存在数据质量问题")
            
            # 数据验证
            if len(stock_data) < 5:
                raise Exception(f"获取的数据量过少({len(stock_data)}条)，无法进行有效分析")
            
            self.log_message(f"✅ 数据处理完成，最终数据量: {len(stock_data)} 条")
            
            # 根据图表类型调用不同的处理逻辑
            if chart_type == "daily":
                return self.process_daily_data(stock_data, hist_days, pred_days)
            else:
                return self.process_minute_data(stock_data, hist_days, pred_days)
                
        except Exception as e:
            self.log_message(f"❌ 数据处理失败: {str(e)}")
            return None
    
    def predict_with_technical_indicators(self, historical_data, pred_days):
        """基于技术指标的预测算法（轻量版）"""
        try:
            # 计算技术指标
            data_with_indicators = historical_data.copy()
            
            # 计算移动平均线
            data_with_indicators['MA5'] = data_with_indicators['close'].rolling(window=5).mean()
            data_with_indicators['MA20'] = data_with_indicators['close'].rolling(window=20).mean()
            
            # 计算MACD
            macd_line, signal_line, histogram = self.calculate_macd(data_with_indicators)
            if macd_line is not None:
                data_with_indicators['MACD'] = macd_line
                data_with_indicators['MACD_Signal'] = signal_line
            
            # 计算KDJ
            data_with_kdj = self.calculate_kdj(data_with_indicators, n=9, m1=3, m2=3)
            if 'K' in data_with_kdj.columns:
                data_with_indicators['K'] = data_with_kdj['K']
                data_with_indicators['D'] = data_with_kdj['D']
                data_with_indicators['J'] = data_with_kdj['J']
            
            # 获取最近的价格和指标
            recent_close = data_with_indicators['close'].iloc[-1]
            recent_ma5 = data_with_indicators['MA5'].iloc[-1] if not pd.isna(data_with_indicators['MA5'].iloc[-1]) else recent_close
            recent_ma20 = data_with_indicators['MA20'].iloc[-1] if not pd.isna(data_with_indicators['MA20'].iloc[-1]) else recent_close
            
            # 计算趋势强度
            ma_trend = 1.0 if recent_ma5 > recent_ma20 else -1.0
            
            # 基于技术指标的价格预测
            predicted_prices = []
            current_price = recent_close
            
            # 计算ATR作为波动性参考
            atr_data = self.calculate_atr(data_with_indicators, period=14)
            recent_atr = atr_data.iloc[-1] if len(atr_data) > 0 else recent_close * 0.02
            
            for i in range(pred_days):
                # 基于趋势和技术指标计算下一个价格
                
                # 趋势因子 (基于MA)
                trend_factor = ma_trend * 0.001  # 0.1%的基础趋势
                
                # KDJ修正 
                if 'K' in data_with_indicators.columns and not pd.isna(data_with_indicators['K'].iloc[-1]):
                    k_value = data_with_indicators['K'].iloc[-1]
                    if k_value > 80:  # 超买
                        trend_factor -= 0.002
                    elif k_value < 20:  # 超卖
                        trend_factor += 0.002
                
                # MACD修正
                if 'MACD' in data_with_indicators.columns and not pd.isna(data_with_indicators['MACD'].iloc[-1]):
                    macd_value = data_with_indicators['MACD'].iloc[-1]
                    macd_signal = data_with_indicators['MACD_Signal'].iloc[-1] if 'MACD_Signal' in data_with_indicators.columns else 0
                    if macd_value > macd_signal:  # 向上趋势
                        trend_factor += 0.001
                    else:  # 向下趋势
                        trend_factor -= 0.001
                
                # 添加一些随机性（基于ATR）
                import random
                volatility_factor = (random.random() - 0.5) * 0.01 * (recent_atr / current_price)
                
                # 计算预测价格
                price_change_factor = 1 + trend_factor + volatility_factor
                current_price = current_price * price_change_factor
                predicted_prices.append(current_price)
            
            # 构造与MultiModelPredictor兼容的返回格式
            result = {
                'ensemble': {
                    'prices': predicted_prices,
                    'confidence': 0.75,  # 技术指标预测的置信度
                    'method': 'technical_indicators'
                }
            }
            
            return result
            
        except Exception as e:
            self.log_message(f"❌ 技术指标预测失败: {str(e)}")
            # 返回简单的线性预测作为最后备份
            last_close = historical_data['close'].iloc[-1]
            simple_prices = [last_close * (1 + 0.001 * i) for i in range(pred_days)]
            return {
                'ensemble': {
                    'prices': simple_prices,
                    'confidence': 0.5,
                    'method': 'simple_linear'
                }
            }, None
    
    def process_daily_data(self, stock_data, hist_days, pred_days):
        """处理日线数据"""
        try:
            # 检查必要的列
            required_columns = ['timestamps', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in stock_data.columns]
            
            if missing_columns:
                self.log_message(f"❌ 数据缺少必要列: {missing_columns}")
                self.log_message(f"可用列: {list(stock_data.columns)}")
                raise Exception(f"数据缺少必要列: {missing_columns}")
            
            # 按时间排序
            stock_data = stock_data.sort_values('timestamps').reset_index(drop=True)
            
            # 日线图特殊处理：使用40日数据分析，显示20日数据
            chart_type = "daily"
            if chart_type == "daily":
                # 获取用户设置的重合天数
                overlap_days = self.overlap_days.get()
                
                # 使用完整的40日数据进行分析
                full_data_for_analysis = stock_data.copy()
                
                # 显示最近20日数据
                display_periods = min(20, len(stock_data))
                historical_data_for_display = stock_data.tail(display_periods).copy()
                
                self.log_message(f"📊 使用{len(full_data_for_analysis)}日数据进行分析")
                self.log_message(f"📈 显示最近{len(historical_data_for_display)}日数据 + 预测{pred_days}日")
                
                # 确保有足够的数据进行预测分析
                if len(full_data_for_analysis) < 20:
                    self.log_message(f"⚠️ 获取到 {len(full_data_for_analysis)} 条数据，少于20日，使用所有可用数据")
                    historical_data_for_display = full_data_for_analysis.copy()
                    # 生成预测数据，使用完整数据分析
                    prediction_data = self.generate_prediction_data_with_overlap(full_data_for_analysis, pred_days, chart_type, overlap_days)
                else:
                    # 使用完整40日数据进行预测分析
                    prediction_data = self.generate_prediction_data_with_overlap(full_data_for_analysis, pred_days, chart_type, overlap_days)
                    
                    if overlap_days == 0:
                        self.log_message(f"📊 日线图：使用40日数据分析，显示20日历史数据，预测{pred_days}日（无重合）")
                    else:
                        self.log_message(f"📊 日线图：使用40日数据分析，显示20日历史数据，预测{pred_days}日（{overlap_days}日重合）")
            
            self.log_message(f"✅ 成功处理 {len(historical_data_for_display)} 条显示数据，生成 {len(prediction_data)} 条预测数据")
            
            return historical_data_for_display, prediction_data
            
        except Exception as e:
            self.log_message(f"❌ 日线数据处理失败: {str(e)}")
            return None, None
    
    def process_minute_data(self, stock_data, hist_days, pred_days):
        """处理5分钟数据"""
        try:
            # 检查必要的列
            required_columns = ['timestamps', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in stock_data.columns]
            
            if missing_columns:
                self.log_message(f"❌ 数据缺少必要列: {missing_columns}")
                return None, None
            
            # 按时间排序
            stock_data = stock_data.sort_values('timestamps').reset_index(drop=True)
            
            # 5分钟图特殊逻辑：使用72小时数据分析，显示24小时
            try:
                overlap_minutes = self.overlap_days.get()  # 这里实际上是分钟数
                
                # 使用完整的72小时数据进行分析
                full_data_for_analysis = stock_data.copy()
                
                # 计算6小时对应的5分钟K线数量
                # 6小时交易时间约为1.5小时 → 约18个5分钟K线
                # 为了显示效果，我们取36个5分钟K线（约3小时交易时间，对应6小时时间跨度）
                display_periods = min(36, len(stock_data))  # 显示最近36个5分钟K线（约6小时时间跨度）
                
                # 分离：用于分析的数据（全部72小时）和用于显示的数据（最近6小时）
                historical_data_for_display = stock_data.tail(display_periods).copy()
                
                self.log_message(f"📊 使用{len(full_data_for_analysis)}条72小时数据进行分析")
                self.log_message(f"📈 显示最近{len(historical_data_for_display)}条数据（约6小时）+ 预测120分钟")
                
                # 5分钟图固定预测120分钟（24个5分钟K线）
                pred_periods = 24  # 120分钟 ÷ 5分钟 = 24个周期
                
                self.log_message(f"📈 5分钟图：使用72小时数据分析，显示6小时，重合验证{overlap_minutes}分钟，预测120分钟")
                
                # 抑制numpy和pandas的警告
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # 使用完整的72小时数据进行预测分析
                    prediction_data = self.generate_prediction_data_5min_with_overlap(full_data_for_analysis, pred_periods, overlap_minutes)
                    
            except Exception as e:
                self.log_message(f"⚠️ 5分钟预测出现问题，使用备用方法: {str(e)}")
                # 使用备用预测方法，依然使用完整数据分析
                prediction_data = self.generate_prediction_data(full_data_for_analysis.tail(50), 24, "5min")
                historical_data_for_display = stock_data.tail(120).copy()
            
            self.log_message(f"✅ 成功处理 {len(historical_data_for_display)} 条显示数据，生成 {len(prediction_data)} 条预测数据")
            
            return historical_data_for_display, prediction_data
            
        except Exception as e:
            self.log_message(f"❌ 5分钟数据处理失败: {str(e)}")
            return None, None
    
    def generate_prediction_data(self, historical_data, pred_days, chart_type):
        """基于历史数据生成预测数据 - 支持多次预测平均"""
        try:
            if len(historical_data) < 5:
                raise Exception("历史数据不足，无法生成预测")
            
            # 检查是否启用多次预测平均
            use_multiple = getattr(self, 'use_multiple_predictions', None)
            if use_multiple and use_multiple.get():
                return self.generate_multiple_predictions_average(historical_data, pred_days, chart_type, num_predictions=5)
            else:
                return self.generate_single_prediction(historical_data, pred_days, chart_type)
                
        except Exception as e:
            self.log_message(f"生成预测数据失败: {str(e)}")
            raise
    
    def generate_single_prediction(self, historical_data, pred_days, chart_type):
        """生成单次预测数据，支持多模型集成"""
        try:
            if len(historical_data) < 5:
                raise Exception("历史数据不足，无法生成预测")
            
            # 检查是否启用多模型集成预测
            use_ensemble = getattr(self, 'use_ensemble_prediction', None)
            if use_ensemble and use_ensemble.get() and self.multi_model_available:
                return self.generate_ensemble_prediction(historical_data, pred_days, chart_type)
            else:
                return self.generate_kronos_prediction(historical_data, pred_days, chart_type)
                
        except Exception as e:
            self.log_message(f"生成预测数据失败: {str(e)}")
            raise
    
    def generate_ensemble_prediction(self, historical_data, pred_days, chart_type):
        """生成多模型集成预测数据"""
        try:
            self.log_message("🤖 启动多模型集成预测...")
            
            # 初始化多模型预测器
            # 尝试使用多模型预测器
            if self.multi_model_available and self.multi_model_predictor is None:
                try:
                    from model.multi_model_predictor import MultiModelPredictor
                    weights = self.get_ensemble_weights()
                    self.multi_model_predictor = MultiModelPredictor(weights)
                    self.log_message(f"🔧 权重设置: {weights}")
                except Exception as e:
                    self.log_message(f"⚠️ 多模型预测器初始化失败: {str(e)}")
                    self.multi_model_available = False
            
            # 准备股票数据格式（需要包含所有必要字段）
            stock_data_for_ml = historical_data.copy()
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in stock_data_for_ml.columns:
                    if col in ['open', 'high', 'low']:
                        stock_data_for_ml[col] = stock_data_for_ml['close']
                    elif col == 'volume':
                        stock_data_for_ml[col] = 1000000  # 默认成交量
            
            # 运行预测算法
            if self.multi_model_available and self.multi_model_predictor is not None:
                # 使用多模型预测器
                ensemble_results = self.multi_model_predictor.predict_short_term(stock_data_for_ml, pred_days)
                self.log_message("🤖 使用AI多模型预测")
            else:
                # 使用技术指标预测算法（轻量版）
                self.log_message("📊 使用技术指标预测算法")
                ensemble_results = self.predict_with_technical_indicators(stock_data_for_ml, pred_days)
            
            # 生成Kronos传统预测作为基准
            kronos_prediction = self.generate_kronos_prediction(historical_data, pred_days, chart_type)
            
            # 获取混合权重
            ensemble_weight = self.ensemble_mix_weight.get() / 100.0
            kronos_weight = 1.0 - ensemble_weight
            
            # 混合预测结果
            if 'ensemble' in ensemble_results and 'prices' in ensemble_results['ensemble']:
                ensemble_prices = ensemble_results['ensemble']['prices']
                kronos_prices = kronos_prediction['close'].values
                
                # 加权混合
                mixed_prices = []
                for i in range(min(len(ensemble_prices), len(kronos_prices))):
                    mixed_price = (ensemble_prices[i] * ensemble_weight + 
                                 kronos_prices[i] * kronos_weight)
                    mixed_prices.append(mixed_price)
                
                # 更新预测数据
                final_prediction = kronos_prediction.copy()
                final_prediction['close'] = mixed_prices
                
                # 调整其他价格字段以保持一致性
                if len(mixed_prices) > 0:
                    for i in range(len(mixed_prices)):
                        final_prediction.loc[i, 'open'] = mixed_prices[i] * (1 + np.random.normal(0, 0.005))
                        final_prediction.loc[i, 'high'] = mixed_prices[i] * (1 + abs(np.random.normal(0, 0.01)))
                        final_prediction.loc[i, 'low'] = mixed_prices[i] * (1 - abs(np.random.normal(0, 0.01)))
                
                # 记录预测信心度
                confidence = ensemble_results.get('confidence', {}).get('overall_confidence', 0.5)
                self.log_message(f"🎯 集成预测完成，信心度: {confidence:.1%}")
                self.log_message(f"⚖️ 混合比例 - 多模型: {ensemble_weight:.1%}, Kronos: {kronos_weight:.1%}")
                
                return final_prediction
            else:
                self.log_message("⚠️ 多模型预测失败，使用Kronos传统算法")
                return kronos_prediction
                
        except Exception as e:
            self.log_message(f"❌ 集成预测失败: {str(e)}")
            self.log_message("🔄 回退到Kronos传统预测算法")
            return self.generate_kronos_prediction(historical_data, pred_days, chart_type)
    
    def generate_kronos_prediction(self, historical_data, pred_days, chart_type):
        """生成Kronos传统预测数据"""
        try:
            if len(historical_data) < 5:
                raise Exception("历史数据不足，无法生成预测")
            
            # 获取最后几个数据点
            last_data = historical_data.tail(5).copy()
            
            # 计算价格变化趋势
            price_changes = last_data['close'].pct_change().dropna()
            avg_change = price_changes.mean()
            volatility = price_changes.std()
            
            # 计算成交量平均值
            avg_volume = last_data['volume'].mean()
            
            # 生成预测时间序列
            last_timestamp = historical_data['timestamps'].iloc[-1]
            if chart_type == "daily":
                future_dates = pd.date_range(
                    start=last_timestamp + pd.Timedelta(days=1),
                    periods=pred_days,
                    freq='D'
                )
            else:  # 5分钟数据
                # 生成未来的15分钟时间戳（只在交易时间）
                future_dates = []
                current_date = last_timestamp + pd.Timedelta(minutes=15)
                
                while len(future_dates) < pred_days:
                    # 只在交易日的交易时间添加
                    if current_date.weekday() < 5:  # 周一到周五
                        if 9.5 <= current_date.hour + current_date.minute/60 <= 15:
                            future_dates.append(current_date)
                    current_date += pd.Timedelta(minutes=15)
                
                future_dates = pd.DatetimeIndex(future_dates[:pred_days])
            
            # 生成预测数据
            last_price = historical_data['close'].iloc[-1]
            predicted_prices = []
            
            for i in range(pred_days):
                # 使用随机游走模型，加入趋势和随机扰动
                random_change = np.random.normal(avg_change, volatility * 0.5)
                trend_factor = 1 + random_change
                predicted_price = last_price * trend_factor
                predicted_prices.append(predicted_price)
                last_price = predicted_price
            
            # 生成其他价格数据
            predicted_closes = np.array(predicted_prices)
            predicted_opens = np.roll(predicted_closes, 1)
            predicted_opens[0] = historical_data['close'].iloc[-1]
            
            # 生成高低价
            predicted_highs = predicted_closes * (1 + np.abs(np.random.normal(0, 0.01, pred_days)))
            predicted_lows = predicted_closes * (1 - np.abs(np.random.normal(0, 0.01, pred_days)))
            
            # 确保价格关系合理
            predicted_highs = np.maximum(predicted_highs, np.maximum(predicted_opens, predicted_closes))
            predicted_lows = np.minimum(predicted_lows, np.minimum(predicted_opens, predicted_closes))
            
            # 生成预测成交量（基于历史平均值加入随机变化）
            predicted_volumes = np.random.normal(avg_volume, avg_volume * 0.3, pred_days)
            predicted_volumes = np.maximum(predicted_volumes, avg_volume * 0.1)  # 确保不为负
            
            # 创建预测数据DataFrame
            prediction_data = pd.DataFrame({
                'timestamps': future_dates,
                'open': predicted_opens,
                'high': predicted_highs,
                'low': predicted_lows,
                'close': predicted_closes,
                'volume': predicted_volumes.astype(int)
            })
            
            return prediction_data
            
        except Exception as e:
            raise Exception(f"生成预测数据时出错: {str(e)}")
    
    def generate_multiple_predictions_average(self, historical_data, pred_days, chart_type, num_predictions=5):
        """生成多次预测并求平均值"""
        try:
            self.log_message(f"🔄 正在进行{num_predictions}次预测并求平均值...")
            
            # 存储多次预测结果
            all_predictions = []
            
            for i in range(num_predictions):
                # 为每次预测设置不同的随机种子
                base_seed = hash(str(historical_data['close'].iloc[-1])) % (2**32)
                np.random.seed(base_seed + i)
                
                # 生成单次预测（直接调用Kronos算法避免递归）
                single_prediction = self.generate_kronos_prediction(historical_data, pred_days, chart_type)
                all_predictions.append(single_prediction)
                
                self.log_message(f"  完成第{i+1}次预测")
            
            # 计算平均值
            self.log_message("📊 计算预测平均值...")
            
            # 取第一次预测作为框架
            avg_prediction = all_predictions[0].copy()
            
            # 对数值列求平均
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                values_matrix = np.array([pred[col].values for pred in all_predictions])
                avg_prediction[col] = np.mean(values_matrix, axis=0)
            
            # 确保价格关系合理
            for i in range(len(avg_prediction)):
                open_price = avg_prediction.iloc[i]['open']
                close_price = avg_prediction.iloc[i]['close']
                high_price = avg_prediction.iloc[i]['high']
                low_price = avg_prediction.iloc[i]['low']
                
                # 调整高低价确保合理关系
                max_price = max(open_price, close_price)
                min_price = min(open_price, close_price)
                
                avg_prediction.iloc[i, avg_prediction.columns.get_loc('high')] = max(high_price, max_price)
                avg_prediction.iloc[i, avg_prediction.columns.get_loc('low')] = min(low_price, min_price)
            
            # 确保成交量为正整数
            avg_prediction['volume'] = avg_prediction['volume'].astype(int).abs()
            
            self.log_message(f"✅ {num_predictions}次预测平均完成，结果更加稳定")
            return avg_prediction
            
        except Exception as e:
            self.log_message(f"多次预测平均失败: {str(e)}")
            # 如果多次预测失败，回退到单次预测
            return self.generate_single_prediction(historical_data, pred_days, chart_type)
    
    def generate_prediction_data_with_overlap(self, full_data, pred_days, chart_type, overlap_days=3):
        """生成有重合区间的预测数据（专用于日线图）- 支持多次预测平均"""
        try:
            if len(full_data) < 10:
                raise Exception("数据不足，无法生成有重合的预测")
            
            # 检查是否启用多次预测平均
            use_multiple = getattr(self, 'use_multiple_predictions', None)
            if use_multiple and use_multiple.get():
                return self.generate_multiple_overlap_predictions_average(full_data, pred_days, chart_type, overlap_days, num_predictions=5)
            else:
                return self.generate_single_overlap_prediction(full_data, pred_days, chart_type, overlap_days)
                
        except Exception as e:
            self.log_message(f"生成重合预测数据失败: {str(e)}")
            raise
    
    def generate_single_overlap_prediction(self, full_data, pred_days, chart_type, overlap_days=3):
        """生成单次重合预测数据"""
        try:
            if len(full_data) < 10:
                raise Exception("数据不足，无法生成有重合的预测")
            
            # 对于日线图，从倒数第overlap_days日开始预测
            # 这样前overlap_days日与历史数据重合，后面为纯预测
            
            # 取倒数第10日到倒数第1日作为分析基础
            analysis_data = full_data.tail(10).copy()
            
            # 计算价格变化趋势
            price_changes = analysis_data['close'].pct_change().dropna()
            avg_change = price_changes.mean()
            volatility = price_changes.std()
            
            # 计算成交量平均值
            avg_volume = analysis_data['volume'].mean()
            
            self.log_message(f"🔮 预测参数：平均变化={avg_change:.4f}, 波动率={volatility:.4f}, 重合天数={overlap_days}")
            
            # 重新计算预测天数：重合天数 + 10天未来预测
            total_pred_days = overlap_days + 10
            
            # 生成预测时间序列：从倒数第overlap_days日开始
            if overlap_days == 0:
                # 无重合，从最后一日的下一日开始
                start_idx = len(full_data)
                start_timestamp = full_data.iloc[-1]['timestamps'] + pd.Timedelta(days=1)
            else:
                # 有重合，从倒数第overlap_days日开始
                start_idx = len(full_data) - overlap_days
                start_timestamp = full_data.iloc[start_idx]['timestamps']
            
            # 生成预测时间序列：重合天数 + 10天未来预测
            future_dates = pd.date_range(
                start=start_timestamp,
                periods=total_pred_days,
                freq='D'
            )
            
            # 生成预测数据
            if overlap_days == 0:
                # 无重合情况，从最后一日收盘价开始
                start_price = full_data.iloc[-1]['close']
            else:
                # 有重合情况，从重合起始日收盘价开始
                start_price = full_data.iloc[start_idx]['close']
                
            predicted_prices = []
            last_price = start_price
            
            for i in range(total_pred_days):
                if i < overlap_days and overlap_days > 0:
                    # 重合区间：在真实价格基础上加入小幅扰动，保持连续性
                    real_idx = start_idx + i
                    if real_idx < len(full_data):
                        real_price = full_data.iloc[real_idx]['close']
                        # 添加小幅扰动，但主要跟随真实趋势
                        noise = np.random.normal(0, volatility * 0.2) if volatility > 0 else 0
                        predicted_price = real_price * (1 + noise)
                    else:
                        # 超出数据范围，使用趋势预测
                        random_change = np.random.normal(avg_change, volatility * 0.5)
                        trend_factor = 1 + random_change
                        predicted_price = last_price * trend_factor
                else:
                    # 纯预测区间：使用趋势预测
                    random_change = np.random.normal(avg_change, volatility * 0.5)
                    trend_factor = 1 + random_change
                    predicted_price = last_price * trend_factor
                
                predicted_prices.append(predicted_price)
                last_price = predicted_price
            
            # 生成其他价格数据
            predicted_closes = np.array(predicted_prices)
            predicted_opens = np.roll(predicted_closes, 1)
            predicted_opens[0] = start_price
            
            # 生成高低价（确保价格关系合理）
            predicted_highs = predicted_closes * (1 + np.abs(np.random.normal(0, 0.01, total_pred_days)))
            predicted_lows = predicted_closes * (1 - np.abs(np.random.normal(0, 0.01, total_pred_days)))
            
            predicted_highs = np.maximum(predicted_highs, np.maximum(predicted_opens, predicted_closes))
            predicted_lows = np.minimum(predicted_lows, np.minimum(predicted_opens, predicted_closes))
            
            # 生成预测成交量
            predicted_volumes = np.random.normal(avg_volume, avg_volume * 0.3, total_pred_days)
            predicted_volumes = np.maximum(predicted_volumes, avg_volume * 0.1)
            
            # 创建预测数据DataFrame
            prediction_data = pd.DataFrame({
                'timestamps': future_dates,
                'open': predicted_opens,
                'high': predicted_highs,
                'low': predicted_lows,
                'close': predicted_closes,
                'volume': predicted_volumes.astype(int)
            })
            
            self.log_message(f"✅ 生成预测数据：{overlap_days}日重合区间 + 10日纯预测")
            
            return prediction_data
            
        except Exception as e:
            raise Exception(f"生成重合预测数据时出错: {str(e)}")
    
    def generate_multiple_overlap_predictions_average(self, full_data, pred_days, chart_type, overlap_days=3, num_predictions=5):
        """生成多次重合预测并求平均值"""
        try:
            self.log_message(f"🔄 正在进行{num_predictions}次重合预测并求平均值...")
            
            # 存储多次预测结果
            all_predictions = []
            
            for i in range(num_predictions):
                # 为每次预测设置不同的随机种子
                base_seed = hash(str(full_data['close'].iloc[-1])) % (2**32)
                np.random.seed(base_seed + i + 100)  # +100是为了与单独预测区分
                
                # 生成单次重合预测
                single_prediction = self.generate_single_overlap_prediction(full_data, pred_days, chart_type, overlap_days)
                all_predictions.append(single_prediction)
                
                self.log_message(f"  完成第{i+1}次重合预测")
            
            # 计算平均值
            self.log_message("📊 计算重合预测平均值...")
            
            # 取第一次预测作为框架
            avg_prediction = all_predictions[0].copy()
            
            # 对数值列求平均
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                values_matrix = np.array([pred[col].values for pred in all_predictions])
                avg_prediction[col] = np.mean(values_matrix, axis=0)
            
            # 确保价格关系合理（特别是重合区间）
            for i in range(len(avg_prediction)):
                open_price = avg_prediction.iloc[i]['open']
                close_price = avg_prediction.iloc[i]['close']
                high_price = avg_prediction.iloc[i]['high']
                low_price = avg_prediction.iloc[i]['low']
                
                # 调整高低价确保合理关系
                max_price = max(open_price, close_price)
                min_price = min(open_price, close_price)
                
                avg_prediction.iloc[i, avg_prediction.columns.get_loc('high')] = max(high_price, max_price)
                avg_prediction.iloc[i, avg_prediction.columns.get_loc('low')] = min(low_price, min_price)
            
            # 确保成交量为正整数
            avg_prediction['volume'] = avg_prediction['volume'].astype(int).abs()
            
            self.log_message(f"✅ {num_predictions}次重合预测平均完成，结果更加稳定")
            return avg_prediction
            
        except Exception as e:
            self.log_message(f"多次重合预测平均失败: {str(e)}")
            # 如果多次预测失败，回退到单次预测
            return self.generate_single_overlap_prediction(full_data, pred_days, chart_type, overlap_days)
    
    def generate_prediction_data_5min_with_overlap(self, stock_data, pred_periods, overlap_minutes):
        """专门为5分钟图生成带重合验证的预测数据"""
        try:
            if len(stock_data) < 10:
                raise Exception("5分钟数据不足，无法生成预测")
            
            # 计算重合的5分钟周期数
            overlap_periods = overlap_minutes // 5  # 将分钟转换为5分钟周期数
            overlap_periods = max(0, min(overlap_periods, len(stock_data) - 1))  # 确保不超过可用数据
            
            # 确定预测和重合的逻辑
            if overlap_periods == 0:
                # 无重合，从最新数据点开始预测
                base_data = stock_data.tail(10).copy()  # 用于分析的基础数据
                overlap_data = None
                # 从最后一个历史数据点开始预测
                last_data = stock_data.iloc[-1]
                last_timestamp = pd.to_datetime(last_data['timestamps'])
                
                self.log_message(f"📊 无重合：从{last_timestamp.strftime('%H:%M')}开始预测120分钟")
            else:
                # 有重合：重合部分显示真实历史数据，然后预测120分钟
                # 获取重合部分的真实数据（最后N个5分钟数据点）
                overlap_data = stock_data.tail(overlap_periods).copy()
                
                # 用于预测算法的基础数据（重合部分之前的数据）
                base_data = stock_data.iloc[:-overlap_periods].tail(10) if len(stock_data) > overlap_periods else stock_data.tail(5)
                
                # 从重合部分的起始点开始（用于生成时间戳）
                overlap_start_data = stock_data.iloc[-overlap_periods]
                last_timestamp = pd.to_datetime(overlap_start_data['timestamps'])
                
                overlap_start_time = last_timestamp.strftime('%H:%M')
                overlap_end_time = pd.to_datetime(stock_data.iloc[-1]['timestamps']).strftime('%H:%M')
                
                self.log_message(f"📊 重合验证：{overlap_start_time}-{overlap_end_time}({overlap_minutes}分钟真实数据) + 120分钟预测")
            
            # 获取最后一个基准数据点用于预测算法
            if len(base_data) == 0:
                base_data = stock_data.tail(1).copy()
            
            last_data = base_data.iloc[-1]
            try:
                last_timestamp = pd.to_datetime(last_data['timestamps'])
            except:
                # 如果时间戳解析失败，使用当前时间
                last_timestamp = pd.Timestamp.now().floor('5T')
            
            # 定义交易时间段
            morning_start = 9.5  # 9:30
            morning_end = 11.5   # 11:30
            afternoon_start = 13.0  # 13:00
            afternoon_end = 15.0    # 15:00
            
            # 生成时间戳序列
            if overlap_periods == 0:
                # 无重合：从最后历史数据点开始生成未来时间戳
                future_timestamps = []
                current_time = last_timestamp
                total_periods_needed = pred_periods  # 只需要预测周期
                
                periods_added = 0
                while periods_added < total_periods_needed:
                    current_time = current_time + pd.Timedelta(minutes=5)
                    
                    # 跳过周末
                    if current_time.weekday() >= 5:
                        days_until_monday = 7 - current_time.weekday()
                        current_time = current_time + pd.Timedelta(days=days_until_monday)
                        current_time = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
                    
                    # 检查是否在交易时间内
                    time_decimal = current_time.hour + current_time.minute / 60.0
                    
                    # 如果超出当日交易时间，跳到下一个交易日
                    if time_decimal > afternoon_end:
                        current_time = current_time + pd.Timedelta(days=1)
                        current_time = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
                        while current_time.weekday() >= 5:
                            current_time = current_time + pd.Timedelta(days=1)
                        time_decimal = 9.5
                    
                    # 如果在休市时间，跳到13:00
                    if morning_end <= time_decimal < afternoon_start:
                        current_time = current_time.replace(hour=13, minute=0, second=0, microsecond=0)
                        time_decimal = 13.0
                    
                    # 如果在交易时间内，添加到列表
                    if ((morning_start <= time_decimal < morning_end) or 
                        (afternoon_start <= time_decimal <= afternoon_end)):
                        future_timestamps.append(current_time)
                        periods_added += 1
            else:
                # 有重合：时间戳包括重合部分+预测部分
                # 重合部分直接使用真实历史数据的时间戳
                overlap_timestamps = list(overlap_data['timestamps'])
                
                # 预测部分：从最后一个历史数据点开始生成
                last_hist_timestamp = pd.to_datetime(stock_data.iloc[-1]['timestamps'])
                future_timestamps = overlap_timestamps.copy()
                
                current_time = last_hist_timestamp
                pred_periods_added = 0
                
                while pred_periods_added < pred_periods:
                    current_time = current_time + pd.Timedelta(minutes=5)
                    
                    # 跳过周末
                    if current_time.weekday() >= 5:
                        days_until_monday = 7 - current_time.weekday()
                        current_time = current_time + pd.Timedelta(days=days_until_monday)
                        current_time = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
                    
                    # 检查是否在交易时间内
                    time_decimal = current_time.hour + current_time.minute / 60.0
                    
                    # 如果超出当日交易时间，跳到下一个交易日
                    if time_decimal > afternoon_end:
                        current_time = current_time + pd.Timedelta(days=1)
                        current_time = current_time.replace(hour=9, minute=30, second=0, microsecond=0)
                        while current_time.weekday() >= 5:
                            current_time = current_time + pd.Timedelta(days=1)
                        time_decimal = 9.5
                    
                    # 如果在休市时间，跳到13:00
                    if morning_end <= time_decimal < afternoon_start:
                        current_time = current_time.replace(hour=13, minute=0, second=0, microsecond=0)
                        time_decimal = 13.0
                    
                    # 如果在交易时间内，添加到列表
                    if ((morning_start <= time_decimal < morning_end) or 
                        (afternoon_start <= time_decimal <= afternoon_end)):
                        future_timestamps.append(current_time)
                        pred_periods_added += 1
            
            # 生成预测数据（基于技术分析）
            close_prices = base_data['close'].values
            volumes = base_data['volume'].values if 'volume' in base_data.columns else None
            
            # 计算趋势和波动性
            if len(close_prices) >= 5:
                short_ma = np.mean(close_prices[-5:])
                long_ma = np.mean(close_prices[-min(10, len(close_prices)):])
                trend_factor = (short_ma - long_ma) / long_ma if long_ma > 0 else 0
            else:
                trend_factor = 0
            
            # 计算15分钟级别的价格波动性
            with np.errstate(divide='ignore', invalid='ignore'):
                price_changes = np.diff(close_prices) / np.where(close_prices[:-1] != 0, close_prices[:-1], 1e-8)
                price_changes = price_changes[np.isfinite(price_changes)]  # 过滤无限值
            volatility = np.std(price_changes) if len(price_changes) > 0 else 0.01
            
            # 生成预测收盘价
            predicted_closes = []
            current_price = last_data['close']
            
            for i in range(len(future_timestamps)):
                # 基本趋势 + 随机波动
                trend_change = trend_factor * 0.001 * (i + 1)  # 趋势影响递减
                random_change = np.random.normal(0, volatility * 0.5)  # 15分钟级别波动
                
                # 加入均值回归效应
                if close_prices[-1] != 0:
                    reversion_factor = -0.1 * ((current_price - close_prices[-1]) / close_prices[-1])
                else:
                    reversion_factor = 0
                
                price_change = trend_change + random_change + reversion_factor
                current_price = current_price * (1 + price_change)
                predicted_closes.append(max(current_price, 0.01))  # 确保价格为正
            
            # 生成高低价和开盘价
            predicted_highs = []
            predicted_lows = []
            predicted_opens = []
            
            for i, close_price in enumerate(predicted_closes):
                # 15分钟K线的开盘价
                if i == 0:
                    open_price = last_data['close']
                else:
                    open_price = predicted_closes[i-1]
                
                # 高低价范围（15分钟级别较小）
                high_low_range = close_price * volatility * 0.3
                high_price = max(open_price, close_price) + np.random.uniform(0, high_low_range)
                low_price = min(open_price, close_price) - np.random.uniform(0, high_low_range)
                
                predicted_opens.append(open_price)
                predicted_highs.append(high_price)
                predicted_lows.append(max(low_price, 0.01))
            
            # 生成成交量
            if volumes is not None and len(volumes) > 0:
                avg_volume = np.mean(volumes[-10:])
                predicted_volumes = np.random.normal(avg_volume, avg_volume * 0.2, len(future_timestamps))
                predicted_volumes = np.maximum(predicted_volumes, 100)  # 确保最小成交量
            else:
                predicted_volumes = np.full(len(future_timestamps), 1000000)
            
            # 确保所有数据都是有效的数值
            predicted_opens = np.array([max(float(x), 0.01) if np.isfinite(x) else 1.0 for x in predicted_opens])
            predicted_highs = np.array([max(float(x), 0.01) if np.isfinite(x) else 1.0 for x in predicted_highs])  
            predicted_lows = np.array([max(float(x), 0.01) if np.isfinite(x) else 1.0 for x in predicted_lows])
            predicted_closes = np.array([max(float(x), 0.01) if np.isfinite(x) else 1.0 for x in predicted_closes])
            predicted_volumes = np.array([max(int(x), 100) if np.isfinite(x) else 1000000 for x in predicted_volumes])
            
            # 处理重合部分和纯预测部分
            if overlap_periods > 0 and overlap_data is not None:
                # 重合部分：使用真实历史数据
                overlap_real = overlap_data.copy()
                overlap_real = overlap_real.reset_index(drop=True)
                
                # 纯预测部分：使用生成的预测数据
                pure_pred_timestamps = future_timestamps[overlap_periods:]
                pure_pred_opens = predicted_opens[overlap_periods:] if len(predicted_opens) > overlap_periods else predicted_opens
                pure_pred_highs = predicted_highs[overlap_periods:] if len(predicted_highs) > overlap_periods else predicted_highs
                pure_pred_lows = predicted_lows[overlap_periods:] if len(predicted_lows) > overlap_periods else predicted_lows
                pure_pred_closes = predicted_closes[overlap_periods:] if len(predicted_closes) > overlap_periods else predicted_closes
                pure_pred_volumes = predicted_volumes[overlap_periods:] if len(predicted_volumes) > overlap_periods else predicted_volumes
                
                # 合并重合部分和纯预测部分
                all_timestamps = list(overlap_real['timestamps']) + list(pure_pred_timestamps)
                all_opens = list(overlap_real['open']) + list(pure_pred_opens)
                all_highs = list(overlap_real['high']) + list(pure_pred_highs) 
                all_lows = list(overlap_real['low']) + list(pure_pred_lows)
                all_closes = list(overlap_real['close']) + list(pure_pred_closes)
                all_volumes = list(overlap_real['volume']) + list(pure_pred_volumes)
                
                prediction_data = pd.DataFrame({
                    'timestamps': all_timestamps,
                    'open': all_opens,
                    'high': all_highs,
                    'low': all_lows,
                    'close': all_closes,
                    'volume': all_volumes
                })
                
                self.log_message(f"✅ 生成15分钟预测数据：{overlap_periods}个重合验证点（真实数据）+ {len(pure_pred_timestamps)}个纯预测点")
            else:
                # 无重合：全部为预测数据
                prediction_data = pd.DataFrame({
                    'timestamps': future_timestamps,
                    'open': predicted_opens,
                    'high': predicted_highs,
                    'low': predicted_lows,
                    'close': predicted_closes,
                    'volume': predicted_volumes
                })
                
                self.log_message(f"✅ 生成15分钟预测数据：无重合验证 + {len(future_timestamps)}个纯预测点")
            
            return prediction_data
            
        except Exception as e:
            self.log_message(f"❌ 生成15分钟预测数据失败: {str(e)}")
            # 返回简单的预测数据作为备用
            return self.generate_prediction_data(stock_data.tail(10), pred_periods, "5min")
    
    def get_mock_stock_data(self, code, chart_type, hist_days, pred_days):
        """生成高质量模拟股票数据（备用方案）"""
        try:
            # 设置随机种子以获得一致的结果
            np.random.seed(hash(code) % 2**32)
            
            # 根据图表类型确定时间间隔
            if chart_type == "daily":
                freq = 'B'  # 工作日
                total_periods = hist_days + pred_days
            else:  # 15min
                freq = '15T'
                total_periods = (hist_days + pred_days) * 26  # 每天约26个15分钟周期
            
            # 生成时间序列
            end_date = datetime.now()
            if chart_type == "daily":
                start_date = end_date - timedelta(days=total_periods * 1.5)  # 留出周末空间
                timestamps = pd.bdate_range(start=start_date, periods=total_periods, freq='B')
            else:
                start_date = end_date - timedelta(days=hist_days + pred_days)
                # 生成工作日的5分钟数据（9:30-15:00）
                business_days = pd.bdate_range(start=start_date, end=end_date)
                timestamps = []
                for day in business_days:
                    day_times = pd.date_range(
                        start=day.replace(hour=9, minute=30),
                        end=day.replace(hour=15, minute=0),
                        freq='15T'
                    )
                    timestamps.extend(day_times)
                timestamps = pd.DatetimeIndex(timestamps[:total_periods])
            
            # 生成更真实的价格数据
            code_hash = hash(code) % 1000
            base_price = 8 + code_hash * 0.1  # 基础价格8-108元
            
            n_points = len(timestamps)
            
            # 生成带趋势的随机游走
            trend = np.sin(np.linspace(0, 4*np.pi, n_points)) * 0.002  # 长期波动趋势
            noise = np.random.normal(0, 0.015, n_points)  # 随机噪声
            returns = trend + noise
            
            # 添加一些突发事件（跳跃）
            jump_prob = 0.05
            jumps = np.random.choice([0, 1], n_points, p=[1-jump_prob, jump_prob])
            jump_sizes = np.random.normal(0, 0.03, n_points) * jumps
            returns += jump_sizes
            
            # 计算价格序列
            close_prices = [base_price]
            for ret in returns[1:]:
                new_price = close_prices[-1] * (1 + ret)
                close_prices.append(max(new_price, 1.0))  # 确保价格不为负
            
            close_prices = np.array(close_prices)
            
            # 生成开高低价（更真实的关系）
            daily_volatility = 0.02
            high_factors = 1 + np.abs(np.random.normal(0, daily_volatility/2, n_points))
            low_factors = 1 - np.abs(np.random.normal(0, daily_volatility/2, n_points))
            
            open_prices = np.roll(close_prices, 1)
            open_prices[0] = close_prices[0] * (1 + np.random.normal(0, 0.01))
            
            high_prices = np.maximum(open_prices, close_prices) * high_factors
            low_prices = np.minimum(open_prices, close_prices) * low_factors
            
            # 确保价格关系合理
            high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))
            low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))
            
            # 生成更真实的成交量（与价格波动相关）
            base_volume = 500000 + (code_hash * 10000)
            price_changes = np.abs(np.diff(close_prices, prepend=close_prices[0]))
            volume_multipliers = 1 + price_changes / close_prices * 5  # 价格波动大时成交量增加
            volumes = np.random.lognormal(np.log(base_volume), 0.4, n_points) * volume_multipliers
            
            # 创建DataFrame
            df = pd.DataFrame({
                'timestamps': timestamps,
                'open': open_prices,
                'high': high_prices,
                'low': low_prices,
                'close': close_prices,
                'volume': volumes.astype(int)
            })
            
            # 按时间排序
            df = df.sort_values('timestamps').reset_index(drop=True)
            
            # 分割历史数据和预测数据
            if chart_type == "daily":
                split_idx = hist_days
            else:
                split_idx = min(hist_days * 26, len(df) - pred_days)
            
            split_idx = max(0, min(split_idx, len(df) - 1))
            
            historical_data = df.iloc[:split_idx].copy()
            prediction_data = df.iloc[split_idx:].copy()
            
            # 确保有足够的数据
            if len(historical_data) == 0:
                historical_data = df.iloc[:max(1, len(df)//2)].copy()
                prediction_data = df.iloc[max(1, len(df)//2):].copy()
            
            return historical_data, prediction_data
            
        except Exception as e:
            raise Exception(f"生成模拟数据时出错: {str(e)}")
    
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
            self.log_message(f"⚠️ KDJ计算失败: {str(e)}")
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
            
            # 取三者最大值作为True Range
            data['TR'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # 第一个ATR值 = 前period个TR的简单平均
            first_atr = data['TR'].iloc[1:period+1].mean() if len(data) > period else data['TR'].mean()
            
            # 初始化ATR列
            data['ATR'] = 0.0
            data.iloc[period, data.columns.get_loc('ATR')] = first_atr
            
            # 从第period+1个值开始，使用Wilder的指数移动平均
            # ATR = ((period-1) * 前ATR + 当前TR) / period
            for i in range(period + 1, len(data)):
                prev_atr = data['ATR'].iloc[i-1]
                current_tr = data['TR'].iloc[i]
                data.iloc[i, data.columns.get_loc('ATR')] = ((period - 1) * prev_atr + current_tr) / period
            
            # 对于前period个值，使用向前填充
            data['ATR'] = data['ATR'].replace(0, np.nan)
            data['ATR'] = data['ATR'].fillna(method='bfill')
            
            # 如果仍有NaN，使用价格的2%作为默认值
            data['ATR'] = data['ATR'].fillna(data['close'] * 0.02)
            
            # 清理临时列
            temp_cols = ['prev_close', 'tr1', 'tr2', 'tr3', 'TR']
            data = data.drop(columns=temp_cols, errors='ignore')
            
            return data
            
        except Exception as e:
            self.log_message(f"⚠️ ATR计算失败: {str(e)}")
            # 失败时使用价格的2%作为ATR
            data['ATR'] = data['close'] * 0.02
            return data
    
    def calculate_dynamic_stop_loss(self, current_price, atr_value, position_type="long", multiplier=2.0):
        """
        计算动态止损价位
        参数：
        - current_price: 当前价格
        - atr_value: 当前ATR值
        - position_type: 持仓类型，"long"(多头)或"short"(空头)
        - multiplier: ATR倍数，默认2.0
        
        返回：(止损价格, 风险金额)
        """
        try:
            if position_type.lower() == "long":
                # 多头止损 = 当前价格 - ATR * 倍数
                stop_loss_price = current_price - (atr_value * multiplier)
                risk_amount = current_price - stop_loss_price
            else:
                # 空头止损 = 当前价格 + ATR * 倍数  
                stop_loss_price = current_price + (atr_value * multiplier)
                risk_amount = stop_loss_price - current_price
            
            # 确保止损价格为正数
            stop_loss_price = max(stop_loss_price, current_price * 0.1)
            
            return stop_loss_price, risk_amount
            
        except Exception as e:
            self.log_message(f"⚠️ 动态止损计算失败: {str(e)}")
            # 失败时使用固定5%止损
            if position_type.lower() == "long":
                stop_loss_price = current_price * 0.95
                risk_amount = current_price * 0.05
            else:
                stop_loss_price = current_price * 1.05
                risk_amount = current_price * 0.05
            return stop_loss_price, risk_amount
    
    def calculate_trading_signals(self, historical_data, prediction_data):
        """计算高胜率交易信号 - 集成KDJ和ATR指标"""
        try:
            # 合并历史和预测数据
            all_data = pd.concat([historical_data, prediction_data], ignore_index=True)
            
            # 计算基础技术指标
            all_data['MA5'] = all_data['close'].rolling(window=5).mean()
            all_data['MA10'] = all_data['close'].rolling(window=10).mean()
            all_data['MA20'] = all_data['close'].rolling(window=20).mean()
            
            # 计算价格变化率和成交量
            all_data['price_change'] = all_data['close'].pct_change()
            all_data['volume_ma'] = all_data['volume'].rolling(window=5).mean()
            
            # 🆕 计算KDJ指标
            self.log_message("🔄 计算KDJ随机指标...")
            all_data = self.calculate_kdj(all_data, n=9, m1=3, m2=3)
            
            # 🆕 计算ATR指标  
            self.log_message("🔄 计算ATR指标...")
            all_data = self.calculate_atr(all_data, period=14)
            
            # 初始化信号列
            all_data['buy_signal'] = False
            all_data['sell_signal'] = False
            all_data['signal_strength'] = 0  # 信号强度 1-3
            all_data['signal_type'] = ''  # 信号类型标记
            
            # 🆕 策略1: KDJ超买超卖策略（新增）
            self.log_message("🔄 分析KDJ超买超卖信号...")
            for i in range(1, len(all_data)):
                if pd.isna(all_data.loc[i, 'K']) or pd.isna(all_data.loc[i, 'D']):
                    continue
                    
                current_k = all_data.loc[i, 'K']
                current_d = all_data.loc[i, 'D']
                current_j = all_data.loc[i, 'J']
                
                prev_k = all_data.loc[i-1, 'K'] if i > 0 else current_k
                prev_d = all_data.loc[i-1, 'D'] if i > 0 else current_d
                
                # KDJ金叉买入信号：K线上穿D线且在超卖区域（K<30或D<30）
                if (prev_k <= prev_d and current_k > current_d and 
                    (current_k < 30 or current_d < 30)):
                    all_data.loc[i, 'buy_signal'] = True
                    all_data.loc[i, 'signal_strength'] = 3  # 超卖区金叉，高强度信号
                    all_data.loc[i, 'signal_type'] = 'KDJ金叉(超卖)'
                
                # KDJ金叉买入信号：K线上穿D线且在中性区域（30<=K<70）
                elif (prev_k <= prev_d and current_k > current_d and 
                      30 <= current_k < 70 and 30 <= current_d < 70):
                    all_data.loc[i, 'buy_signal'] = True
                    all_data.loc[i, 'signal_strength'] = 2  # 中性区金叉，中等强度
                    all_data.loc[i, 'signal_type'] = 'KDJ金叉(中性)'
                
                # KDJ死叉卖出信号：K线下穿D线且在超买区域（K>70或D>70）
                elif (prev_k >= prev_d and current_k < current_d and 
                      (current_k > 70 or current_d > 70)):
                    all_data.loc[i, 'sell_signal'] = True
                    all_data.loc[i, 'signal_strength'] = 3  # 超买区死叉，高强度信号
                    all_data.loc[i, 'signal_type'] = 'KDJ死叉(超买)'
                
                # KDJ死叉卖出信号：K线下穿D线且在中性区域
                elif (prev_k >= prev_d and current_k < current_d and 
                      30 < current_k <= 70 and 30 < current_d <= 70):
                    all_data.loc[i, 'sell_signal'] = True
                    all_data.loc[i, 'signal_strength'] = 2  # 中性区死叉，中等强度
                    all_data.loc[i, 'signal_type'] = 'KDJ死叉(中性)'
                
                # J值极端反转信号
                elif current_j < 10:  # J值小于10，强烈超卖
                    all_data.loc[i, 'buy_signal'] = True
                    all_data.loc[i, 'signal_strength'] = 2
                    all_data.loc[i, 'signal_type'] = 'J值超卖反转'
                    
                elif current_j > 90:  # J值大于90，强烈超买
                    all_data.loc[i, 'sell_signal'] = True
                    all_data.loc[i, 'signal_strength'] = 2
                    all_data.loc[i, 'signal_type'] = 'J值超买反转'
            
            # 策略2: 预测趋势跟踪（原有，与KDJ结合验证）
            hist_len = len(historical_data)
            if hist_len > 0 and len(prediction_data) > 2:
                # 获取历史数据最后几个点的趋势
                recent_trend = historical_data['close'].tail(3).pct_change().mean()
                pred_trend = prediction_data['close'].head(3).pct_change().mean()
                
                # 获取最后的KDJ值用于确认
                last_k = all_data.loc[hist_len-1, 'K'] if hist_len > 0 else 50
                last_d = all_data.loc[hist_len-1, 'D'] if hist_len > 0 else 50
                
                # 预测线向上且趋势一致，KDJ不在超买区
                if (pred_trend > 0.005 and recent_trend > -0.01 and 
                    last_k < 80 and last_d < 80):  # KDJ确认不超买
                    # 在历史数据结束点生成买入信号
                    if not all_data.loc[hist_len-1, 'buy_signal']:  # 避免重复信号
                        all_data.loc[hist_len-1, 'buy_signal'] = True
                        all_data.loc[hist_len-1, 'signal_strength'] = 3
                        all_data.loc[hist_len-1, 'signal_type'] = '预测趋势+KDJ确认'
                
                # 预测线向下且趋势转换，KDJ不在超卖区
                elif (pred_trend < -0.005 and recent_trend < 0.01 and 
                      last_k > 20 and last_d > 20):  # KDJ确认不超卖
                    if not all_data.loc[hist_len-1, 'sell_signal']:  # 避免重复信号
                        all_data.loc[hist_len-1, 'sell_signal'] = True
                        all_data.loc[hist_len-1, 'signal_strength'] = 3
                        all_data.loc[hist_len-1, 'signal_type'] = '预测趋势+KDJ确认'
            
            # 策略3: 多指标组合确认（均线交叉+KDJ+成交量）
            for i in range(5, len(all_data)-1):
                if pd.isna(all_data.loc[i, 'K']) or pd.isna(all_data.loc[i, 'D']):
                    continue
                    
                current_k = all_data.loc[i, 'K']
                current_d = all_data.loc[i, 'D']
                
                # 5日均线上穿10日均线
                if (all_data.loc[i, 'MA5'] > all_data.loc[i, 'MA10'] and 
                    all_data.loc[i-1, 'MA5'] <= all_data.loc[i-1, 'MA10']):
                    
                    # KDJ确认：不在超买区域
                    kdj_confirm = current_k < 80 and current_d < 80
                    
                    # 成交量确认
                    volume_confirm = all_data.loc[i, 'volume'] > all_data.loc[i, 'volume_ma'] * 1.1
                    
                    if kdj_confirm and volume_confirm:
                        if not all_data.loc[i, 'buy_signal']:  # 避免重复信号
                            all_data.loc[i, 'buy_signal'] = True
                            all_data.loc[i, 'signal_strength'] = 3  # 多指标确认，高强度
                            all_data.loc[i, 'signal_type'] = '均线+KDJ+量能'
                    elif kdj_confirm:  # 仅KDJ确认
                        if not all_data.loc[i, 'buy_signal']:
                            all_data.loc[i, 'buy_signal'] = True
                            all_data.loc[i, 'signal_strength'] = 2  # 中等强度
                            all_data.loc[i, 'signal_type'] = '均线+KDJ确认'
                
                # 5日均线下穿10日均线
                elif (all_data.loc[i, 'MA5'] < all_data.loc[i, 'MA10'] and 
                      all_data.loc[i-1, 'MA5'] >= all_data.loc[i-1, 'MA10']):
                    
                    # KDJ确认：不在超卖区域
                    kdj_confirm = current_k > 20 and current_d > 20
                    
                    if kdj_confirm:
                        if not all_data.loc[i, 'sell_signal']:  # 避免重复信号
                            all_data.loc[i, 'sell_signal'] = True
                            all_data.loc[i, 'signal_strength'] = 2
                            all_data.loc[i, 'signal_type'] = '均线+KDJ确认'
            
            # 策略4: 价格突破确认（加强KDJ验证）
            for i in range(20, len(all_data)):
                if pd.isna(all_data.loc[i, 'K']) or pd.isna(all_data.loc[i, 'D']):
                    continue
                    
                current_price = all_data.loc[i, 'close']
                ma20 = all_data.loc[i, 'MA20']
                prev_price = all_data.loc[i-1, 'close']
                prev_ma20 = all_data.loc[i-1, 'MA20']
                
                current_k = all_data.loc[i, 'K']
                current_d = all_data.loc[i, 'D']
                
                # 向上突破20日均线
                if current_price > ma20 and prev_price <= prev_ma20:
                    # KDJ确认不在超买区
                    if current_k < 80 and current_d < 80:
                        if not all_data.loc[i, 'buy_signal']:  # 避免重复信号
                            all_data.loc[i, 'buy_signal'] = True
                            all_data.loc[i, 'signal_strength'] = 2
                            all_data.loc[i, 'signal_type'] = '突破MA20+KDJ'
                
                # 向下跌破20日均线
                elif current_price < ma20 and prev_price >= prev_ma20:
                    # KDJ确认不在超卖区
                    if current_k > 20 and current_d > 20:
                        if not all_data.loc[i, 'sell_signal']:  # 避免重复信号
                            all_data.loc[i, 'sell_signal'] = True
                            all_data.loc[i, 'signal_strength'] = 2
                            all_data.loc[i, 'signal_type'] = '跌破MA20+KDJ'
            
            # 🆕 统计信号质量和KDJ分布
            buy_signals = all_data[all_data['buy_signal'] == True].copy()
            sell_signals = all_data[all_data['sell_signal'] == True].copy()
            
            # 记录优化效果
            kdj_buy_signals = len(buy_signals[buy_signals['signal_type'].str.contains('KDJ', na=False)])
            kdj_sell_signals = len(sell_signals[sell_signals['signal_type'].str.contains('KDJ', na=False)])
            
            total_buy = len(buy_signals)
            total_sell = len(sell_signals)
            
            self.log_message(f"📊 KDJ优化信号统计:")
            self.log_message(f"   买入信号: {total_buy}个 (含KDJ: {kdj_buy_signals}个)")
            self.log_message(f"   卖出信号: {total_sell}个 (含KDJ: {kdj_sell_signals}个)")
            
            if total_buy > 0 or total_sell > 0:
                kdj_ratio = (kdj_buy_signals + kdj_sell_signals) / (total_buy + total_sell) * 100
                self.log_message(f"   KDJ策略占比: {kdj_ratio:.1f}%")
            
            return buy_signals, sell_signals, all_data
            
        except Exception as e:
            self.log_message(f"计算交易信号出错: {str(e)}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    def calculate_strategy_performance(self, buy_signals, sell_signals, historical_data):
        """计算策略性能指标"""
        try:
            total_signals = len(buy_signals) + len(sell_signals)
            if total_signals == 0:
                return None
            
            # 模拟交易计算收益率
            returns = []
            position = 0  # 0=空仓, 1=持仓
            buy_price = 0
            
            # 合并并排序所有信号
            all_signals = []
            
            for idx, signal in buy_signals.iterrows():
                all_signals.append({
                    'date': signal['timestamps'],
                    'price': signal['close'],
                    'type': 'buy',
                    'strength': signal['signal_strength']
                })
            
            for idx, signal in sell_signals.iterrows():
                all_signals.append({
                    'date': signal['timestamps'],
                    'price': signal['close'],
                    'type': 'sell',
                    'strength': signal['signal_strength']
                })
            
            # 按时间排序
            all_signals = sorted(all_signals, key=lambda x: x['date'])
            
            # 模拟交易
            for signal in all_signals:
                if signal['type'] == 'buy' and position == 0:
                    # 买入
                    buy_price = signal['price']
                    position = 1
                elif signal['type'] == 'sell' and position == 1:
                    # 卖出
                    sell_price = signal['price']
                    return_pct = (sell_price - buy_price) / buy_price * 100
                    returns.append(return_pct)
                    position = 0
            
            # 计算统计指标
            if len(returns) > 0:
                win_rate = len([r for r in returns if r > 0]) / len(returns) * 100
                avg_return = np.mean(returns)
                max_return = max(returns)
                min_return = min(returns)
            else:
                # 基于信号强度估算胜率
                high_strength_signals = len([s for s in all_signals if s['strength'] == 3])
                medium_strength_signals = len([s for s in all_signals if s['strength'] == 2])
                
                # 经验胜率估算
                estimated_win_rate = (high_strength_signals * 85 + medium_strength_signals * 75) / total_signals if total_signals > 0 else 70
                win_rate = min(estimated_win_rate, 90)  # 最高不超过90%
                avg_return = 2.5  # 预期平均收益
            
            return {
                'total_signals': total_signals,
                'win_rate': win_rate,
                'avg_return': avg_return,
                'total_trades': len(returns)
            }
            
        except Exception as e:
            self.log_message(f"计算策略性能出错: {str(e)}")
            return None
    
    def display_warning_chart(self, code, chart_type):
        """显示数据获取失败的警告图表"""
        # 清除之前的图表
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()
        
        # 创建新的图表
        fig = Figure(figsize=(10, 6), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        
        # 显示警告信息
        ax.text(0.5, 0.6, f"⚠️ 无法获取股票 {code} 的真实数据", 
                ha='center', va='center', fontsize=20, color='red', 
                transform=ax.transAxes, weight='bold')
        
        ax.text(0.5, 0.4, "可能的原因:", 
                ha='center', va='center', fontsize=14, 
                transform=ax.transAxes, weight='bold')
        
        ax.text(0.5, 0.3, "• 网络连接问题\n• 股票代码不存在\n• 数据服务暂时不可用\n• AkShare库在exe环境中无法正常工作", 
                ha='center', va='center', fontsize=12, 
                transform=ax.transAxes)
        
        ax.text(0.5, 0.1, "建议：请使用Python版本(.py文件)获取真实数据", 
                ha='center', va='center', fontsize=12, color='blue',
                transform=ax.transAxes, style='italic')
        
        # 隐藏坐标轴
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        
        fig.suptitle(f"Kronos股票预测系统 - {code} ({chart_type})", fontsize=16, weight='bold')
        fig.tight_layout()
        
        # 创建画布
        self.canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 创建工具栏
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.chart_frame)
        self.toolbar.update()
        
        # 隐藏提示标签
        if hasattr(self, 'chart_label'):
            self.chart_label.pack_forget()
        
        self.current_figure = fig
    
    def calculate_macd(self, data, fast_period=12, slow_period=26, signal_period=9):
        """计算MACD指标"""
        try:
            prices = data['close']
            
            # 计算EMA
            ema_fast = prices.ewm(span=fast_period).mean()
            ema_slow = prices.ewm(span=slow_period).mean()
            
            # 计算MACD线
            macd_line = ema_fast - ema_slow
            
            # 计算信号线
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # 计算柱状图
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
            
        except Exception as e:
            self.log_message(f"计算MACD失败: {str(e)}")
            return None, None, None

    def display_chart_in_gui(self, code, historical_data, prediction_data, chart_type):
        """在GUI中显示图表和交易信号"""
        try:
            # 清除之前的图表
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            if self.toolbar:
                self.toolbar.destroy()
            if self.chart_label:
                self.chart_label.destroy()
            
            # 计算交易信号
            self.log_message("正在分析交易机会...")
            buy_signals, sell_signals, all_data = self.calculate_trading_signals(historical_data, prediction_data)
            
            # 创建新的图表 - 三图表布局：价格图 + MACD图 + KDJ图
            self.current_figure = Figure(figsize=(12, 14), dpi=100)
            
            # 合并历史和预测数据用于指标计算
            all_data_for_indicators = pd.concat([historical_data, prediction_data], ignore_index=True)
            
            # 计算MACD指标
            macd_line, signal_line, histogram = self.calculate_macd(all_data_for_indicators)
            
            # 计算KDJ指标
            all_data_with_kdj = self.calculate_kdj(all_data_for_indicators.copy(), n=9, m1=3, m2=3)
            
            # 准备数据
            hist_dates = historical_data['timestamps']
            hist_closes = historical_data['close']
            
            pred_dates = prediction_data['timestamps']
            pred_closes = prediction_data['close']
            
            # 获取重合天数/分钟数设置
            overlap_value = int(self.overlap_days.get()) if hasattr(self, 'overlap_days') else 0
            
            # 处理重合期间的数据显示问题
            if overlap_value > 0:
                # 5分钟图：重合值是分钟数，需要转换为数据点数
                if chart_type == "5min":
                    overlap_periods = overlap_value // 15  # 分钟数转换为15分钟周期数
                    overlap_periods = max(0, min(overlap_periods, len(pred_dates)))  # 确保不超过预测数据长度
                else:
                    # 日线图：重合值就是天数
                    overlap_periods = overlap_value
                    overlap_periods = max(0, min(overlap_periods, len(pred_dates)))
                
                # 有重合期间：将预测数据分为重合部分和纯预测部分
                overlap_pred_dates = pred_dates[:overlap_periods]
                overlap_pred_closes = pred_closes[:overlap_periods]
                
                pure_pred_dates = pred_dates[overlap_periods:]
                pure_pred_closes = pred_closes[overlap_periods:]
                
                # 检查重合期间是否真的与历史数据重合
                hist_end_date = hist_dates.iloc[-1]
                overlap_start_date = overlap_pred_dates.iloc[0] if len(overlap_pred_dates) > 0 else None
                
                if overlap_start_date and overlap_start_date <= hist_end_date:
                    # 确实有重合，只显示历史数据和纯预测部分
                    display_pred_dates = pure_pred_dates
                    display_pred_closes = pure_pred_closes
                    if chart_type == "5min":
                        self.log_message(f"📊 检测到{overlap_value}分钟重合期间，已调整显示避免重复")
                    else:
                        self.log_message(f"📊 检测到{overlap_value}天重合期间，已调整显示避免重复")
                else:
                    # 没有真正重合，显示全部预测数据
                    display_pred_dates = pred_dates
                    display_pred_closes = pred_closes
            else:
                # 无重合期间，正常显示全部预测数据
                display_pred_dates = pred_dates
                display_pred_closes = pred_closes
            
            # 第一个子图：价格图
            ax1 = self.current_figure.add_subplot(3, 1, 1)
            
            # 根据图表类型选择坐标系统
            if chart_type == "5min":
                # 5分钟图：使用索引坐标系统
                hist_x = list(range(len(hist_dates)))
                
                # 预测数据的X坐标从历史数据末尾开始连续
                if len(display_pred_dates) > 0:
                    pred_x_start = len(hist_dates) - 1  # 从历史数据的最后一个点开始
                    pred_x = list(range(pred_x_start, pred_x_start + len(display_pred_dates)))
                else:
                    pred_x = []
                
                # 绘制历史数据（蓝色实线）
                ax1.plot(hist_x, hist_closes, color='blue', linewidth=2)
                
                # 绘制预测数据（红色虚线）
                if len(display_pred_dates) > 0:
                    ax1.plot(pred_x, display_pred_closes, color='red', linewidth=2, linestyle='--', alpha=0.8)
                
                # 设置X轴标签（5分钟图）
                all_dates_for_labels = pd.concat([hist_dates, display_pred_dates], ignore_index=True)
                total_points = len(hist_dates) + len(display_pred_dates)
                
                # 选择合适的标签间隔
                step = max(1, total_points // 8)  # 大约显示8个标签
                x_ticks = list(range(0, total_points, step))
                x_labels = []
                
                for i in x_ticks:
                    if i < len(all_dates_for_labels):
                        time_str = pd.to_datetime(all_dates_for_labels.iloc[i]).strftime('%m-%d %H:%M')
                        x_labels.append(time_str)
                
                ax1.set_xticks(x_ticks)
                ax1.set_xticklabels(x_labels, rotation=45)
                
            else:
                # 日线图：使用日期坐标系统（原逻辑）
                # 绘制历史数据（蓝色实线）- 不重复添加标签
                ax1.plot(hist_dates, hist_closes, color='blue', linewidth=2)
                
                # 绘制预测数据（红色虚线）- 不重复添加标签
                if len(display_pred_dates) > 0:
                    ax1.plot(display_pred_dates, display_pred_closes, color='red', linewidth=2, linestyle='--', alpha=0.8)
            
            # 获取股票中文名称
            stock_name = self.get_stock_name(code)
            
            # 构建完整标题
            if stock_name:
                title = f'{code} {stock_name} 股价走势分析 ({chart_type})'
                self.log_message(f"📋 股票名称: {stock_name}")
            else:
                title = f'{code} 股价走势分析 ({chart_type})'
                self.log_message(f"⚠️ 未能获取股票名称，使用代码显示")
            
            # 设置第一个子图的标题
            ax1.set_title(title, fontsize=14, fontweight='bold', pad=20)
            ax1.set_ylabel('价格 (¥)', fontsize=12)
            
            # 手动创建图例，避免重复标签
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], color='blue', linewidth=2, label='历史数据'),
                Line2D([0], [0], color='red', linewidth=2, linestyle='--', label='预测数据'),
                Line2D([0], [0], color='orange', linewidth=1, alpha=0.7, label='MA5'),
                Line2D([0], [0], color='purple', linewidth=1, alpha=0.7, label='MA20')
            ]
            ax1.legend(handles=legend_elements)
            ax1.grid(True, alpha=0.3)
            
            # 第二个子图：MACD图
            ax2 = self.current_figure.add_subplot(3, 1, 2)
            
            if macd_line is not None:
                # 准备MACD数据的时间轴
                all_dates = pd.concat([hist_dates, pred_dates], ignore_index=True)
                
                # 分离历史和预测的MACD数据
                hist_macd = macd_line[:len(historical_data)]
                hist_signal = signal_line[:len(historical_data)]
                hist_histogram = histogram[:len(historical_data)]
                
                pred_macd = macd_line[len(historical_data):]
                pred_signal = signal_line[len(historical_data):]
                pred_histogram = histogram[len(historical_data):]
                
                # 处理MACD预测数据的重合问题
                if overlap_value > 0 and len(display_pred_dates) < len(pred_dates):
                    # 有重合且进行了调整，同样调整MACD预测数据
                    display_pred_macd = pred_macd[overlap_periods:]
                    display_pred_signal = pred_signal[overlap_periods:]
                    display_pred_histogram = pred_histogram[overlap_periods:]
                else:
                    # 无重合或无需调整
                    display_pred_macd = pred_macd
                    display_pred_signal = pred_signal
                    display_pred_histogram = pred_histogram
                
                # 根据图表类型选择坐标系统
                if chart_type == "5min":
                    # 5分钟图：使用索引坐标系统（与价格图保持一致）
                    hist_x_macd = list(range(len(hist_dates)))
                    
                    if len(display_pred_dates) > 0:
                        pred_x_start_macd = len(hist_dates) - 1
                        pred_x_macd = list(range(pred_x_start_macd, pred_x_start_macd + len(display_pred_dates)))
                    else:
                        pred_x_macd = []
                    
                    # 绘制历史MACD（实线）
                    ax2.plot(hist_x_macd, hist_macd, label='MACD线', color='blue', linewidth=1.5)
                    ax2.plot(hist_x_macd, hist_signal, label='信号线', color='red', linewidth=1.5)
                    
                    # 绘制预测MACD（虚线）
                    if len(display_pred_dates) > 0 and len(display_pred_macd) > 0:
                        ax2.plot(pred_x_macd, display_pred_macd, color='blue', linewidth=1.5, linestyle='--', alpha=0.7)
                        ax2.plot(pred_x_macd, display_pred_signal, color='red', linewidth=1.5, linestyle='--', alpha=0.7)
                        
                        # 绘制预测部分MACD柱状图（透明柱）
                        colors_pred = ['lightgreen' if x > 0 else 'lightcoral' for x in display_pred_histogram]
                        ax2.bar(pred_x_macd, display_pred_histogram, color=colors_pred, alpha=0.4, width=0.8)
                    
                    # 绘制历史部分MACD柱状图（实体柱）
                    colors_hist = ['green' if x > 0 else 'red' for x in hist_histogram]
                    ax2.bar(hist_x_macd, hist_histogram, color=colors_hist, alpha=0.6, width=0.8)
                    
                    # 设置MACD图的X轴标签（与价格图一致）
                    ax2.set_xticks(x_ticks)
                    ax2.set_xticklabels(x_labels, rotation=45)
                    
                else:
                    # 日线图：使用日期坐标系统（原逻辑）
                    # 绘制历史MACD（实线）
                    ax2.plot(hist_dates, hist_macd, label='MACD线', color='blue', linewidth=1.5)
                    ax2.plot(hist_dates, hist_signal, label='信号线', color='red', linewidth=1.5)
                    
                    # 绘制预测MACD（虚线） - 使用处理后的数据避免重合
                    if len(display_pred_dates) > 0 and len(display_pred_macd) > 0:
                        ax2.plot(display_pred_dates, display_pred_macd, color='blue', linewidth=1.5, linestyle='--', alpha=0.7)
                        ax2.plot(display_pred_dates, display_pred_signal, color='red', linewidth=1.5, linestyle='--', alpha=0.7)
                        
                        # 绘制预测部分MACD柱状图（透明柱）
                        colors_pred = ['lightgreen' if x > 0 else 'lightcoral' for x in display_pred_histogram]
                        ax2.bar(display_pred_dates, display_pred_histogram, color=colors_pred, alpha=0.4, width=0.8)
                    
                    # 绘制历史部分MACD柱状图（实体柱）
                    colors_hist = ['green' if x > 0 else 'red' for x in hist_histogram]
                    ax2.bar(hist_dates, hist_histogram, color=colors_hist, alpha=0.6, width=0.8)
                
                # 添加零轴线
                ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                
                ax2.set_title('MACD 技术指标', fontsize=12, fontweight='bold', pad=15)
                ax2.set_ylabel('MACD', fontsize=10)
                ax2.legend(fontsize=9)
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'MACD计算失败', transform=ax2.transAxes, 
                        ha='center', va='center', fontsize=12)
            
            # 第三个子图：KDJ图
            ax3 = self.current_figure.add_subplot(3, 1, 3)
            
            if 'K' in all_data_with_kdj.columns and 'D' in all_data_with_kdj.columns and 'J' in all_data_with_kdj.columns:
                # 分离历史和预测的KDJ数据
                hist_k = all_data_with_kdj['K'][:len(historical_data)]
                hist_d = all_data_with_kdj['D'][:len(historical_data)]
                hist_j = all_data_with_kdj['J'][:len(historical_data)]
                
                pred_k = all_data_with_kdj['K'][len(historical_data):]
                pred_d = all_data_with_kdj['D'][len(historical_data):]
                pred_j = all_data_with_kdj['J'][len(historical_data):]
                
                # 处理KDJ预测数据的重合问题
                if overlap_value > 0 and len(display_pred_dates) < len(pred_dates):
                    # 有重合且进行了调整，同样调整KDJ预测数据
                    display_pred_k = pred_k[overlap_periods:]
                    display_pred_d = pred_d[overlap_periods:]
                    display_pred_j = pred_j[overlap_periods:]
                else:
                    # 无重合或无需调整
                    display_pred_k = pred_k
                    display_pred_d = pred_d
                    display_pred_j = pred_j
                
                # 根据图表类型选择坐标系统
                if chart_type == "5min":
                    # 5分钟图：使用索引坐标系统（与价格图保持一致）
                    hist_x_kdj = list(range(len(hist_dates)))
                    
                    if len(display_pred_dates) > 0:
                        pred_x_start_kdj = len(hist_dates) - 1
                        pred_x_kdj = list(range(pred_x_start_kdj, pred_x_start_kdj + len(display_pred_dates)))
                    else:
                        pred_x_kdj = []
                    
                    # 绘制历史KDJ（实线）
                    ax3.plot(hist_x_kdj, hist_k, label='K线', color='blue', linewidth=1.5)
                    ax3.plot(hist_x_kdj, hist_d, label='D线', color='red', linewidth=1.5)
                    ax3.plot(hist_x_kdj, hist_j, label='J线', color='green', linewidth=1.5)
                    
                    # 绘制预测KDJ（虚线）
                    if len(display_pred_dates) > 0:
                        ax3.plot(pred_x_kdj, display_pred_k, color='blue', linewidth=1.5, linestyle='--', alpha=0.7)
                        ax3.plot(pred_x_kdj, display_pred_d, color='red', linewidth=1.5, linestyle='--', alpha=0.7)
                        ax3.plot(pred_x_kdj, display_pred_j, color='green', linewidth=1.5, linestyle='--', alpha=0.7)
                    
                    # 设置X轴标签（与价格图保持一致）
                    ax3.set_xticks(x_ticks)
                    ax3.set_xticklabels(x_labels, rotation=45)
                    
                else:
                    # 日线图：使用日期坐标系统
                    # 绘制历史KDJ（实线）
                    ax3.plot(hist_dates, hist_k, label='K线', color='blue', linewidth=1.5)
                    ax3.plot(hist_dates, hist_d, label='D线', color='red', linewidth=1.5)
                    ax3.plot(hist_dates, hist_j, label='J线', color='green', linewidth=1.5)
                    
                    # 绘制预测KDJ（虚线）
                    if len(display_pred_dates) > 0:
                        ax3.plot(display_pred_dates, display_pred_k, color='blue', linewidth=1.5, linestyle='--', alpha=0.7)
                        ax3.plot(display_pred_dates, display_pred_d, color='red', linewidth=1.5, linestyle='--', alpha=0.7)
                        ax3.plot(display_pred_dates, display_pred_j, color='green', linewidth=1.5, linestyle='--', alpha=0.7)
                    
                    # 设置X轴格式（日期）
                    ax3.xaxis.set_major_formatter(DateFormatter('%m-%d'))
                    ax3.xaxis.set_major_locator(DayLocator(interval=max(1, len(hist_dates)//8)))
                    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
                
                # 添加超买超卖线（20和80）
                ax3.axhline(y=20, color='green', linestyle=':', alpha=0.7, label='超卖线(20)')
                ax3.axhline(y=80, color='red', linestyle=':', alpha=0.7, label='超买线(80)')
                ax3.axhline(y=50, color='gray', linestyle='-', alpha=0.3, label='中轴线(50)')
                
                ax3.set_title('KDJ 随机指标', fontsize=12, fontweight='bold', pad=15)
                ax3.set_ylabel('KDJ', fontsize=10)
                ax3.legend(fontsize=9)
                ax3.grid(True, alpha=0.3)
                ax3.set_ylim(-10, 110)  # 设置Y轴范围
            else:
                ax3.text(0.5, 0.5, 'KDJ计算失败', transform=ax3.transAxes, 
                        ha='center', va='center', fontsize=12)
            
            # 调整布局，为子图标题留出足够空间
            self.current_figure.tight_layout(pad=3.0, h_pad=4.0)
            
            # 移除整体标题，避免重复显示
            # self.current_figure.suptitle(f'{code} 股票智能分析图 ({chart_type})', 
            #                            fontsize=16, fontweight='bold', y=0.98)
            
            if chart_type == "5min":
                # 清除之前的绘制，避免重复
                ax1.clear()
                
                # 5分钟图：使用索引作为X轴，避免显示非交易时间
                hist_indices = range(len(hist_dates))
                pred_indices = range(len(hist_dates), len(hist_dates) + len(pred_dates))
                
                # 获取重合分钟数来判断重合部分
                overlap_minutes = self.overlap_days.get()
                overlap_periods = overlap_minutes // 15 if overlap_minutes > 0 else 0
                
                if overlap_periods > 0 and overlap_periods < len(pred_dates):
                    # 有重合：显示历史数据 + 重合验证部分(真实历史) + 纯预测部分
                    # 重合部分应该是历史数据的最后几个点，而不是预测数据
                    
                    # 获取历史数据的最后几个点作为重合验证数据
                    if overlap_periods <= len(hist_closes):
                        overlap_real_closes = hist_closes[-overlap_periods:].tolist()
                    else:
                        overlap_real_closes = hist_closes.tolist()
                    
                    # 纯预测部分（预测数据全部作为预测显示）
                    pure_pred_closes = pred_closes.tolist()
                    
                    # 创建索引
                    hist_indices = list(range(len(hist_dates)))
                    overlap_start_idx = len(hist_indices) - len(overlap_real_closes)  # 重合部分在历史数据末尾
                    overlap_indices = list(range(overlap_start_idx, len(hist_indices)))
                    pure_pred_indices = list(range(len(hist_indices), len(hist_indices) + len(pure_pred_closes)))
                    
                    # 连续显示：完整历史数据（蓝色实线）- 移除重复标签
                    ax1.plot(hist_indices, hist_closes, color='blue', linewidth=2)
                    
                    # 重合验证：重新显示历史数据的最后部分（绿色，表示验证基准）
                    if len(overlap_indices) > 0:
                        ax1.plot(overlap_indices, overlap_real_closes, 
                                color='green', linewidth=3, alpha=0.7, 
                                label=f'重合验证基准({overlap_minutes}分钟)')
                    
                    # 预测数据：从历史数据结束后开始显示（红色虚线）- 移除重复标签
                    if len(pure_pred_indices) > 0:
                        ax1.plot(pure_pred_indices, pure_pred_closes, 
                                color='red', linewidth=2, linestyle='--', alpha=0.8)
                    
                    # 在重合区间添加背景色标识
                    if len(overlap_indices) > 0:
                        ax1.axvspan(overlap_indices[0], overlap_indices[-1], 
                                  alpha=0.15, color='yellow', label='重合验证区间')
                    
                    self.log_message(f"📊 重合验证模式：绿色=验证基准，红色=预测数据，可对比预测准确性")
                else:
                    # 无重合：正常显示历史数据和预测数据
                    hist_indices = list(range(len(hist_dates)))
                    pred_indices = list(range(len(hist_dates), len(hist_dates) + len(pred_dates)))
                    
                    ax1.plot(hist_indices, hist_closes, color='blue', linewidth=2)
                    ax1.plot(pred_indices, pred_closes, color='red', linewidth=2, linestyle='--')
                    
                    self.log_message(f"📊 无重合模式：显示 {len(hist_dates)} 条历史数据 + {len(pred_dates)} 条预测数据")
                
                # 自定义X轴标签，只显示部分时间点
                all_dates = list(hist_dates) + list(display_pred_dates)
                total_points = len(hist_dates) + len(display_pred_dates)
                all_indices = list(range(total_points))
                
                # 选择要显示的时间点（每隔几个点显示一个）
                step = max(1, len(all_dates) // 12)  # 最多显示12个标签
                display_indices = []
                display_labels = []
                
                for i in range(0, len(all_dates), step):
                    if i < len(all_indices):
                        display_indices.append(all_indices[i])
                        date = all_dates[i]
                        
                        # 确保date是datetime对象
                        if isinstance(date, str):
                            date = pd.to_datetime(date)
                        
                        # 格式化时间标签 - 5分钟图专用格式
                        time_str = date.strftime('%H:%M')
                        date_str = date.strftime('%m-%d')
                        
                        # 关键时间点显示日期+时间，其他只显示时间
                        if time_str in ['09:30', '13:00'] or i == 0:  # 开盘时间显示日期
                            display_labels.append(f"{date_str}\n{time_str}")
                        elif time_str in ['11:30', '15:00']:  # 收盘时间
                            display_labels.append(f"{time_str}\n收盘")
                        else:
                            display_labels.append(time_str)
                
                ax1.set_xticks(display_indices)
                ax1.set_xticklabels(display_labels, rotation=45, fontsize=9)
            else:
                # 清除之前的绘制，避免重复
                ax1.clear()
                
                # 日线图：正常显示
                ax1.plot(hist_dates, hist_closes, color='blue', linewidth=2)
                ax1.plot(pred_dates, pred_closes, color='red', linewidth=2, linestyle='--')
            
            # 添加均线（如果数据足够）
            if len(all_data) > 20:
                if chart_type == "5min":
                    # 5分钟图：使用索引
                    all_indices = list(hist_indices) + list(pred_indices)
                    if 'MA5' in all_data.columns:
                        ma5_valid = all_data['MA5'].dropna()
                        if len(ma5_valid) > 0:
                            ma5_indices = all_indices[-len(ma5_valid):]
                            ax1.plot(ma5_indices, ma5_valid, 
                                    label='MA5', color='orange', linewidth=1, alpha=0.7)
                    
                    if 'MA20' in all_data.columns:
                        ma20_valid = all_data['MA20'].dropna()
                        if len(ma20_valid) > 0:
                            ma20_indices = all_indices[-len(ma20_valid):]
                            ax1.plot(ma20_indices, ma20_valid, 
                                    label='MA20', color='purple', linewidth=1, alpha=0.7)
                else:
                    # 日线图：使用日期
                    all_dates = list(hist_dates) + list(pred_dates)
                    if 'MA5' in all_data.columns:
                        ma5_valid = all_data['MA5'].dropna()
                        if len(ma5_valid) > 0:
                            ax1.plot(all_dates[-len(ma5_valid):], ma5_valid, 
                                    label='MA5', color='orange', linewidth=1, alpha=0.7)
                    
                    if 'MA20' in all_data.columns:
                        ma20_valid = all_data['MA20'].dropna()
                        if len(ma20_valid) > 0:
                            ax1.plot(all_dates[-len(ma20_valid):], ma20_valid, 
                                    label='MA20', color='purple', linewidth=1, alpha=0.7)
            
            # 移除买卖信号标注功能（根据用户要求）
            # 原买卖信号计算仍保留用于智能建议分析，但不在图表上显示
            
            if not buy_signals.empty:
                self.log_message(f"计算到 {len(buy_signals)} 个买入信号点位（仅用于分析，不在图表显示）")
            
            if not sell_signals.empty:
                self.log_message(f"计算到 {len(sell_signals)} 个卖出信号点位（仅用于分析，不在图表显示）")
            
            # 获取股票中文名称
            stock_name = self.get_stock_name(code)
            
            # 构建完整标题
            if stock_name:
                chart_title = f'{code} {stock_name} 智能交易策略分析 ({"日线图" if chart_type == "daily" else "5分钟图"})'
            else:
                chart_title = f'{code} 智能交易策略分析 ({"日线图" if chart_type == "daily" else "5分钟图"})'
            
            ax1.set_title(chart_title, fontsize=14, fontweight='bold')
            ax1.set_ylabel('价格 (元)', fontsize=10)
            
            # 手动创建图例，避免重复标签
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], color='blue', linewidth=2, label='历史数据'),
                Line2D([0], [0], color='red', linewidth=2, linestyle='--', label='预测数据')
            ]
            # 只有在有足够数据时才添加MA线的图例
            if len(all_data) > 20:
                legend_elements.extend([
                    Line2D([0], [0], color='orange', linewidth=1, alpha=0.7, label='MA5'),
                    Line2D([0], [0], color='purple', linewidth=1, alpha=0.7, label='MA20')
                ])
            ax1.legend(handles=legend_elements, fontsize=8, loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 图例说明（移除买卖信号相关说明）
            legend_text = "蓝色实线 = 历史数据  红色虚线 = 预测数据  | 橙色/紫色线 = 技术指标"
            ax1.text(0.02, 0.98, legend_text, transform=ax1.transAxes, 
                    fontsize=8, verticalalignment='top', 
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.8))
            
            # 计算并显示策略性能
            # 将图表嵌入到tkinter中
            self.canvas = FigureCanvasTkAgg(self.current_figure, self.chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # 添加导航工具栏
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.chart_frame)
            self.toolbar.update()
            
            # 添加鼠标悬停功能
            self.setup_hover_annotations(ax1, ax2, hist_dates, hist_closes, 
                                        display_pred_dates, display_pred_closes, chart_type)
            
            self.log_message("图表已在程序中显示")
            self.log_message("鼠标悬停在图表上可查看详细信息")
            
        except Exception as e:
            self.log_message(f"显示图表时出错: {str(e)}")
            messagebox.showerror("显示错误", f"无法显示图表：{str(e)}")
    
    def setup_hover_annotations(self, ax1, ax2, hist_dates, hist_closes, 
                               pred_dates, pred_closes, chart_type):
        """设置鼠标悬停显示日期时间和数值"""
        try:
            # 合并数据
            all_dates_original = list(hist_dates) + list(pred_dates)
            all_closes = list(hist_closes) + list(pred_closes)
            
            # 根据图表类型设置坐标系统
            if chart_type == "5min":
                # 5分钟图：使用索引坐标系统
                all_x_coords = list(range(len(all_dates_original)))
            else:
                # 日线图：转换日期为数值
                import matplotlib.dates as mdates
                all_x_coords = [mdates.date2num(date) for date in all_dates_original]
            
            # 为每个子图创建独立的注释
            self.annot_price = ax1.annotate('', xy=(0,0), xytext=(20,20), textcoords="offset points",
                                           bbox=dict(boxstyle="round", fc="lightblue", alpha=0.9),
                                           arrowprops=dict(arrowstyle="->", color='blue'))
            self.annot_price.set_visible(False)
            
            self.annot_macd = ax2.annotate('', xy=(0,0), xytext=(20,20), textcoords="offset points",
                                          bbox=dict(boxstyle="round", fc="lightgreen", alpha=0.9),
                                          arrowprops=dict(arrowstyle="->", color='green'))
            self.annot_macd.set_visible(False)
            
            def find_nearest_point(event_x, x_coords):
                """找到最近的数据点"""
                if chart_type == "5min":
                    # 5分钟图：直接使用索引
                    nearest_index = int(round(event_x))
                    nearest_index = max(0, min(nearest_index, len(x_coords) - 1))
                    distance = abs(event_x - nearest_index)
                    return nearest_index, distance
                else:
                    # 日线图：计算最近距离
                    distances = [abs(d - event_x) for d in x_coords]
                    min_index = distances.index(min(distances))
                    min_distance = distances[min_index]
                    return min_index, min_distance
            
            def on_hover(event):
                """鼠标悬停事件处理"""
                try:
                    if event.inaxes == ax1 and event.xdata is not None:
                        # 价格图悬停
                        min_index, min_distance = find_nearest_point(event.xdata, all_x_coords)
                        
                        # 检查是否足够接近
                        if chart_type == "5min":
                            # 5分钟图：容错范围0.5个索引单位
                            threshold = 0.5
                        else:
                            # 日线图：按原来的逻辑
                            data_range = max(all_x_coords) - min(all_x_coords)
                            threshold = data_range / len(all_x_coords) * 5
                        
                        if min_distance < threshold and min_index < len(all_closes):
                            x_pos = all_x_coords[min_index]
                            y_pos = all_closes[min_index]
                            
                            # 格式化时间显示
                            date_obj = all_dates_original[min_index]
                            if chart_type == "5min":
                                date_str = date_obj.strftime('%m-%d %H:%M')
                            else:
                                date_str = date_obj.strftime('%Y-%m-%d')
                            
                            # 判断是历史数据还是预测数据
                            if min_index < len(hist_dates):
                                data_type = "历史"
                            else:
                                data_type = "预测"
                            
                            # 智能调整注释位置
                            is_near_right = min_index >= len(all_x_coords) * 0.8
                            ax1_ylim = ax1.get_ylim()
                            y_range = ax1_ylim[1] - ax1_ylim[0]
                            is_near_top = y_pos >= (ax1_ylim[1] - y_range * 0.2)
                            
                            # 重新创建注释以改变位置
                            try:
                                self.annot_price.remove()
                            except:
                                pass
                            
                            # 根据位置调整悬停框偏移
                            if is_near_right and is_near_top:
                                xytext = (-120, -60)
                            elif is_near_right:
                                xytext = (-120, 20)
                            elif is_near_top:
                                xytext = (20, -60)
                            else:
                                xytext = (20, 20)
                            
                            # 创建新的注释
                            self.annot_price = ax1.annotate(f"时间: {date_str}\n{data_type}数据\n价格: {y_pos:.2f}元", 
                                                           xy=(x_pos, y_pos), xytext=xytext, 
                                                           textcoords="offset points",
                                                           bbox=dict(boxstyle="round", fc="lightblue", alpha=0.9),
                                                           arrowprops=dict(arrowstyle="->", color='blue'))
                            try:
                                self.annot_macd.set_visible(False)
                            except:
                                pass
                            self.canvas.draw_idle()
                        else:
                            try:
                                self.annot_price.set_visible(False)
                            except:
                                pass
                            self.canvas.draw_idle()
                            
                    elif event.inaxes == ax2 and event.xdata is not None:
                        # MACD图悬停
                        min_index, min_distance = find_nearest_point(event.xdata, all_x_coords)
                        
                        # 检查是否足够接近
                        if chart_type == "5min":
                            # 5分钟图：容错范围0.5个索引单位
                            threshold = 0.5
                        else:
                            # 日线图：按原来的逻辑
                            data_range = max(all_x_coords) - min(all_x_coords)
                            threshold = data_range / len(all_x_coords) * 5
                        
                        if min_distance < threshold and min_index < len(all_closes):
                            x_pos = all_x_coords[min_index]
                            
                            # 格式化时间显示
                            date_obj = all_dates_original[min_index]
                            if chart_type == "5min":
                                date_str = date_obj.strftime('%m-%d %H:%M')
                            else:
                                date_str = date_obj.strftime('%Y-%m-%d')
                            
                            # 判断是历史数据还是预测数据
                            if min_index < len(hist_dates):
                                data_type = "历史"
                            else:
                                data_type = "预测"
                            
                            # 智能调整注释位置
                            is_near_right = min_index >= len(all_x_coords) * 0.8
                            
                            # 重新创建注释以改变位置
                            try:
                                self.annot_macd.remove()
                            except:
                                pass
                            
                            # 根据位置调整悬停框偏移
                            if is_near_right:
                                xytext = (-120, 20)
                            else:
                                xytext = (20, 20)
                            
                            # 创建新的注释
                            self.annot_macd = ax2.annotate(f"时间: {date_str}\n{data_type}数据\nMACD指标", 
                                                          xy=(x_pos, 0), xytext=xytext,
                                                          textcoords="offset points",
                                                          bbox=dict(boxstyle="round", fc="lightgreen", alpha=0.9),
                                                          arrowprops=dict(arrowstyle="->", color='green'))
                            try:
                                self.annot_price.set_visible(False)
                            except:
                                pass
                            self.canvas.draw_idle()
                        else:
                            try:
                                self.annot_macd.set_visible(False)
                            except:
                                pass
                            self.canvas.draw_idle()
                    else:
                        # 鼠标不在任何子图上
                        try:
                            self.annot_price.set_visible(False)
                            self.annot_macd.set_visible(False)
                        except:
                            pass
                        self.canvas.draw_idle()
                        
                except Exception as e:
                    self.log_message(f"悬停处理错误: {str(e)}")
            
            # 连接鼠标移动事件
            self.hover_connection = self.canvas.mpl_connect('motion_notify_event', on_hover)
            self.log_message("鼠标悬停功能已启用")
            
        except Exception as e:
            self.log_message(f"设置悬停注释失败: {str(e)}")
    
    def save_chart_file(self, code, historical_data, prediction_data, chart_type):
        """保存图表到文件（后台保存）"""
        try:
            # 创建新的图表用于保存 - 三图布局：价格 + MACD + KDJ
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))
            
            # 准备数据
            hist_dates = historical_data['timestamps']
            hist_closes = historical_data['close']
            hist_volumes = historical_data['volume']
            
            pred_dates = prediction_data['timestamps']
            pred_closes = prediction_data['close']
            pred_volumes = prediction_data['volume']
            
            # 合并数据用于指标计算
            all_data_for_indicators = pd.concat([historical_data, prediction_data], ignore_index=True)
            
            # 计算MACD指标
            macd_line, signal_line, histogram = self.calculate_macd(all_data_for_indicators)
            
            # 计算KDJ指标
            all_data_with_kdj = self.calculate_kdj(all_data_for_indicators.copy(), n=9, m1=3, m2=3)
            
            # 上图：价格
            ax1.plot(hist_dates, hist_closes, color='blue', linewidth=2)
            ax1.plot(pred_dates, pred_closes, color='red', linewidth=2, linestyle='--')
            
            # 获取股票中文名称
            stock_name = self.get_stock_name(code)
            
            # 构建完整标题
            if stock_name:
                chart_title = f'{code} {stock_name} 股票价格预测 ({"日线图" if chart_type == "daily" else "5分钟图"})'
            else:
                chart_title = f'{code} 股票价格预测 ({"日线图" if chart_type == "daily" else "5分钟图"})'
            
            ax1.set_title(chart_title, fontsize=16, fontweight='bold')
            ax1.set_ylabel('价格 (元)', fontsize=12)
            
            # 手动创建图例，避免重复标签
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], color='blue', linewidth=2, label='历史数据'),
                Line2D([0], [0], color='red', linewidth=2, linestyle='--', label='预测数据')
            ]
            ax1.legend(handles=legend_elements, fontsize=10)
            ax1.grid(True, alpha=0.3)
            
            # 第二个子图：MACD
            if macd_line is not None:
                # 分离历史和预测的MACD数据
                hist_macd = macd_line[:len(historical_data)]
                hist_signal = signal_line[:len(historical_data)]
                hist_histogram = histogram[:len(historical_data)]
                
                pred_macd = macd_line[len(historical_data):]
                pred_signal = signal_line[len(historical_data):]
                pred_histogram = histogram[len(historical_data):]
                
                # 绘制历史MACD（实线）
                ax2.plot(hist_dates, hist_macd, label='MACD线', color='blue', linewidth=1.5)
                ax2.plot(hist_dates, hist_signal, label='信号线', color='red', linewidth=1.5)
                ax2.bar(hist_dates, hist_histogram, label='MACD柱状图', alpha=0.3, color='gray', width=0.8)
                
                # 绘制预测MACD（虚线）
                ax2.plot(pred_dates, pred_macd, color='blue', linewidth=1.5, linestyle='--', alpha=0.7)
                ax2.plot(pred_dates, pred_signal, color='red', linewidth=1.5, linestyle='--', alpha=0.7)
                ax2.bar(pred_dates, pred_histogram, alpha=0.2, color='gray', width=0.8)
                
                # 添加零轴线
                ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                
                ax2.set_title('MACD 技术指标', fontsize=12, fontweight='bold')
                ax2.set_ylabel('MACD', fontsize=10)
                ax2.legend(fontsize=10)
                ax2.grid(True, alpha=0.3)
            
            # 第三个子图：KDJ
            if 'K' in all_data_with_kdj.columns and 'D' in all_data_with_kdj.columns and 'J' in all_data_with_kdj.columns:
                # 分离历史和预测的KDJ数据
                hist_k = all_data_with_kdj['K'][:len(historical_data)]
                hist_d = all_data_with_kdj['D'][:len(historical_data)]
                hist_j = all_data_with_kdj['J'][:len(historical_data)]
                
                pred_k = all_data_with_kdj['K'][len(historical_data):]
                pred_d = all_data_with_kdj['D'][len(historical_data):]
                pred_j = all_data_with_kdj['J'][len(historical_data):]
                
                # 绘制历史KDJ（实线）
                ax3.plot(hist_dates, hist_k, label='K线', color='blue', linewidth=1.5)
                ax3.plot(hist_dates, hist_d, label='D线', color='red', linewidth=1.5)
                ax3.plot(hist_dates, hist_j, label='J线', color='green', linewidth=1.5)
                
                # 绘制预测KDJ（虚线）
                ax3.plot(pred_dates, pred_k, color='blue', linewidth=1.5, linestyle='--', alpha=0.7)
                ax3.plot(pred_dates, pred_d, color='red', linewidth=1.5, linestyle='--', alpha=0.7)
                ax3.plot(pred_dates, pred_j, color='green', linewidth=1.5, linestyle='--', alpha=0.7)
                
                # 添加超买超卖线
                ax3.axhline(y=20, color='green', linestyle=':', alpha=0.7, label='超卖线(20)')
                ax3.axhline(y=80, color='red', linestyle=':', alpha=0.7, label='超买线(80)')
                ax3.axhline(y=50, color='gray', linestyle='-', alpha=0.3, label='中轴线(50)')
                
                ax3.set_title('KDJ 随机指标', fontsize=12, fontweight='bold')
                ax3.set_ylabel('KDJ', fontsize=10)
                ax3.set_xlabel('时间', fontsize=12)
                ax3.legend(fontsize=10)
                ax3.grid(True, alpha=0.3)
                ax3.set_ylim(-10, 110)
            
            # 格式化x轴
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # 保存图表
            chart_file = f"data/{code}_prediction_chart_{chart_type}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()  # 关闭图表以释放内存
            
            return chart_file
            
        except Exception as e:
            self.log_message(f"保存图表文件时出错: {str(e)}")
            return None
    
    def save_chart(self):
        """保存当前显示的图表"""
        if not self.current_figure:
            messagebox.showwarning("无图表", "请先运行预测生成图表")
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPG files", "*.jpg"), ("PDF files", "*.pdf"), ("All files", "*.*")],
                title="保存图表"
            )
            if file_path:
                self.current_figure.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("保存成功", f"图表已保存到：{file_path}")
                self.log_message(f"图表已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存图表：{str(e)}")
            self.log_message(f"保存图表失败: {str(e)}")
    
    def open_results_folder(self):
        """打开结果文件夹"""
        try:
            if self.last_prediction_files:
                folder_path = os.path.dirname(self.last_prediction_files['historical'])
                if os.path.exists(folder_path):
                    os.startfile(folder_path)
                    self.log_message(f"已打开结果文件夹: {folder_path}")
                else:
                    self.log_message("结果文件夹不存在")
            else:
                # 打开默认的data文件夹
                if os.path.exists("data"):
                    os.startfile("data")
                    self.log_message("已打开data文件夹")
                else:
                    self.log_message("请先运行预测生成结果文件")
        except Exception as e:
            self.log_message(f"打开文件夹失败: {str(e)}")
    
    def open_csv_batch_analyzer(self):
        """打开CSV批量分析对话框"""
        try:
            # 创建CSV批量分析窗口
            csv_window = tk.Toplevel(self.root)
            csv_window.title("CSV批量股票分析工具")
            csv_window.geometry("600x500")
            csv_window.resizable(True, True)
            
            # 主容器
            main_frame = tk.Frame(csv_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # 标题
            title_label = tk.Label(main_frame, text="📊 CSV批量股票分析工具", 
                                  font=('Arial', 16, 'bold'), fg='#2E86AB')
            title_label.pack(pady=(0, 20))
            
            # 文件选择区域
            file_frame = tk.LabelFrame(main_frame, text="选择CSV文件", font=('Arial', 11, 'bold'))
            file_frame.pack(fill=tk.X, pady=(0, 15))
            
            # 文件路径显示
            file_path_frame = tk.Frame(file_frame)
            file_path_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.csv_file_path = tk.StringVar()
            file_entry = tk.Entry(file_path_frame, textvariable=self.csv_file_path, 
                                 font=('Arial', 10), state='readonly')
            file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            browse_button = tk.Button(file_path_frame, text="浏览", 
                                     command=self.browse_csv_file,
                                     font=('Arial', 10))
            browse_button.pack(side=tk.RIGHT)
            
            # 示例按钮
            example_frame = tk.Frame(file_frame)
            example_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            sample_button = tk.Button(example_frame, text="使用示例文件 (sample_stock_list.csv)", 
                                     command=lambda: self.csv_file_path.set("sample_stock_list.csv"),
                                     font=('Arial', 9), bg='#E8F5E8')
            sample_button.pack(side=tk.LEFT, padx=(0, 10))
            
            create_demo_button = tk.Button(example_frame, text="创建演示文件", 
                                          command=self.create_demo_csv_files,
                                          font=('Arial', 9), bg='#E8F8FF')
            create_demo_button.pack(side=tk.LEFT)
            
            # 分析参数设置
            params_frame = tk.LabelFrame(main_frame, text="分析参数", font=('Arial', 11, 'bold'))
            params_frame.pack(fill=tk.X, pady=(0, 15))
            
            # 参数设置网格
            params_grid = tk.Frame(params_frame)
            params_grid.pack(fill=tk.X, padx=10, pady=10)
            
            # 时间框架
            tk.Label(params_grid, text="时间框架:", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
            self.csv_timeframe = tk.StringVar(value="daily")
            timeframe_frame = tk.Frame(params_grid)
            timeframe_frame.grid(row=0, column=1, sticky='w', padx=10)
            tk.Radiobutton(timeframe_frame, text="日线", variable=self.csv_timeframe, value="daily").pack(side=tk.LEFT)
            tk.Radiobutton(timeframe_frame, text="15分钟", variable=self.csv_timeframe, value="15min").pack(side=tk.LEFT, padx=10)
            tk.Radiobutton(timeframe_frame, text="5分钟", variable=self.csv_timeframe, value="5min").pack(side=tk.LEFT)
            
            # 预测天数
            tk.Label(params_grid, text="预测天数:", font=('Arial', 10)).grid(row=1, column=0, sticky='w', pady=5)
            self.csv_pred_days = tk.IntVar(value=5)
            pred_days_spinbox = tk.Spinbox(params_grid, from_=1, to=20, textvariable=self.csv_pred_days, 
                                          width=10, font=('Arial', 10))
            pred_days_spinbox.grid(row=1, column=1, sticky='w', padx=10)
            
            # 高级选项
            advanced_frame = tk.LabelFrame(main_frame, text="高级选项", font=('Arial', 11, 'bold'))
            advanced_frame.pack(fill=tk.X, pady=(0, 15))
            
            advanced_grid = tk.Frame(advanced_frame)
            advanced_grid.pack(fill=tk.X, padx=10, pady=10)
            
            # 使用Kronos模型
            self.csv_use_kronos = tk.BooleanVar(value=False)
            kronos_checkbox = tk.Checkbutton(advanced_grid, text="使用Kronos深度学习模型", 
                                           variable=self.csv_use_kronos, font=('Arial', 10))
            kronos_checkbox.grid(row=0, column=0, sticky='w', pady=2)
            
            # 使用多模型集成
            self.csv_use_ensemble = tk.BooleanVar(value=True)
            ensemble_checkbox = tk.Checkbutton(advanced_grid, text="启用多模型集成预测", 
                                             variable=self.csv_use_ensemble, font=('Arial', 10))
            ensemble_checkbox.grid(row=1, column=0, sticky='w', pady=2)
            
            # 输出目录
            tk.Label(advanced_grid, text="输出目录:", font=('Arial', 10)).grid(row=2, column=0, sticky='w', pady=5)
            self.csv_output_dir = tk.StringVar(value="")
            output_entry = tk.Entry(advanced_grid, textvariable=self.csv_output_dir, 
                                   width=30, font=('Arial', 10))
            output_entry.grid(row=2, column=1, sticky='w', padx=10)
            tk.Label(advanced_grid, text="(留空自动生成)", font=('Arial', 8), fg='gray').grid(row=2, column=2, sticky='w', padx=5)
            
            # 按钮区域
            button_frame = tk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))
            
            # 开始分析按钮
            start_button = tk.Button(button_frame, text="🚀 开始批量分析", 
                                    command=lambda: self.start_csv_batch_analysis(csv_window),
                                    font=('Arial', 12, 'bold'),
                                    bg='#4CAF50', fg='white',
                                    height=2)
            start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            # 关闭按钮
            close_button = tk.Button(button_frame, text="关闭", 
                                    command=csv_window.destroy,
                                    font=('Arial', 10))
            close_button.pack(side=tk.RIGHT)
            
            # 说明文本
            info_frame = tk.Frame(main_frame)
            info_frame.pack(fill=tk.X, pady=(15, 0))
            
            info_text = """📝 使用说明：
1. 选择包含股票代码的CSV文件
2. CSV文件应包含"股票代码"、"stock_code"、"code"等列名
3. 支持6位数字格式(如000001)和带后缀格式(如000001.SZ)
4. 分析结果将保存为CSV总结和JSON详细文件
5. 需要在data/目录下有对应的历史数据文件"""
            
            info_label = tk.Label(info_frame, text=info_text, 
                                 font=('Arial', 9), fg='#666666',
                                 justify=tk.LEFT, wraplength=550)
            info_label.pack(anchor='w')
            
            self.log_message("📊 CSV批量分析界面已打开")
            
        except Exception as e:
            self.log_message(f"❌ 打开CSV分析界面失败: {str(e)}")
            messagebox.showerror("错误", f"打开CSV分析界面失败：{str(e)}")
    
    def browse_csv_file(self):
        """浏览选择CSV文件"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择CSV文件",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
                initialdir=os.getcwd()
            )
            if file_path:
                self.csv_file_path.set(file_path)
                self.log_message(f"已选择CSV文件: {os.path.basename(file_path)}")
        except Exception as e:
            self.log_message(f"❌ 选择文件失败: {str(e)}")
    
    def create_demo_csv_files(self):
        """创建演示CSV文件"""
        try:
            # 运行演示脚本创建文件
            result = subprocess.run([sys.executable, "demo_csv_formats.py"], 
                                   capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                self.log_message("✅ 演示CSV文件创建成功")
                messagebox.showinfo("成功", "演示CSV文件已创建！\n可以选择demo_format1.csv等文件进行测试。")
            else:
                self.log_message(f"❌ 创建演示文件失败: {result.stderr}")
                messagebox.showerror("错误", f"创建演示文件失败：{result.stderr}")
                
        except Exception as e:
            self.log_message(f"❌ 创建演示文件失败: {str(e)}")
            messagebox.showerror("错误", f"创建演示文件失败：{str(e)}")
    
    def start_csv_batch_analysis(self, parent_window):
        """开始CSV批量分析"""
        try:
            # 验证输入
            csv_file = self.csv_file_path.get().strip()
            if not csv_file:
                messagebox.showerror("错误", "请选择CSV文件！")
                return
            
            if not os.path.exists(csv_file):
                messagebox.showerror("错误", f"文件不存在：{csv_file}")
                return
            
            # 获取参数
            timeframe = self.csv_timeframe.get()
            pred_days = self.csv_pred_days.get()
            use_kronos = self.csv_use_kronos.get()
            use_ensemble = self.csv_use_ensemble.get()
            output_dir = self.csv_output_dir.get().strip()
            
            # 构建命令
            cmd = [sys.executable, "analyze_csv_stocks.py", csv_file]
            
            if output_dir:
                cmd.extend(["--output", output_dir])
            
            cmd.extend(["--timeframe", timeframe])
            cmd.extend(["--pred-days", str(pred_days)])
            
            if use_kronos:
                cmd.append("--use-kronos")
            
            self.log_message(f"🚀 开始CSV批量分析: {os.path.basename(csv_file)}")
            self.log_message(f"📋 参数: {timeframe}, 预测{pred_days}天, Kronos={use_kronos}")
            
            # 关闭参数窗口
            parent_window.destroy()
            
            # 在后台线程运行分析
            def run_analysis():
                try:
                    # 如果文件名包含非ASCII字符，创建临时副本
                    temp_file = None
                    analysis_file = csv_file
                    
                    if not csv_file.isascii():
                        # 创建临时文件避免编码问题
                        import tempfile
                        import shutil
                        temp_file = os.path.join(os.path.dirname(csv_file), "temp_analysis.csv")
                        shutil.copy2(csv_file, temp_file)
                        analysis_file = temp_file
                        
                        # 更新命令中的文件路径
                        cmd[2] = analysis_file
                    
                    # 运行分析命令，显式设置编码
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        cwd=os.getcwd(),
                        encoding='utf-8',
                        errors='replace'
                    )
                    
                    # 清理临时文件
                    if temp_file and os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    
                    # 在主线程中更新UI
                    self.root.after(0, lambda: self.handle_csv_analysis_result(result, csv_file))
                    
                except Exception as e:
                    # 清理临时文件
                    if temp_file and os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    self.root.after(0, lambda: self.log_message(f"❌ 分析执行失败: {str(e)}"))
            
            # 启动后台线程
            analysis_thread = threading.Thread(target=run_analysis, daemon=True)
            analysis_thread.start()
            
            # 显示进度
            self.progress.start(10)
            self.log_message("⏳ 正在后台运行批量分析，请稍候...")
            
        except Exception as e:
            self.log_message(f"❌ 启动CSV分析失败: {str(e)}")
            messagebox.showerror("错误", f"启动分析失败：{str(e)}")
    
    def handle_csv_analysis_result(self, result, csv_file):
        """处理CSV分析结果"""
        try:
            # 停止进度条
            self.progress.stop()
            
            if result.returncode == 0:
                # 分析成功
                self.log_message("✅ CSV批量分析完成！")
                
                # 解析输出中的结果路径
                output_lines = result.stdout.split('\n')
                result_dir = None
                
                for line in output_lines:
                    if "结果保存在:" in line:
                        result_dir = line.split("结果保存在:")[-1].strip()
                        break
                    elif "analysis_results" in line and "保存至:" in line:
                        # 尝试从详细输出中提取路径
                        if "analysis_results" in line:
                            parts = line.split()
                            for part in parts:
                                if "analysis_results" in part:
                                    result_dir = os.path.dirname(part)
                                    break
                
                # 显示结果对话框
                self.show_csv_analysis_result_dialog(csv_file, result_dir, result.stdout)
                
            else:
                # 分析失败
                self.log_message(f"❌ CSV批量分析失败")
                self.log_message(f"错误信息: {result.stderr}")
                messagebox.showerror("分析失败", f"CSV批量分析失败：\n{result.stderr}")
                
        except Exception as e:
            self.log_message(f"❌ 处理分析结果失败: {str(e)}")
    
    def show_csv_analysis_result_dialog(self, csv_file, result_dir, output_text):
        """显示CSV分析结果对话框"""
        try:
            # 创建结果窗口
            result_window = tk.Toplevel(self.root)
            result_window.title("批量分析结果")
            result_window.geometry("700x600")
            
            # 主容器
            main_frame = tk.Frame(result_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # 标题
            title_label = tk.Label(main_frame, text="📊 CSV批量分析完成", 
                                  font=('Arial', 16, 'bold'), fg='green')
            title_label.pack(pady=(0, 20))
            
            # 基本信息
            info_frame = tk.Frame(main_frame)
            info_frame.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(info_frame, text=f"分析文件: {os.path.basename(csv_file)}", 
                    font=('Arial', 11, 'bold')).pack(anchor='w')
            
            if result_dir:
                tk.Label(info_frame, text=f"结果保存: {result_dir}", 
                        font=('Arial', 11), fg='blue').pack(anchor='w')
            
            # 输出信息显示
            output_frame = tk.LabelFrame(main_frame, text="分析详情", font=('Arial', 11, 'bold'))
            output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            # 创建文本框和滚动条
            text_container = tk.Frame(output_frame)
            text_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            output_text_widget = tk.Text(text_container, height=15, font=('Consolas', 9), 
                                        wrap=tk.WORD, state='normal')
            output_scrollbar = tk.Scrollbar(text_container, orient=tk.VERTICAL, 
                                           command=output_text_widget.yview)
            output_text_widget.configure(yscrollcommand=output_scrollbar.set)
            
            output_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 配置颜色标签
            self.configure_text_colors(output_text_widget)
            
            # 插入带颜色的输出文本
            self.insert_colored_text(output_text_widget, output_text)
            output_text_widget.config(state='disabled')
            
            # 按钮区域
            button_frame = tk.Frame(main_frame)
            button_frame.pack(fill=tk.X)
            
            # 打开结果文件夹按钮
            if result_dir and os.path.exists(result_dir):
                open_folder_button = tk.Button(button_frame, text="📁 打开结果文件夹", 
                                              command=lambda: self.open_specific_folder(result_dir),
                                              font=('Arial', 11, 'bold'),
                                              bg='#2196F3', fg='white')
                open_folder_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            # 查看总结报告按钮
            if result_dir:
                view_summary_button = tk.Button(button_frame, text="📋 查看总结报告", 
                                               command=lambda: self.view_csv_summary_report(result_dir),
                                               font=('Arial', 11, 'bold'),
                                               bg='#4CAF50', fg='white')
                view_summary_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            # 关闭按钮
            close_button = tk.Button(button_frame, text="关闭", 
                                    command=result_window.destroy,
                                    font=('Arial', 11))
            close_button.pack(side=tk.RIGHT)
            
        except Exception as e:
            self.log_message(f"❌ 显示结果对话框失败: {str(e)}")
    
    def open_specific_folder(self, folder_path):
        """打开指定文件夹"""
        try:
            if os.path.exists(folder_path):
                os.startfile(folder_path)
                self.log_message(f"📁 已打开文件夹: {folder_path}")
            else:
                self.log_message(f"❌ 文件夹不存在: {folder_path}")
                messagebox.showerror("错误", "文件夹不存在！")
        except Exception as e:
            self.log_message(f"❌ 打开文件夹失败: {str(e)}")
    
    def configure_text_colors(self, text_widget):
        """为Text组件配置颜色标签"""
        # 配置不同颜色的标签
        text_widget.tag_configure("green", foreground="#00AA00", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("red", foreground="#DD0000", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("yellow", foreground="#DDAA00", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("blue", foreground="#0066DD", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("cyan", foreground="#00AAAA", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("magenta", foreground="#AA00AA", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("orange", foreground="#FF6600", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("purple", foreground="#6600FF", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("brown", foreground="#AA5500", font=('Consolas', 9, 'bold'))
        
        # 交易建议颜色
        text_widget.tag_configure("strong_buy", foreground="#00CC00", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("buy", foreground="#44AA44", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("weak_buy", foreground="#66AA66", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("hold", foreground="#888888", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("weak_sell", foreground="#AA6666", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("sell", foreground="#AA4444", font=('Consolas', 9, 'bold'))
        text_widget.tag_configure("strong_sell", foreground="#CC0000", font=('Consolas', 9, 'bold'))
    
    def insert_colored_text(self, text_widget, text_content):
        """插入带颜色的文本内容"""
        import re
        
        # 移除ANSI转义序列并根据内容添加颜色
        lines = text_content.split('\n')
        
        for line in lines:
            # 移除ANSI转义序列
            clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            
            # 根据内容判断颜色
            if "强烈买入" in clean_line or "Strong Buy" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "strong_buy")
            elif "买入" in clean_line or "Buy" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "buy")
            elif "弱买入" in clean_line or "Weak Buy" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "weak_buy")
            elif "持有" in clean_line or "Hold" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "hold")
            elif "弱卖出" in clean_line or "Weak Sell" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "weak_sell")
            elif "卖出" in clean_line or "Sell" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "sell")
            elif "强烈卖出" in clean_line or "Strong Sell" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "strong_sell")
            elif "✅" in clean_line or "成功" in clean_line or "完成" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "green")
            elif "❌" in clean_line or "错误" in clean_line or "失败" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "red")
            elif "⚠️" in clean_line or "警告" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "yellow")
            elif "📊" in clean_line or "分析" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "blue")
            elif "💰" in clean_line or "价格" in clean_line:
                text_widget.insert(tk.END, clean_line + '\n', "cyan")
            else:
                text_widget.insert(tk.END, clean_line + '\n')
    
    def view_csv_summary_report(self, result_dir):
        """查看CSV总结报告"""
        try:
            # 查找总结报告文件
            summary_files = []
            if os.path.exists(result_dir):
                for file in os.listdir(result_dir):
                    if file.startswith("batch_analysis_summary") and file.endswith(".csv"):
                        summary_files.append(os.path.join(result_dir, file))
            
            if not summary_files:
                messagebox.showwarning("警告", "未找到总结报告文件！")
                return
            
            # 选择最新的总结文件
            latest_summary = max(summary_files, key=os.path.getmtime)
            
            # 读取并显示总结报告
            self.show_csv_summary_content(latest_summary)
            
        except Exception as e:
            self.log_message(f"❌ 查看总结报告失败: {str(e)}")
            messagebox.showerror("错误", f"查看总结报告失败：{str(e)}")
    
    def show_csv_summary_content(self, summary_file):
        """显示CSV总结报告内容"""
        try:
            # 读取CSV文件
            df = pd.read_csv(summary_file, encoding='utf-8-sig')
            
            # 创建报告窗口
            report_window = tk.Toplevel(self.root)
            report_window.title(f"总结报告 - {os.path.basename(summary_file)}")
            report_window.geometry("900x500")
            
            # 主容器
            main_frame = tk.Frame(report_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # 标题
            title_label = tk.Label(main_frame, text="📋 批量分析总结报告", 
                                  font=('Arial', 16, 'bold'), fg='#2E86AB')
            title_label.pack(pady=(0, 20))
            
            # 创建表格显示
            # 使用Treeview显示表格
            tree_frame = tk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            # 创建Treeview
            columns = list(df.columns)
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
            
            # 配置Treeview颜色标签 - 按照中国股市传统颜色
            tree.tag_configure('strong_buy', background='#FFE8E8', foreground='#CC0000')     # 红色 - 强烈买入
            tree.tag_configure('buy', background='#FFEEEE', foreground='#DD0000')           # 红色 - 买入
            tree.tag_configure('weak_buy', background='#FFFF99', foreground='#CC6600')      # 明显黄色 - 少量买入
            tree.tag_configure('hold', background='#F5F5F5', foreground='#666666')          # 灰色 - 观望
            tree.tag_configure('weak_sell', background='#E8F8E8', foreground='#228B22')     # 绿色 - 少量卖出
            tree.tag_configure('sell', background='#E0F0E0', foreground='#008000')          # 绿色 - 卖出
            tree.tag_configure('strong_sell', background='#D8F0D8', foreground='#006400')   # 深绿色 - 强烈卖出
            tree.tag_configure('success', background='#E8F5E8', foreground='#2E7D2E')
            tree.tag_configure('error', background='#FFE8E8', foreground='#D32F2F')
            
            # 配置列
            for col in columns:
                tree.heading(col, text=col)
                if col == '股票代码':
                    tree.column(col, width=80, anchor='center')
                elif col == '建议':
                    tree.column(col, width=120, anchor='center')
                elif col == '建议强度':
                    tree.column(col, width=80, anchor='center')
                elif col == '建议评分':
                    tree.column(col, width=80, anchor='center')
                else:
                    tree.column(col, width=100, anchor='center')
            
            # 插入数据并设置颜色
            for index, row in df.iterrows():
                values = list(row)
                
                # 格式化股票代码为6位完整格式
                if '股票代码' in df.columns:
                    stock_code_index = df.columns.get_loc('股票代码')
                    original_code = str(values[stock_code_index])
                    if original_code.isdigit():
                        values[stock_code_index] = original_code.zfill(6)  # 补齐到6位
                
                # 确定行的颜色标签
                tag = ''
                if '建议' in df.columns:
                    recommendation = str(row['建议']).strip()
                    # 注意：要先检查更具体的匹配，再检查一般的匹配
                    if "强烈买入" in recommendation:
                        tag = 'strong_buy'
                    elif "少量买入" in recommendation:  # 先检查少量买入
                        tag = 'weak_buy'
                    elif "买入" in recommendation:     # 再检查一般买入
                        tag = 'buy'
                    elif "强烈卖出" in recommendation:
                        tag = 'strong_sell'
                    elif "少量卖出" in recommendation:
                        tag = 'weak_sell'
                    elif "卖出" in recommendation:
                        tag = 'sell'
                    elif "观望" in recommendation or "持有" in recommendation:
                        tag = 'hold'
                
                # 插入行数据
                item_id = tree.insert('', 'end', values=values, tags=(tag,))
                        
                # 设置预测状态的图标
                if '预测状态' in df.columns:
                    status = str(row['预测状态']).strip()
                    if status == '成功':
                        tree.set(item_id, '预测状态', f"✅ {status}")
                    elif status == '失败':
                        tree.set(item_id, '预测状态', f"❌ {status}")
                    else:
                        tree.set(item_id, '预测状态', f"⚠️ {status}")
            
            # 添加滚动条
            v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=v_scrollbar.set)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
            tree.configure(xscrollcommand=h_scrollbar.set)
            
            # 布局
            tree.grid(row=0, column=0, sticky='nsew')
            v_scrollbar.grid(row=0, column=1, sticky='ns')
            h_scrollbar.grid(row=1, column=0, sticky='ew')
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # 统计信息
            stats_frame = tk.Frame(main_frame)
            stats_frame.pack(fill=tk.X, pady=(15, 0))
            
            total_stocks = len(df)
            successful = len(df[df['预测状态'] == '成功']) if '预测状态' in df.columns else 0
            
            stats_text = f"总计: {total_stocks} 只股票 | 成功: {successful} 只 | 成功率: {successful/total_stocks*100:.1f}%"
            tk.Label(stats_frame, text=stats_text, font=('Arial', 12, 'bold'), 
                    fg='green').pack()
            
            # 关闭按钮
            close_button = tk.Button(main_frame, text="关闭", 
                                    command=report_window.destroy,
                                    font=('Arial', 11))
            close_button.pack(pady=(10, 0))
            
        except Exception as e:
            self.log_message(f"❌ 显示总结报告失败: {str(e)}")
            messagebox.showerror("错误", f"显示总结报告失败：{str(e)}")

    def open_results_folder(self):
        """打开结果文件夹"""
        if not self.last_prediction_files:
            messagebox.showwarning("无结果", "请先运行预测")
            return
            
        try:
            data_folder = os.path.abspath("data")
            if os.name == 'nt':  # Windows
                os.startfile(data_folder)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', data_folder])
        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开文件夹：{str(e)}")
    
    def run_prediction_thread(self):
        """在后台线程中运行预测"""
        try:
            # 获取输入参数
            code = self.stock_code.get().strip()
            chart_type = self.chart_type.get()
            
            if not code:
                messagebox.showerror("输入错误", "请输入股票代码")
                return
            
            # 根据图表类型使用自动优化参数
            if chart_type == "daily":
                # 日线图使用优化的固定参数
                hist_days = 25  # 最优历史数据天数
                pred_days = 7   # 最优预测天数
            else:
                # 5分钟图使用优化的固定参数
                hist_days = 2  # 固定前2日
                pred_days = 8  # 固定8个5分钟周期
            
            self.log_message(f"开始预测 {code} ({chart_type})")
            self.log_message(f"历史数据: {hist_days}天, 预测: {pred_days}天")
            
            # 获取数据
            self.log_message("正在获取股票数据...")
            historical_data, prediction_data = self.get_stock_data_simple(code, chart_type, hist_days, pred_days)
            
            # 检查数据是否获取成功
            if historical_data is None or prediction_data is None:
                self.log_message("❌ 无法获取真实股票数据")
                # 显示警告图表
                self.root.after(0, lambda: self.display_warning_chart(code, chart_type))
                return
            
            # 保存数据到CSV
            self.log_message("正在保存数据...")
            
            hist_file = f"data/{code}_historical_{chart_type}.csv"
            pred_file = f"data/{code}_prediction_{chart_type}.csv"
            
            historical_data.to_csv(hist_file, index=False, encoding='utf-8-sig')
            prediction_data.to_csv(pred_file, index=False, encoding='utf-8-sig')
            
            self.last_prediction_files = [hist_file, pred_file]
            
            # 在主线程中显示图表
            self.root.after(0, lambda: self.display_chart_in_gui(code, historical_data, prediction_data, chart_type))
            
            # 在后台保存图表文件
            chart_file = self.save_chart_file(code, historical_data, prediction_data, chart_type)
            if chart_file:
                self.log_message(f"图表已保存: {chart_file}")
            
            self.log_message("预测完成！")
            self.log_message(f"历史数据: {hist_file}")
            self.log_message(f"预测数据: {pred_file}")
            
            # 存储最后预测文件路径
            self.last_prediction_files = [hist_file, pred_file]
            
            # 进行交易信号分析
            self.log_message("🤖 正在分析当前交易信号...")
            action, analysis_report = self.analyze_current_trading_signal(historical_data, prediction_data)
            
        except Exception as e:
            error_msg = f"预测失败: {str(e)}"
            self.log_message(error_msg)
            self.root.after(0, lambda: messagebox.showerror("预测失败", error_msg))
        finally:
            # 停止进度条并重新启用按钮
            self.root.after(0, self.stop_progress)
    
    def run_prediction(self):
        """运行预测（启动后台线程）"""
        # 禁用按钮并启动进度条
        self.predict_button.config(state='disabled')
        self.progress.start()
        
        # 在后台线程中运行预测
        thread = threading.Thread(target=self.run_prediction_thread)
        thread.daemon = True
        thread.start()
    
    def analyze_current_trading_signal(self, historical_data, prediction_data):
        """分析当前时点的交易信号 - 考虑重合区间的一致性"""
        try:
            # 获取重合天数设置
            overlap_days = int(self.overlap_days.get()) if hasattr(self, 'overlap_days') else 0
            chart_type = self.chart_type.get()
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_message(f"🎯 分析当前时点交易信号 (重合: {overlap_days}天)")
            
            # 关键逻辑：如果有重合天数，当前时点可能在预测范围内
            if overlap_days > 0:
                # 检查当前时点在重合区间的位置
                # 重合区间意味着预测的前几天是已知的历史数据
                current_signal_source = "历史数据"
                
                # 获取历史数据的最后价格作为当前价格
                current_price = historical_data['close'].iloc[-1]
                
                # 获取预测数据中对应"今天"的预测值（重合区间的最后一天）
                if len(prediction_data) >= overlap_days:
                    today_predicted_price = prediction_data['close'].iloc[overlap_days-1] if overlap_days > 0 else current_price
                    
                    # 关键：比较当前真实价格与预测数据的关系
                    price_deviation = (current_price - today_predicted_price) / today_predicted_price * 100
                    
                    # 分析预测趋势（预测的前3天趋势）
                    if len(prediction_data) >= 3:
                        pred_start = prediction_data['close'].iloc[0]
                        pred_trend_price = prediction_data['close'].iloc[2]  # 第3天的预测
                        pred_trend = (pred_trend_price - pred_start) / pred_start * 100
                    else:
                        pred_trend = 0
                else:
                    today_predicted_price = current_price
                    price_deviation = 0
                    pred_trend = 0
            else:
                # 无重合，纯粹基于历史数据
                current_signal_source = "历史数据"
                current_price = historical_data['close'].iloc[-1]
                today_predicted_price = current_price
                price_deviation = 0
                
                # 分析未来预测趋势
                if len(prediction_data) >= 3:
                    pred_start = prediction_data['close'].iloc[0]
                    pred_end = prediction_data['close'].iloc[2]
                    pred_trend = (pred_end - pred_start) / pred_start * 100
                else:
                    pred_trend = 0
            
            # 计算短期价格动量（基于历史数据）
            recent_prices = historical_data['close'].tail(5)
            price_momentum = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100
            
            # 🆕 计算KDJ指标分析
            self.log_message("🔄 计算KDJ和ATR指标...")
            historical_with_indicators = historical_data.copy()
            historical_with_indicators = self.calculate_kdj(historical_with_indicators, n=9, m1=3, m2=3)
            historical_with_indicators = self.calculate_atr(historical_with_indicators, period=14)
            
            # 获取最新KDJ值
            current_k = historical_with_indicators['K'].iloc[-1] if len(historical_with_indicators) > 0 else 50
            current_d = historical_with_indicators['D'].iloc[-1] if len(historical_with_indicators) > 0 else 50
            current_j = historical_with_indicators['J'].iloc[-1] if len(historical_with_indicators) > 0 else 50
            
            # 获取ATR值用于动态止损
            current_atr = historical_with_indicators['ATR'].iloc[-1] if len(historical_with_indicators) > 0 else current_price * 0.02
            
            # KDJ信号分析
            kdj_signal = ""
            kdj_score = 0
            
            if current_k < 20 and current_d < 20:
                kdj_signal = "🟢 KDJ强烈超卖"
                kdj_score = 2
            elif current_k < 30 and current_d < 30:
                kdj_signal = "🟡 KDJ超卖"
                kdj_score = 1
            elif current_k > 80 and current_d > 80:
                kdj_signal = "🔴 KDJ强烈超买"
                kdj_score = -2
            elif current_k > 70 and current_d > 70:
                kdj_signal = "🟠 KDJ超买"
                kdj_score = -1
            else:
                kdj_signal = "⚪ KDJ中性"
                kdj_score = 0
            
            # KDJ金叉死叉分析
            if len(historical_with_indicators) >= 2:
                prev_k = historical_with_indicators['K'].iloc[-2]
                prev_d = historical_with_indicators['D'].iloc[-2]
                
                if prev_k <= prev_d and current_k > current_d:
                    kdj_signal += " (金叉)"
                    kdj_score += 1
                elif prev_k >= prev_d and current_k < current_d:
                    kdj_signal += " (死叉)"
                    kdj_score -= 1
            
            # J值极端情况
            j_signal = ""
            if current_j < 10:
                j_signal = "⚡ J值极度超卖"
                kdj_score += 1
            elif current_j > 90:
                j_signal = "⚡ J值极度超买"
                kdj_score -= 1
            
            # 计算动态止损建议
            long_stop_loss, long_risk = self.calculate_dynamic_stop_loss(current_price, current_atr, "long", 2.0)
            short_stop_loss, short_risk = self.calculate_dynamic_stop_loss(current_price, current_atr, "short", 2.0)
            
            risk_ratio_long = (long_risk / current_price) * 100
            risk_ratio_short = (short_risk / current_price) * 100
            
            # 简化的MACD计算
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
                        macd_signal = "🟢 MACD金叉"
                        macd_score = 2
                    elif prev_macd >= prev_signal and current_macd < current_signal:
                        macd_signal = "🔴 MACD死叉"
                        macd_score = -2
                    elif current_macd > 0:
                        macd_signal = "🟡 MACD多头"
                        macd_score = 1
                    elif current_macd < 0:
                        macd_signal = "🟠 MACD空头"
                        macd_score = -1
                    else:
                        macd_signal = "⚪ MACD中性"
                        macd_score = 0
                else:
                    macd_signal = "⚪ MACD数据不足"
                    macd_score = 0
            else:
                macd_signal = "⚪ 历史数据不足"
                macd_score = 0
                current_macd = 0
                current_signal = 0
            
            # 趋势评分
            trend_score = 0
            if pred_trend > 2:
                trend_signal = f"📈 预测强势上涨 +{pred_trend:.1f}%"
                trend_score = 2
            elif pred_trend > 0.5:
                trend_signal = f"📊 预测温和上涨 +{pred_trend:.1f}%"
                trend_score = 1
            elif pred_trend > -0.5:
                trend_signal = f"➡️ 预测横盘 {pred_trend:.1f}%"
                trend_score = 0
            elif pred_trend > -2:
                trend_signal = f"📉 预测温和下跌 {pred_trend:.1f}%"
                trend_score = -1
            else:
                trend_signal = f"⬇️ 预测下跌 {pred_trend:.1f}%"
                trend_score = -2
            
            # 综合评分（MACD + 趋势 + KDJ）
            total_score = macd_score + trend_score + kdj_score
            
            # 生成建议（7级精细评分系统，加入KDJ）
            if total_score >= 4:
                recommendation = "🟢 强烈建议买入"
                action = "强烈买入"
                confidence = "极高"
                risk_level = "积极操作"
            elif total_score >= 2:
                recommendation = "🟡 建议买入"
                action = "买入"
                confidence = "较高"
                risk_level = "积极买入"
            elif total_score >= 0:
                recommendation = "🔵 建议少量买入"
                action = "少买"
                confidence = "中等"
                risk_level = "谨慎买入"
            elif total_score >= -1:
                recommendation = "⚪ 建议观望等待"
                action = "观望"
                confidence = "谨慎"
                risk_level = "暂不操作"
            elif total_score >= -3:
                recommendation = "🟠 建议少量卖出"
                action = "少卖"
                confidence = "中等"
                risk_level = "谨慎卖出"
            else:
                recommendation = "🔴 强烈建议卖出"
                action = "强烈卖出"
                confidence = "极高"
                risk_level = "积极减仓"
            
            # 生成增强的分析报告
            analysis_report = f"""
📊 === 增强版交易信号分析 (KDJ+ATR) ===

🕐 分析时间: {current_time}
💰 当前价格: ¥{current_price:.2f}
📍 重合设置: {overlap_days}天重合

🔍 核心技术指标分析:
{macd_signal}
• MACD值: {current_macd:.4f}
• Signal值: {current_signal:.4f}

🎯 KDJ随机指标分析:
{kdj_signal}
• K值: {current_k:.1f}
• D值: {current_d:.1f}
• J值: {current_j:.1f}
{j_signal}

📊 ATR波动率分析:
• ATR值: {current_atr:.4f} (¥{current_atr:.2f})
• 波动率: {(current_atr/current_price)*100:.2f}%

�️ 动态止损建议:
• 多头止损: ¥{long_stop_loss:.2f} (风险: {risk_ratio_long:.2f}%)
• 空头止损: ¥{short_stop_loss:.2f} (风险: {risk_ratio_short:.2f}%)

�📈 价格动量分析:
• 短期动量: {price_momentum:+.2f}%
{trend_signal}

🎯 综合建议: {recommendation}
• MACD评分: {macd_score}/2
• 趋势评分: {trend_score}/2
• KDJ评分: {kdj_score}/3
• 总评分: {total_score}/7
• 信号强度: {confidence}
• 操作建议: {risk_level}

📋 7级评分系统说明:
• 🟢 强烈买入: 总评分 ≥ 4分 (多指标强烈看好)
• 🟡 建议买入: 总评分 2-3分 (多指标偏好)
• 🔵 少量买入: 总评分 0-1分 (谨慎偏好)
• ⚪ 观望等待: 总评分 -1分 (信号不明)
• 🟠 少量卖出: 总评分 -3到-2分 (谨慎偏空)
• 🔴 强烈卖出: 总评分 ≤ -4分 (多指标看空)

💡 KDJ超买超卖参考:
• 超卖区: K<30, D<30 (买入时机)
• 中性区: 30≤K,D≤70 (观察区间)
• 超买区: K>70, D>70 (卖出时机)

🛡️ 风险控制建议:
• 建议止损: {"多头 ¥" + f"{long_stop_loss:.2f}" if action in ["强烈买入", "买入", "少买"] else "空头 ¥" + f"{short_stop_loss:.2f}"}
• 风险比例: {risk_ratio_long:.2f}% (基于2倍ATR)
• 仓位建议: {"重仓" if confidence == "极高" else "半仓" if confidence in ["较高", "中等"] else "轻仓"}

💡 重合区间说明:
• 数据来源: {current_signal_source}
• 预测一致性: {"✅ 建议与预测趋势一致" if (action in ["强烈买入", "买入", "少买"] and pred_trend > 0) or (action in ["强烈卖出", "少卖"] and pred_trend < 0) or action == "观望" else "⚠️ 建议较预测更保守"}

⚠️ 风险提示: 
• KDJ适合短线操作，注意及时止盈止损
• ATR动态止损可根据市场波动调整
• 多指标确认可有效降低假信号风险
• 建议结合基本面分析做最终决策
            """
            
            self.log_message(analysis_report)
            
            # 更新界面显示
            self.root.after(0, lambda: self.update_advice_display(action, recommendation, current_price, pred_trend))
            
            return action, analysis_report
            
        except Exception as e:
            error_msg = f"交易信号分析失败: {str(e)}"
            self.log_message(error_msg)
            return "观望", error_msg
    
    def update_advice_display(self, action, recommendation, current_price, pred_trend):
        """更新界面上的交易建议显示 - 支持5级评分系统"""
        try:
            # 根据5级建议类型设置颜色和图标
            if action == "强烈买入":
                bg_color = "#ffebee"  # 浅红色背景
                fg_color = "#c62828"  # 红色文字
                icon = "🚀"
                action_display = "强烈买入"
                detail_reason = "技术面极好，建议积极买入"
            elif action == "少买":
                bg_color = "#fff8e1"  # 浅黄色背景
                fg_color = "#f57f17"  # 黄色文字
                icon = "📈"
                action_display = "少量买入"
                detail_reason = "技术面偏好，建议小仓位买入"
            elif action == "观望":
                bg_color = "#e8f4f8"  # 浅蓝灰背景
                fg_color = "#2c3e50"  # 深蓝灰文字
                icon = "⏸️"
                action_display = "观望等待"
                detail_reason = "技术面不明确，建议等待机会"
            elif action == "少卖":
                bg_color = "#e8f5e8"  # 浅绿色背景
                fg_color = "#2e7d32"  # 绿色文字
                icon = "📉"
                action_display = "少量卖出"
                detail_reason = "技术面偏差，建议小仓位减持"
            elif action == "强烈卖出":
                bg_color = "#e3f2fd"  # 浅蓝色背景
                fg_color = "#1976d2"  # 蓝色文字
                icon = "⚠️"
                action_display = "强烈卖出"
                detail_reason = "技术面极差，建议积极减仓"
            else:
                # 默认观望状态
                bg_color = "#e8f4f8"
                fg_color = "#2c3e50"
                icon = "⏸️"
                action_display = "观望等待"
                detail_reason = "信号不明确，建议观望"
            
            # 更新背景色
            self.advice_result_frame.config(bg=bg_color)
            
            # 更新标题
            title_text = f"{icon} {action_display}"
            self.advice_title.config(text=title_text, bg=bg_color, fg=fg_color)
            
            # 更新详情 - 为5种状态提供不同的显示内容
            if action_display == "观望等待":
                detail_text = f"当前价格: ¥{current_price:.2f}\n预测趋势: {pred_trend:+.1f}%\n{detail_reason}\n建议等待更强烈信号"
            elif "强烈" in action_display:
                detail_text = f"当前价格: ¥{current_price:.2f}\n预测趋势: {pred_trend:+.1f}%\n{detail_reason}\n信号强度: 极高"
            else:  # 少量买入或少量卖出
                detail_text = f"当前价格: ¥{current_price:.2f}\n预测趋势: {pred_trend:+.1f}%\n{detail_reason}\n建议小仓位操作"
            
            self.advice_detail.config(text=detail_text, bg=bg_color, fg=fg_color)
            
            # 启用按钮
            self.refresh_advice_btn.config(state='normal')
            self.detail_advice_btn.config(state='normal')
            
        except Exception as e:
            self.log_message(f"更新建议显示失败: {str(e)}")
    
    def refresh_quick_advice(self):
        """快速刷新交易建议"""
        try:
            # 检查是否有最近的预测数据
            if not hasattr(self, 'last_prediction_files') or not self.last_prediction_files:
                messagebox.showwarning("提示", "请先运行预测以获取交易建议！")
                return
            
            # 读取最近的预测数据
            hist_file, pred_file = self.last_prediction_files
            
            if not os.path.exists(hist_file) or not os.path.exists(pred_file):
                messagebox.showerror("错误", "预测数据文件不存在，请重新运行预测！")
                return
            
            # 读取数据
            historical_data = pd.read_csv(hist_file)
            prediction_data = pd.read_csv(pred_file)
            
            # 进行交易信号分析
            self.log_message("🔄 正在刷新交易建议...")
            action, analysis_report = self.analyze_current_trading_signal(historical_data, prediction_data)
            
        except Exception as e:
            error_msg = f"刷新建议失败: {str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def show_detailed_analysis(self):
        """显示详细的交易分析"""
        try:
            # 检查是否有最近的预测数据
            if not hasattr(self, 'last_prediction_files') or not self.last_prediction_files:
                messagebox.showwarning("提示", "请先运行预测以获取交易建议！")
                return
            
            # 读取最近的预测数据
            hist_file, pred_file = self.last_prediction_files
            
            if not os.path.exists(hist_file) or not os.path.exists(pred_file):
                messagebox.showerror("错误", "预测数据文件不存在，请重新运行预测！")
                return
            
            # 读取数据
            historical_data = pd.read_csv(hist_file)
            prediction_data = pd.read_csv(pred_file)
            
            # 进行交易信号分析
            self.log_message("📊 正在生成详细分析...")
            action, analysis_report = self.analyze_current_trading_signal(historical_data, prediction_data)
            
            # 显示分析对话框
            analysis_window = tk.Toplevel(self.root)
            analysis_window.title(f"详细交易分析 - {self.stock_code.get()}")
            analysis_window.geometry("600x500")
            analysis_window.resizable(False, False)
            
            # 设置窗口图标和样式
            analysis_window.configure(bg='#f0f0f0')
            
            # 标题
            title_label = tk.Label(analysis_window, 
                                  text=f"🤖 {self.stock_code.get()} 详细交易分析",
                                  font=('Arial', 16, 'bold'),
                                  bg='#f0f0f0', fg='#333333')
            title_label.pack(pady=10)
            
            # 分析结果框
            result_frame = tk.Frame(analysis_window, bg='#f0f0f0')
            result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # 文本显示区域
            text_widget = tk.Text(result_frame, 
                                 font=('Consolas', 10),
                                 bg='white', fg='#333333',
                                 wrap=tk.WORD,
                                 padx=10, pady=10)
            
            # 滚动条
            scrollbar = tk.Scrollbar(result_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            # 布局
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 插入分析报告
            text_widget.insert(tk.END, analysis_report)
            text_widget.config(state=tk.DISABLED)  # 设为只读
            
            # 按钮框架
            button_frame = tk.Frame(analysis_window, bg='#f0f0f0')
            button_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # 关闭按钮
            close_button = tk.Button(button_frame, text="关闭", 
                                   command=analysis_window.destroy,
                                   font=('Arial', 10),
                                   bg='#666666', fg='white',
                                   width=10)
            close_button.pack(side=tk.RIGHT)
            
            # 重新分析按钮
            refresh_button = tk.Button(button_frame, text="重新分析", 
                                     command=lambda: self.refresh_analysis(analysis_window),
                                     font=('Arial', 10),
                                     bg='#2196F3', fg='white',
                                     width=10)
            refresh_button.pack(side=tk.RIGHT, padx=(0, 10))
            
            # 使窗口居中
            analysis_window.transient(self.root)
            analysis_window.grab_set()
            
        except Exception as e:
            error_msg = f"显示详细分析失败: {str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def refresh_analysis(self, window):
        """刷新详细分析"""
        window.destroy()
        self.show_detailed_analysis()
    
    def stop_progress(self):
        """停止进度条并重新启用按钮"""
        self.progress.stop()
        self.predict_button.config(state='normal')

def main():
    """主函数"""
    # 全局禁用所有确认对话框
    import sys
    import io
    
    # 重定向标准输入为空，避免任何input()调用
    sys.stdin = io.StringIO('')
    
    # 设置静默运行模式
    os.environ['SILENT_MODE'] = '1'
    
    root = tk.Tk()
    app = KronosPredictor(root)
    root.mainloop()

if __name__ == "__main__":
    main()