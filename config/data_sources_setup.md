# API配置说明文档

## 📊 数据源配置指南

### 1. TuShare配置
1. 访问 https://tushare.pro/register 注册账户
2. 获取token后，将token保存到以下位置之一：
   - 环境变量：`set TUSHARE_TOKEN=your_token_here`
   - 配置文件：创建 `config/tushare_token.txt` 并写入token

### 2. Alpha Vantage配置
1. 访问 https://www.alphavantage.co/support/#api-key 免费注册
2. 获取API key后，将key保存到以下位置之一：
   - 环境变量：`set ALPHA_VANTAGE_KEY=your_key_here`
   - 配置文件：创建 `config/alpha_vantage_key.txt` 并写入key

### 3. 安装依赖包
```bash
# 基础依赖
pip install akshare pandas numpy

# 可选依赖（推荐安装）
pip install yfinance tushare requests

# 完整安装命令
pip install akshare yfinance tushare requests pandas numpy
```

### 4. 使用示例
```python
from data_sources.multi_source_provider import MultiSourceDataProvider

# 创建数据提供器
provider = MultiSourceDataProvider()

# 获取股票数据（自动尝试多个数据源）
data = provider.get_stock_data('000001', 'daily')

# 测试所有数据源可用性
results = provider.test_all_sources()
print(results)
```