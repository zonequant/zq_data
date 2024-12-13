# ZQ Data - 基于 Polars 的行情数据服务设计文档

## 1. 系统概述

### 1.1 整体架构

#### 1.1.1 核心组件
1. **数据采集层**
   - REST API采集模块
   - WebSocket实时订阅模块
   - 数据标准化模块

2. **数据存储层**
   - Parquet文件存储
   - 文件系统管理
   - 数据压缩和索引

3. **查询服务层**
   - 统一查询接口
   - 数据加载优化
   - 并发查询支持

#### 1.1.2 系统特点
1. **高性能**
   - 基于Polars的高效数据处理
   - 异步IO操作
   - 批量数据处理

2. **可扩展**
   - 模块化设计
   - 标准化接口
   - 插件化架构

3. **可靠性**
   - 数据校验机制
   - 自动重试机制
   - 异常处理

## 2. 数据存储设计

### 2.1 文件命名规范
```
{broker}/{market}/{data_type}/{symbol}_{frequency}_{date}.parquet

data_type: tick 或 kline

示例：
- ctp/futures/tick/IF2403_tick_20240113.parquet     # 中金所IF主力合约逐笔数据
- ctp/futures/kline/IF2403_1m_20240113.parquet      # 中金所IF主力合约1分钟K线
- xtp/sh/tick/000001_tick_20240113.parquet         # 上证指数逐笔数据
- xtp/sh/kline/000001_1m_20240113.parquet          # 上证指数1分钟K线
- binance/spot/tick/btcusdt_tick_20240113.parquet  # 币安BTC/USDT现货逐笔数据
- binance/spot/kline/btcusdt_1m_20240113.parquet   # 币安BTC/USDT现货1分钟K线
- ib/nasdaq/tick/aapl_tick_20240113.parquet        # IB纳斯达克AAPL逐笔数据
- ib/nasdaq/kline/aapl_1m_20240113.parquet         # IB纳斯达克AAPL 1分钟K线
```

### 2.2 目录结构
```
data/
├── ctp/                        # CTP期货数据
│   └── futures/               # 期货市场
│       ├── tick/             # 逐笔数据
│       │   └── IF2403/       # IF主力合约
│       │       └── 2024/     # 按年组织
│       └── kline/            # K线数据
│           └── IF2403/       # IF主力合约
│               └── 2024/     # 按年组织
├── xtp/                        # XTP证券数据
│   ├── sh/                    # 上海市场
│   │   ├── tick/            # 逐笔数据
│   │   │   └── 2024/        # 按年组织
│   │   └── kline/           # K线数据
│   │       └── 2024/        # 按年组织
│   └── sz/                    # 深圳市场
│       ├── tick/
│       │   └── 2024/
│       └── kline/
│           └── 2024/
└── binance/                    # 币安数据
    ├── spot/                  # 现货市场
    │   ├── tick/
    │   │   └── 2024/
    │   └── kline/
    │       └── 2024/
    └── futures/               # 合约市场
        ├── tick/
        │   └── 2024/
        └── kline/
            └── 2024/
```

### 2.3 数据管理策略
- 按天切分文件，文件名包含日期信息
- 按年组织目录结构，便于管理和查询
- 支持数据压缩和优化存储
- 自动管理数据生命周期

## 3. 数据采集系统

### 3.1 数据采集架构

#### 3.1.1 采集方式
1. **REST API采集**
   - 用于获取历史数据
   - 支持定时任务采集
   - 支持数据补全
   - 支持批量请求

2. **WebSocket实时采集**
   - 用于订阅实时数据
   - 支持断线重连
   - 支持心跳检测
   - 支持多路订阅

#### 3.1.2 数据类型
1. **Tick数据**
   - 逐笔成交
   - 实时深度
   - 逐笔委托

2. **K线数据**
   - 支持标准周期：1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1M
   - 支持自定义周期
   - 支持实时计算和历史计算

#### 3.1.3 核心功能
1. **数据采集**
   - 多源并行采集
   - 自动重试机制
   - 断点续传
   - 数据校验

2. **实时处理**
   - 事件驱动架构
   - 回调函数机制
   - 实时数据处理
   - 异常处理机制

### 3.2 适配器设计

#### 3.2.1 统一接口
1. **REST接口**
   - 获取历史K线数据
   - 获取历史Tick数据
   - 支持时间范围查询
   - 支持分页请求

2. **WebSocket接口**
   - 订阅实时数据
   - 支持回调函数
   - 支持取消订阅
   - 连接状态管理

#### 3.2.2 支持的交易所
1. **期货市场**
   - CTP（中国期货市场）
   - CME（芝加哥商品交易所）

2. **股票市场**
   - XTP（国内股票）
   - Interactive Brokers（海外市场）

3. **数字货币**
   - Binance（币安）
   - OKX
   - Bybit

#### 3.2.3 数据标准化
1. **字段映射**
   - 统一字段名称
   - 统一数据类型
   - 统一时间格式

2. **数据转换**
   - 价格标准化
   - 数量标准化
   - 时区处理

## 4. 查询接口

### 4.1 统一查询接口
```python
class DataService:
    async def get_tick(self, symbol: str, start_time: datetime, end_time: datetime) -> pl.DataFrame:
        """获取Tick数据"""
        pass
    
    async def get_kline(self, symbol: str, freq: str, start_time: datetime, end_time: datetime) -> pl.DataFrame:
        """获取K线数据"""
        pass
    
    async def subscribe_real_time(self, symbol: str, callback: Callable):
        """订阅实时数据"""
        pass
```