# Lighter-Paradex 套利机器人 - 完整设置指南

## 📋 目录
1. [快速开始](#快速开始)
2. [环境要求](#环境要求)
3. [安装步骤](#安装步骤)
4. [配置说明](#配置说明)
5. [运行方式](#运行方式)
6. [Telegram机器人设置](#telegram机器人设置)
7. [云服务器部署](#云服务器部署)
8. [故障排除](#故障排除)

---

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/jinzhufadacai-cyber/lighter-paradex-arbitrage.git
cd lighter-paradex-arbitrage

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入真实的API密钥

# 5. 运行套利脚本
python L_P.py --symbol BTC/USDT --size 0.001
```

---

## 环境要求

| 项目 | 要求 |
|------|------|
| Python | 3.9 - 3.12 |
| 操作系统 | Windows / Linux / macOS |
| 网络 | 稳定的互联网连接 |

### 推荐云服务器配置
```
最低配置: 2核 CPU, 4GB 内存, 50GB SSD
推荐配置: 4核 CPU, 8GB 内存, 100GB SSD
推荐系统: Ubuntu 20.04/22.04 LTS
```

---

## 安装步骤

### Windows 安装

```powershell
# 安装 Python 3.12 (从 python.org 下载)

# 创建虚拟环境
cd C:\path\to\lighter-paradex-arbitrage
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### Linux/macOS 安装

```bash
# 安装 Python
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev -y

# 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 常见安装问题

**问题: 安装卡在 torch 下载**
```bash
# 使用安全安装方式
pip install -r requirements-safe.txt
# 或使用约束文件
pip install -r requirements.txt -c constraints.txt
```

**问题: Microsoft Visual C++ 错误 (Windows)**
```bash
# 安装 Visual Studio Build Tools
# 下载: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

---

## 配置说明

### 环境变量 (.env)

```bash
# Lighter 交易所配置
API_KEY_PRIVATE_KEY=0x你的私钥
LIGHTER_ACCOUNT_INDEX=0
LIGHTER_API_KEY_INDEX=0

# Paradex 交易所配置
PARADEX_L1_ADDRESS=0x你的L1地址
PARADEX_L2_PRIVATE_KEY=0x你的L2私钥

# Telegram 配置 (可选)
TELEGRAM_BOT_TOKEN=你的Bot_Token
TELEGRAM_CHAT_ID=你的Chat_ID
AUTHORIZED_USERS=你的用户ID
```

### 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--symbol` | BTC/USDT | 交易对 |
| `--size` | 0.001 | 每笔交易量 |
| `--max-position` | 0.1 | 最大持仓 |
| `--long-threshold` | 10.0 | 做多阈值($) |
| `--short-threshold` | 10.0 | 做空阈值($) |
| `--fill-timeout` | 30 | 订单超时(秒) |
| `--scan-interval` | 2.0 | 扫描间隔(秒) |

---

## 运行方式

### 方式1: 直接运行套利脚本

```bash
python L_P.py --symbol BTC/USDT --size 0.001 --max-position 0.1
```

### 方式2: 通过Telegram机器人控制

```bash
# 启动Telegram控制器
python telegram_bot.py

# 然后在Telegram中使用命令控制
```

### 方式3: 后台运行 (Linux)

```bash
# 使用 screen
screen -S arbitrage-bot
python L_P.py --symbol BTC/USDT --size 0.001
# 按 Ctrl+A, D 分离

# 使用 nohup
nohup python L_P.py --symbol BTC/USDT --size 0.001 > output.log 2>&1 &
```

---

## Telegram机器人设置

### 步骤1: 创建Bot
1. 在Telegram搜索 `@BotFather`
2. 发送 `/newbot` 创建机器人
3. 保存获得的 Bot Token

### 步骤2: 获取Chat ID
1. 向你的机器人发送 `/start`
2. 访问: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. 找到 `"id"` 字段

### 步骤3: 配置环境变量
```bash
TELEGRAM_BOT_TOKEN=你的token
AUTHORIZED_USERS=你的用户ID
```

### 可用命令
| 命令 | 功能 |
|------|------|
| `/start` | 启动机器人 |
| `/status` | 查看状态 |
| `/run` | 启动套利 |
| `/stop` | 停止套利 |
| `/balance` | 查看余额 |
| `/config` | 查看配置 |
| `/emergency_stop` | 紧急停止 |

---

## 云服务器部署

### 一键部署脚本

```bash
#!/bin/bash
# 在服务器上执行

# 安装依赖
sudo apt update && sudo apt install -y python3.9 python3.9-venv git

# 克隆项目
git clone https://github.com/jinzhufadacai-cyber/lighter-paradex-arbitrage.git
cd lighter-paradex-arbitrage

# 设置环境
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置
cp .env.example .env
nano .env  # 填入API密钥

echo "部署完成! 运行: python L_P.py --symbol BTC/USDT --size 0.001"
```

### 使用 systemd 服务

创建 `/etc/systemd/system/arbitrage-bot.service`:
```ini
[Unit]
Description=Lighter-Paradex Arbitrage Bot
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/home/用户名/lighter-paradex-arbitrage
Environment="PATH=/home/用户名/lighter-paradex-arbitrage/venv/bin"
ExecStart=/home/用户名/lighter-paradex-arbitrage/venv/bin/python L_P.py --symbol BTC/USDT --size 0.001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable arbitrage-bot
sudo systemctl start arbitrage-bot
```

---

## 故障排除

### 常见错误及解决方案

**1. ModuleNotFoundError: No module named 'telegram'**
```bash
pip install python-telegram-bot
```

**2. 缺少必要的环境变量**
```bash
# 检查.env文件是否正确配置
cat .env

# 确保变量格式正确，没有多余空格
```

**3. SDK导入失败**
```bash
# 安装交易所SDK
pip install git+https://github.com/tradeparadex/paradex-py.git
pip install lighter
```

**4. 权限不足**
```bash
# Linux: 设置文件权限
chmod 600 .env
chmod +x L_P.py
```

**5. Telegram Bot 未授权**
```bash
# 确保AUTHORIZED_USERS包含你的用户ID
# 用户ID是数字，不是用户名
```

### 日志检查

```bash
# 查看机器人日志
tail -f telegram_bot.log

# 查看套利日志
tail -f lighter_paradex_arbitrage_*.log
```

---

## 项目文件说明

| 文件 | 说明 |
|------|------|
| `L_P.py` | 主套利脚本 |
| `telegram_bot.py` | Telegram机器人（控制+通知） |
| `arbitrage.py` | 套利基础模块 |
| `exchanges/` | 交易所实现 |
| `requirements.txt` | 依赖列表 |
| `.env` | 配置文件 (需创建) |

---

## 安全建议

1. **永远不要** 将 `.env` 文件提交到Git
2. **定期更换** API密钥
3. **使用最小权限** 的API密钥
4. **设置IP白名单** (如果交易所支持)
5. **监控日志** 检查异常活动

---

## 联系与支持

- GitHub Issues: 提交问题和建议
- 文档更新: 查看最新版本

**最后更新**: 2026-01-05

