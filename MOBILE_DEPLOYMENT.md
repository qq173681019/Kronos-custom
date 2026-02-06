# Kronos Mobile Deployment Guide

## 移动端部署指南

本项目现已支持移动端访问和Vercel部署。

### 快速开始

#### 1. 生成移动端报告

```bash
python generate_mobile_reports.py
```

这将生成:
- `mobile_reports/index.html` - 移动端首页
- `mobile_reports/{股票代码}_daily_mobile.html` - 各股票详细预测页面

#### 2. 本地预览

直接用浏览器打开 `mobile_reports/index.html`，或使用Python启动简单服务器:

```bash
cd mobile_reports
python -m http.server 8000
```

然后访问: http://localhost:8000

#### 3. 部署到Vercel

方法一：使用Vercel CLI
```bash
cd mobile_reports
vercel deploy
```

方法二：GitHub集成
1. 将 `mobile_reports` 内容推送到GitHub仓库
2. 在Vercel中导入该仓库
3. 设置构建输出目录为 `.` (当前目录)
4. 部署完成

### 特性

✅ 完全响应式设计，适配各种移动设备  
✅ 静态HTML，加载速度快  
✅ 离线可用，无需后端API  
✅ 使用现有的BatchStockAnalyzer引擎  
✅ 预计算所有预测数据  

### 自定义股票列表

编辑 `generate_mobile_reports.py` 中的股票列表:

```python
popular_stocks = ['600519', '600036', '000858']  # 添加你的股票代码
```

### 定时更新

可以设置cron任务定期重新生成报告:

```bash
# 每天9点更新
0 9 * * * cd /path/to/Kronos-custom && python generate_mobile_reports.py
```

### 注意事项

- 生成的报告包含预测数据的快照，不会实时更新
- 建议定期重新生成以获取最新预测
- 所有预测使用多模型集成算法（技术指标+机器学习+支撑阻力位）
- 数据来源：AkShare → yfinance → Tencent → Baostock（自动切换）

### 技术架构

```
BatchStockAnalyzer (现有引擎)
        ↓
export_mobile_json() (新增方法)
        ↓
MobileReportBuilder (HTML生成器)
        ↓
static HTML files (可部署到任何静态托管)
```

### 移动端特性

- 触摸优化的UI界面
- 渐变色彩设计
- 大号字体，易于阅读
- 简洁的预测卡片布局
- 实时趋势指示器
- 置信度可视化

---

由Kronos AI Team提供技术支持
