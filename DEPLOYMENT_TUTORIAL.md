# Lighter和Paradex套利脚本云服务器部署教程

## 📋 目录
1. [云服务器选择与配置](#1-云服务器选择与配置)
2. [本地环境准备](#2-本地环境准备)
3. [文件上传到云服务器](#3-文件上传到云服务器)
4. [云服务器环境配置](#4-云服务器环境配置)
5. [脚本安装与运行](#5-脚本安装与运行)
6. [后台运行与管理](#6-后台运行与管理)
7. [监控与日志管理](#7-监控与日志管理)
8. [故障排除](#8-故障排除)
9. [安全建议](#9-安全建议)

---

## 1. 云服务器选择与配置

### 1.1 推荐云服务商
- **阿里云 ECS**：适合国内用户，网络稳定
- **腾讯云 CVM**：性价比高，中文支持好
- **AWS EC2**：全球覆盖，功能强大
- **Vultr/DigitalOcean**：海外服务，适合国际用户

### 1.2 服务器配置建议
```yaml
最低配置（测试/开发）:
- CPU: 2核
- 内存: 4GB
- 存储: 50GB SSD
- 带宽: 5Mbps

推荐配置（生产环境）:
- CPU: 4核
- 内存: 8GB
- 存储: 100GB SSD
- 带宽: 10Mbps以上
```

### 1.3 操作系统选择
```bash
推荐系统: Ubuntu 20.04/22.04 LTS
备选系统: CentOS 7/8, Debian 11

# 理由：
# 1. Ubuntu有完善的Python生态
# 2. 社区支持好，教程资源多
# 3. 长期支持版本稳定
```

### 1.4 安全组配置
在云控制台配置安全组规则：

| 端口 | 协议 | 用途 | 建议 |
|------|------|------|------|
| 22 | TCP | SSH连接 | 限制为您的IP |
| 80/443 | TCP | Web访问（可选） | 可选开放 |
| 自定义端口 | TCP | Telegram Bot Webhook | 按需开放 |

---

## 2. 本地环境准备

### 2.1 安装必要的工具

#### Windows用户
```powershell
# 1. 安装 Git（用于代码管理和SCP）
# 下载地址：https://git-scm.com/download/win

# 2. 安装 WinSCP 或 FileZilla（图形化文件传输）
# WinSCP: https://winscp.net/eng/download.php
# FileZilla: https://filezilla-project.org/

# 3. 安装 PuTTY（SSH连接工具）
# 下载地址：https://www.putty.org/
```

#### macOS/Linux用户
```bash
# 检查是否已安装必要工具
which ssh  # SSH客户端
which scp  # 安全文件传输
which git  # Git版本控制
```

### 2.2 准备项目文件
在本地计算机上整理项目文件：

```bash
项目结构：
lighter-paradex-arbitrage/
├── L_P.py                    # 主程序
├── arbitrage.py              # 核心框架
├── telegram_control.py       # Telegram控制
├── requirements.txt          # 依赖列表
├── .env.example             # 环境变量模板
├── README.md                # 说明文档
├── DEPLOYMENT_TUTORIAL.md   # 本教程
└── exchanges/
    └── astros.py            # 交易所示例
```

### 2.3 创建配置文件
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入您的真实配置
# 注意：不要在代码仓库中提交包含密钥的.env文件！
```

---

## 3. 文件上传到云服务器

### 3.1 方法一：使用SCP（命令行）

```bash
# 1. 连接到服务器（Windows使用Git Bash或WSL）
ssh username@your-server-ip

# 2. 创建项目目录
mkdir -p ~/projects/lighter-paradex

# 3. 从本地上传文件（在本地终端执行）
# 上传整个文件夹
scp -r lighter-paradex-arbitrage username@your-server-ip:~/projects/

# 或逐个上传重要文件
scp L_P.py username@your-server-ip:~/projects/lighter-paradex/
scp arbitrage.py username@your-server-ip:~/projects/lighter-paradex/
scp requirements.txt username@your-server-ip:~/projects/lighter-paradex/
scp .env username@your-server-ip:~/projects/lighter-paradex/
```

### 3.2 方法二：使用Git

```bash
# 1. 在服务器上安装Git
ssh username@your-server-ip
sudo apt update && sudo apt install git -y

# 2. 克隆项目（如果使用Git托管）
cd ~/projects
git clone https://your-repository-url.git lighter-paradex

# 3. 上传环境配置文件
# 将本地的.env文件上传到服务器
scp .env username@your-server-ip:~/projects/lighter-paradex/
```

### 3.3 方法三：使用WinSCP（Windows图形化）

1. **打开WinSCP**
2. **新建会话**：
   - 主机名：服务器IP地址
   - 端口：22
   - 用户名：您的用户名
   - 密码：您的密码或使用密钥

3. **上传文件**：
   - 左侧窗口：本地文件
   - 右侧窗口：服务器目录
   - 拖拽整个文件夹到服务器

4. **设置权限**：
   - 右键点击上传的文件
   - 选择"属性"
   - 设置755权限（可执行）

---

## 4. 云服务器环境配置

### 4.1 连接到服务器
```bash
ssh username@your-server-ip
# 如果是首次连接，会提示确认主机密钥
```

### 4.2 系统更新
```bash
# 更新系统包
sudo apt update
sudo apt upgrade -y

# 安装基本工具
sudo apt install -y curl wget vim htop net-tools
```

### 4.3 Python环境安装

```bash
# 1. 安装Python 3.9（推荐版本）
sudo apt install -y python3.9 python3.9-venv python3.9-dev

# 2. 创建Python虚拟环境
cd ~/projects/lighter-paradex
python3.9 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 升级pip
pip install --upgrade pip
```

### 4.4 安装依赖
```bash
# 在虚拟环境中执行
source venv/bin/activate
pip install -r requirements.txt

# 如果需要，可以单独安装特定版本
pip install python-telegram-bot==20.7
pip install aiohttp>=3.8.0
pip install websockets>=12.0
pip install python-dotenv>=1.0.0
```

### 4.5 环境变量配置
```bash
# 1. 将.env文件放到项目目录
# 确保.env文件包含正确的API密钥

# 2. 设置环境变量权限
chmod 600 .env

# 3. 可选：将环境变量添加到系统
# 编辑 ~/.bashrc 或 ~/.profile
echo 'export LIGHTER_API_KEY="your_key_here"' >> ~/.bashrc
echo 'export PARADEX_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

---

## 5. 脚本安装与运行

### 5.1 测试安装
```bash
cd ~/projects/lighter-paradex
source venv/bin/activate

# 测试Python环境
python --version

# 测试模块导入
python -c "import asyncio; import telegram; print('环境正常')"
```

### 5.2 运行脚本（测试模式）
```bash
# 第一次运行使用测试参数
python L_P.py --help

# 测试运行（不连接真实交易所）
python L_P.py --symbol BTC/USDT --size 0.001 --max-position 0.1 --scan-interval 5.0
```

### 5.3 配置Telegram Bot（可选）
```bash
# 如果使用Telegram控制，需要配置Webhook
# 1. 获取Bot Token：从 @BotFather
# 2. 获取Chat ID：从 @userinfobot
# 3. 在.env文件中配置：
# TELEGRAM_BOT_TOKEN=your_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here

# 4. 启动脚本时带上Telegram参数
python L_P.py \
  --symbol BTC/USDT \
  --size 0.001 \
  --max-position 0.1 \
  --telegram-token YOUR_BOT_TOKEN \
  --telegram-chat-id YOUR_CHAT_ID
```

---

## 6. 后台运行与管理

### 6.1 使用screen（简单方法）
```bash
# 1. 安装screen
sudo apt install screen -y

# 2. 创建新的screen会话
screen -S arbitrage-bot

# 3. 在screen中运行脚本
cd ~/projects/lighter-paradex
source venv/bin/activate
python L_P.py [参数]

# 4. 分离screen会话（保持运行）
按 Ctrl+A，然后按 D

# 5. 重新连接会话
screen -r arbitrage-bot

# 6. 查看所有screen会话
screen -ls
```

### 6.2 使用tmux（更强大）
```bash
# 1. 安装tmux
sudo apt install tmux -y

# 2. 创建新的tmux会话
tmux new -s arbitrage-bot

# 3. 运行脚本
cd ~/projects/lighter-paradex
source venv/bin/activate
python L_P.py [参数]

# 4. 分离tmux会话
按 Ctrl+B，然后按 D

# 5. 重新连接
tmux attach -t arbitrage-bot

# 6. 查看会话列表
tmux ls
```

### 6.3 使用systemd服务（生产环境推荐）

#### 创建服务文件
```bash
sudo vim /etc/systemd/system/arbitrage-bot.service
```

服务文件内容：
```ini
[Unit]
Description=Lighter and Paradex Arbitrage Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/projects/lighter-paradex
Environment="PATH=/home/your_username/projects/lighter-paradex/venv/bin"
ExecStart=/home/your_username/projects/lighter-paradex/venv/bin/python L_P.py \
  --symbol BTC/USDT \
  --size 0.001 \
  --max-position 0.1 \
  --telegram-token YOUR_BOT_TOKEN \
  --telegram-chat-id YOUR_CHAT_ID
Restart=always
RestartSec=10
StandardOutput=file:/var/log/arbitrage-bot.log
StandardError=file:/var/log/arbitrage-bot-error.log

[Install]
WantedBy=multi-user.target
```

#### 管理服务：
```bash
# 1. 重新加载systemd配置
sudo systemctl daemon-reload

# 2. 启动服务
sudo systemctl start arbitrage-bot

# 3. 查看服务状态
sudo systemctl status arbitrage-bot

# 4. 设置开机自启
sudo systemctl enable arbitrage-bot

# 5. 停止服务
sudo systemctl stop arbitrage-bot

# 6. 查看日志
sudo journalctl -u arbitrage-bot -f
```

### 6.4 使用supervisor（进程管理）
```bash
# 1. 安装supervisor
sudo apt install supervisor -y

# 2. 创建配置文件
sudo vim /etc/supervisor/conf.d/arbitrage-bot.conf
```

#### supervisor配置：
```ini
[program:arbitrage-bot]
command=/home/your_username/projects/lighter-paradex/venv/bin/python L_P.py --symbol BTC/USDT --size 0.001
directory=/home/your_username/projects/lighter-paradex
user=your_username
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/arbitrage-bot.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=HOME="/home/your_username",USER="your_username",PATH="/home/your_username/projects/lighter-paradex/venv/bin"
```

#### 管理进程：
```bash
# 重载配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动进程
sudo supervisorctl start arbitrage-bot

# 查看状态
sudo supervisorctl status arbitrage-bot

# 查看所有进程
sudo supervisorctl status
```

---

## 7. 监控与日志管理

### 7.1 日志配置
```bash
# 查看实时日志
tail -f /var/log/arbitrage-bot.log

# 查看错误日志
tail -f /var/log/arbitrage-bot-error.log

# 查看最近100行日志
tail -n 100 /var/log/arbitrage-bot.log

# 按时间筛选日志
grep "2024-01-03" /var/log/arbitrage-bot.log
```

### 7.2 系统资源监控
```bash
# 安装监控工具
sudo apt install htop -y

# 实时监控
htop

# 查看进程
ps aux | grep python

# 查看内存使用
free -h

# 查看磁盘使用
df -h

# 查看网络连接
netstat -tulpn
```

### 7.3 性能监控脚本
创建监控脚本 `monitor.sh`：
```bash
#!/bin/bash
# monitor.sh - 监控套利机器人状态

echo "=== 系统资源监控 ==="
echo "时间: $(date)"
echo "运行时间: $(uptime -p)"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
echo "内存使用: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "磁盘使用: $(df -h / | tail -1 | awk '{print $3"/"$2}')"

echo -e "\n=== 套利机器人进程 ==="
ps aux | grep -E "L_P.py|python.*arbitrage" | grep -v grep

echo -e "\n=== 日志文件大小 ==="
ls -lh /var/log/arbitrage*.log 2>/dev/null || echo "日志文件不存在"

echo -e "\n=== 网络连接 ==="
netstat -an | grep ESTABLISHED | wc -l | xargs echo "活跃连接数:"
```

```bash
# 给予执行权限
chmod +x monitor.sh

# 运行监控脚本
./monitor.sh
```

### 7.4 自动化监控
```bash
# 创建cron任务，每5分钟检查一次
crontab -e

# 添加以下内容：
*/5 * * * * /home/your_username/projects/lighter-paradex/monitor.sh >> /var/log/monitor.log 2>&1
```

---

## 8. 故障排除

### 8.1 常见问题及解决方案

#### 问题1：Python模块导入失败
```bash
# 解决方案：
source venv/bin/activate
pip install -r requirements.txt --force-reinstall

# 检查Python版本
python --version
```

#### 问题2：API连接失败
```bash
# 检查网络连接
ping api.lighter.xyz
ping api.paradex.trade

# 检查防火墙
sudo ufw status

# 测试API密钥
python -c "import os; print('Lighter key:', 'Set' if os.getenv('LIGHTER_API_KEY') else 'Not set')"
```

#### 问题3：Telegram Bot无法连接
```bash
# 检查Token格式
echo $TELEGRAM_BOT_TOKEN

# 测试Telegram API
curl https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe

# 检查网络代理
env | grep -i proxy
```

#### 问题4：脚本意外停止
```bash
# 查看系统日志
sudo journalctl -xe

# 检查内存使用
free -h

# 检查磁盘空间
df -h

# 查看进程信号
dmesg | tail -20
```

### 8.2 调试模式运行
```bash
# 增加详细日志输出
python L_P.py --symbol BTC/USDT --size 0.001 --scan-interval 10.0 --log-dir /tmp/debug-logs

# 使用Python调试
python -m pdb L_P.py --symbol BTC/USDT --size 0.001
```

---

## 9. 安全建议

### 9.1 服务器安全
```bash
# 1. 更新SSH端口
sudo vim /etc/ssh/sshd_config
# 修改 Port 22 为其他端口

# 2. 禁用root登录
sudo vim /etc/ssh/sshd_config
# 设置 PermitRootLogin no

# 3. 使用密钥认证
ssh-keygen -t rsa -b 4096
ssh-copy-id username@your-server-ip

# 4. 配置防火墙
sudo ufw enable
sudo ufw allow 22/tcp  # SSH端口
sudo ufw allow 80/tcp  # HTTP（如果需Web界面）
sudo ufw allow 443/tcp # HTTPS
```

### 9.2 密钥管理
```bash
# 1. 不要将.env文件提交到Git
echo ".env" >> .gitignore
echo "key*." >> .gitignore

# 2. 设置文件权限
chmod 600 .env
chmod 700 ~/projects/lighter-paradex

# 3. 定期更换API密钥
# 在交易所控制台中定期更新API密钥
```

### 9.3 备份策略
```bash
# 1. 创建备份脚本 backup.sh
#!/bin/bash
BACKUP_DIR="/home/your_username/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份配置文件
tar -czf $BACKUP_DIR/arbitrage-config-$DATE.tar.gz \
  .env \
  *.py \
  requirements.txt

# 备份日志
tar -czf $BACKUP_DIR/arbitrage-logs-$DATE.tar.gz \
  /var/log/arbitrage-*.log

echo "备份完成: $BACKUP_DIR/arbitrage-$DATE.tar.gz"

# 2. 设置自动备份
crontab -e
# 每天凌晨2点备份
0 2 * * * /home/your_username/projects/lighter-paradex/backup.sh
```

### 9.4 监控告警
```bash
# 使用简单的监控脚本
#!/bin/bash
# alert.sh - 异常告警脚本

LOG_FILE="/var/log/arbitrage-bot.log"
ERROR_KEYWORDS=("ERROR" "CRITICAL" "FAILED" "EXCEPTION")

for keyword in "${ERROR_KEYWORDS[@]}"; do
    if tail -n 50 $LOG_FILE | grep -q "$keyword"; then
        echo "发现错误关键词: $keyword" | mail -s "套利机器人告警" your-email@example.com
    fi
done

# 检查进程是否运行
if ! pgrep -f "L_P.py" > /dev/null; then
    echo "套利机器人进程停止" | mail -s "进程告警" your-email@example.com
fi
```

---

## 附录

### A. 快速部署脚本
创建 `deploy.sh` 自动化脚本：

```bash
#!/bin/bash
# deploy.sh - 一键部署脚本

set -e  # 遇到错误立即退出

echo "=== Lighter和Paradex套利机器人部署脚本 ==="

# 1. 系统更新
echo "更新系统..."
sudo apt update && sudo apt upgrade -y

# 2. 安装Python
echo "安装Python环境..."
sudo apt install -y python3.9 python3.9-venv python3.9-dev

# 3. 创建项目目录
echo "创建项目目录..."
mkdir -p ~/projects/lighter-paradex
cd ~/projects/lighter-paradex

# 4. 创建虚拟环境
echo "创建虚拟环境..."
python3.9 -m venv venv
source venv/bin/activate

# 5. 安装依赖
echo "安装Python依赖..."
pip install --upgrade pip
pip install python-telegram-bot==20.7 aiohttp>=3.8.0 websockets>=12.0 python-dotenv>=1.0.0

# 6. 复制配置文件（假设文件已存在）
echo "设置配置文件..."
if [ -f ".env" ]; then
    echo ".env文件已存在"
else
    echo "请手动创建.env配置文件"
fi

echo "部署完成！"
echo "请手动运行: source venv/bin/activate && python L_P.py"
```

### B. 常用命令速查表

```bash
# 服务器连接
ssh username@server-ip              # 连接服务器
exit                                 # 断开连接

# 文件传输
scp file.txt user@server:~/          # 上传文件
scp user@server:~/file.txt .         # 下载文件

# 进程管理
ps aux | grep python                # 查看Python进程
kill -9 PID                         # 强制结束进程
pkill -f "L_P.py"                   # 按名称结束进程

# 日志管理
tail -f /var/log/arbitrage-bot.log  # 实时查看日志
journalctl -u arbitrage-bot -f      # 查看systemd日志
sudo supervisorctl tail arbitrage-bot # 查看supervisor日志

# 系统监控
htop                                # 实时系统监控
df -h                               # 磁盘使用情况
free -h                             # 内存使用情况
netstat -tulpn                      # 网络连接状态
```

### C. 联系支持

遇到问题可以：
1. **查看日志文件**：`/var/log/arbitrage-bot.log`
2. **检查系统状态**：`systemctl status arbitrage-bot`
3. **搜索错误信息**：在搜索引擎中搜索错误关键词
4. **查看官方文档**：相关交易所API文档
5. **社区支持**：相关技术社区和论坛

---

## 总结

通过本教程，您应该能够：

✅ **选择合适的云服务器**  
✅ **配置本地开发环境**  
✅ **安全上传脚本文件**  
✅ **配置云服务器环境**  
✅ **安装和运行套利机器人**  
✅ **设置后台运行和进程管理**  
✅ **配置监控和日志系统**  
✅ **处理常见故障问题**  
✅ **实施安全最佳实践**  

记住，套利交易存在风险，建议：
1. 先在小额资金下测试
2. 监控服务器性能和网络延迟
3. 定期备份配置和日志
4. 设置适当的风险控制参数
5. 保持软件和系统的更新

祝您部署顺利！如有问题，请参考故障排除章节或联系相关技术支持。