# Lighter - Paradex 专业跨交易所套利系统

基于 cross-exchange-arbitrage 架构的专业级套利系统，专门优化用于 Lighter 和 Paradex 交易所之间的价差套利。

## 📁 项目结构

```
lighter-paradex-arbitrage/
├── arbitrage.py                    # 主程序入口
├── .env                            # 配置文件
├── requirements.txt                # 依赖列表
│
├── exchanges/                      # 交易所接口层
│   ├── __init__.py
│   ├── base_exchange.py           # 交易所基类
│   ├── lighter_exchange.py        # Lighter 实现
│   └── paradex_exchange.py        # Paradex 实现
│
├── strategy/                       # 策略核心层
│   ├── __init__.py
│   ├── arbitrage_engine.py        # 套利引擎
│   ├── position_tracker.py        # 持仓追踪
│   ├── order_manager.py           # 订单管理
│   └── data_logger.py             # 数据日志
│
├── utils/                          # 工具层
│   ├── __init__.py
│   ├── telegram_notifier.py       # Telegram 通知
│   └── config_loader.py           # 配置加载
│
└── logs/                           # 日志目录
    ├── trades/                     # 交易日志
    └── errors/                     # 错误日志
```

## 🎯 核心特性

### 1. 模块化架构
- **交易所层**: 统一的交易所接口，易于扩展
- **策略层**: 独立的套利引擎和风险管理
- **工具层**: 通知、日志等辅助功能

### 2. 智能套利引擎
- **实时价差监控**: WebSocket + 轮询双模式
- **自动套利决策**: 基于价差阈值触发
- **智能订单管理**: Maker + Taker 组合策略

### 3. 风险控制
- **持仓追踪**: 实时监控两边持仓
- **最大持仓限制**: 防止过度暴露
- **订单超时保护**: 自动取消未成交订单
- **对冲失败告警**: 立即推送紧急通知

### 4. 数据与日志
- **交易日志**: CSV 格式记录所有交易
- **错误日志**: 详细的异常追踪
- **性能指标**: 实时统计和报告

## 🚀 快速开始

### 1. 环境要求

```bash
Python 3.9 - 3.12
虚拟环境推荐
```

### 2. 安装步骤

```bash
# 克隆项目
git clone https://github.com/jinzhufadacai-cyber/lighter-paradex-arbitrage.git
cd lighter-paradex-arbitrage

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置 API

创建 `.env` 文件：

```bash
# Lighter 配置
LIGHTER_PRIVATE_KEY="0x..."
LIGHTER_ACCOUNT_INDEX=0
LIGHTER_API_KEY_INDEX=0

# Paradex 配置
PARADEX_L1_ADDRESS="0x..."
PARADEX_L2_PRIVATE_KEY="0x..."

# Telegram 通知
TG_BOT_TOKEN="..."
TG_ADMIN_CHAT_ID="..."
```

### 4. 运行系统

```bash
# 基础运行
python lighter_paradex_arb_pro.py --ticker BTC --size 0.01

# 完整参数
python lighter_paradex_arb_pro.py \
  --ticker BTC \
  --size 0.01 \
  --max-position 0.1 \
  --long-threshold 15 \
  --short-threshold 15 \
  --fill-timeout 5
```

## ⚙️ 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--ticker` | str | 必填 | 交易对 (BTC, ETH, SOL) |
| `--size` | float | 0.01 | 每笔交易量 |
| `--max-position` | float | 1.0 | 最大持仓限制 |
| `--long-threshold` | float | 10.0 | 做多阈值（美元） |
| `--short-threshold` | float | 10.0 | 做空阈值（美元） |
| `--fill-timeout` | int | 5 | 订单超时（秒） |

## 📊 工作原理

### 套利流程

```
实时监控订单簿
     ↓
计算价差
     ↓
价差 > 阈值？
     ↓ YES
检查持仓限制
     ↓ OK
执行套利交易
     ↓
记录日志 + 发送通知
     ↓
继续监控...
```

## ⚖️ 免责声明

本项目仅供学习和研究使用。加密货币交易涉及重大风险，使用风险自负。