# Lighter-Paradex 跨交易所套利系统

基于 cross-exchange-arbitrage 架构的专业级套利系统，实现 Lighter 和 Paradex 交易所之间的价差套利。

## 📁 项目结构

```
lighter-paradex-arbitrage/
├── L_P.py                # 主套利脚本
├── arbitrage.py          # 套利基础模块
├── telegram_bot.py       # Telegram机器人(控制+通知)
├── exchanges/            # 交易所实现
│   ├── lighter_real.py   # Lighter交易所
│   └── paradex_real.py   # Paradex交易所
├── requirements.txt      # 依赖列表
├── SETUP_GUIDE.md        # 完整设置指南
└── README.md             # 本文件
```

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/jinzhufadacai-cyber/lighter-paradex-arbitrage.git
cd lighter-paradex-arbitrage

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp .env.example .env
# 编辑.env填入真实密钥

# 运行
python L_P.py --symbol BTC/USDT --size 0.001
```

## ⚙️ 主要参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--symbol` | BTC/USDT | 交易对 |
| `--size` | 0.001 | 每笔交易量 |
| `--max-position` | 0.1 | 最大持仓 |
| `--long-threshold` | 10.0 | 做多阈值($) |
| `--short-threshold` | 10.0 | 做空阈值($) |

## 🤖 Telegram控制

支持通过Telegram机器人远程控制套利系统：

```bash
# 设置环境变量
TELEGRAM_BOT_TOKEN=你的token
AUTHORIZED_USERS=你的用户ID

# 方式1: 独立运行控制器
python telegram_bot.py

# 方式2: 与套利脚本一起运行
python L_P.py --symbol BTC/USDT --size 0.001 --telegram-token YOUR_TOKEN
```

**可用命令**: `/start`, `/status`, `/run`, `/stop`, `/balance`, `/config`

## 📖 详细文档

请查看 [SETUP_GUIDE.md](SETUP_GUIDE.md) 获取完整的安装、配置和部署指南。

## ⚠️ 免责声明

本项目仅供学习和研究使用。加密货币交易涉及重大风险，使用风险自负。
