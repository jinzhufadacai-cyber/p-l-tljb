# Lighter-Paradex 套利机器人测试指南

## 📋 测试目的
验证环境变量加载修复是否有效，确保机器人在云服务器上能正常运行。

## 🔧 修复内容
已修复 `L_P.py` 文件：
1. 添加导入：`from dotenv import load_dotenv` (第39行)
2. 添加加载调用：`load_dotenv()` (第340行，main()函数内)

## 🚀 云服务器测试步骤

### 第1步：连接到云服务器
```bash
ssh jinzhufadacai@136.110.123.34
# 或使用 root 用户
sudo -i
```

### 第2步：进入项目目录
```bash
cd ~/lighter-paradex-arbitrage
```

### 第3步：检查项目文件
```bash
# 列出所有文件
ls -la

# 检查关键文件是否存在
ls -la L_P.py arbitrage.py requirements.txt .env.example
```

### 第4步：激活虚拟环境
```bash
# 如果使用虚拟环境
source venv/bin/activate

# 检查 Python 版本
python --version

# 检查依赖是否安装
pip list | grep -E "python-dotenv|telegram|aiohttp"
```

### 第5步：创建真实的 .env 文件
```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件，填入真实的 API 密钥
nano .env
# 或使用 vi
vi .env
```

### 第6步：验证 .env 文件内容
确保 `.env` 文件包含以下内容（使用您的真实密钥）：
```env
# Lighter 交易所配置
LIGHTER_API_KEY=您的真实_Lighter_API_密钥
LIGHTER_API_SECRET=您的账户索引,API密钥索引  # 例如: 0,0

# Paradex 交易所配置
PARADEX_API_KEY=您的真实_Paradex_API_密钥
PARADEX_API_SECRET=您的真实_Paradex_API_私钥

# Telegram 机器人配置（可选）
TELEGRAM_BOT_TOKEN=您的_Telegram_Bot_Token
TELEGRAM_CHAT_ID=您的_Chat_ID
```

### 第7步：测试环境变量加载
```bash
# 方法1：使用我们创建的测试脚本（如果已上传）
python test_env_loading.py

# 方法2：手动测试
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('LIGHTER_API_KEY:', '已设置' if os.getenv('LIGHTER_API_KEY') else '未设置')
print('PARADEX_API_KEY:', '已设置' if os.getenv('PARADEX_API_KEY') else '未设置')
"
```

### 第8步：运行修复后的主脚本
```bash
# 使用最小参数测试
python L_P.py --symbol BTC/USDT --size 0.001 --max-position 0.1
```

### 第9步：检查运行结果

**期望的正常输出：**
```
2026-01-02 23:03:14,260 - __main__ - INFO - 启动Lighter和Paradex套利机器人...
2026-01-02 23:03:14,261 - __main__ - INFO - 环境变量加载成功
2026-01-02 23:03:14,262 - __main__ - INFO - 正在连接交易所...
```

**如果仍有错误：**
1. **错误信息**：`缺少必要的环境变量`
   - 检查 `.env` 文件权限：`ls -la .env`
   - 检查文件格式：确保没有多余空格或引号
   - 重新加载环境变量：`source .env`（仅测试，不推荐）

2. **错误信息**：`ModuleNotFoundError: No module named 'dotenv'`
   - 安装依赖：`pip install python-dotenv`
   - 重新安装所有依赖：`pip install -r requirements.txt`

### 第10步：高级测试（可选）
```bash
# 测试 Telegram 机器人功能
python L_P.py --symbol BTC/USDT --size 0.001 --max-position 0.1 --telegram-token 您的Token

# 测试不同交易对
python L_P.py --symbol ETH/USDT --size 0.01 --max-position 1.0

# 启用调试模式（查看详细日志）
export LOG_LEVEL=DEBUG
python L_P.py --symbol BTC/USDT --size 0.001 --max-position 0.1
```

## 🔍 故障排除

### 问题1：`.env` 文件已存在但环境变量仍无法加载
**解决方案：**
```bash
# 检查 .env 文件编码
file .env

# 检查文件内容（不显示敏感信息）
head -n 5 .env

# 测试直接加载
python -c "
from dotenv import load_dotenv
import os
print('当前目录:', os.getcwd())
load_dotenv('.env')
print('LIGHTER_API_KEY 前5字符:', os.getenv('LIGHTER_API_KEY', '未设置')[:5] if os.getenv('LIGHTER_API_KEY') else '未设置')
"
```

### 问题2：权限问题
```bash
# 检查文件权限
ls -la .env

# 如果是 root 用户创建的，可能需要更改权限
chmod 644 .env  # 设置可读权限
chown jinzhufadacai:jinzhufadacai .env  # 更改所有者
```

### 问题3：虚拟环境问题
```bash
# 重新创建虚拟环境
deactivate  # 退出当前环境
cd ~/lighter-paradex-arbitrage
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📊 测试检查清单

- [ ] `.env` 文件已创建并包含正确的 API 密钥
- [ ] 文件权限正确（644 或 600）
- [ ] `python-dotenv` 已安装
- [ ] 虚拟环境已激活
- [ ] 脚本启动时不再显示 "缺少必要的环境变量"
- [ ] 日志显示 "环境变量加载成功" 或类似信息
- [ ] 交易所连接正常（如果 API 密钥正确）

## 🎯 成功标准
1. 脚本启动时**不报错** "缺少必要的环境变量"
2. 日志显示正常初始化信息
3. 机器人开始监控订单簿（即使没有实际交易）

## 📝 测试记录模板
```bash
# 测试时间
date

# 测试环境
python --version
pip show python-dotenv

# 执行测试
python L_P.py --symbol BTC/USDT --size 0.001 --max-position 0.1 2>&1 | head -20
```

## 🆘 如果仍然失败

如果按照以上步骤测试仍然失败，请提供以下信息：

1. **完整的错误信息**
2. **`.env` 文件的前几行**（隐藏敏感信息）
3. **执行的命令和输出**
4. **文件权限信息**：`ls -la L_P.py .env`
5. **Python 环境信息**：`python --version; pip list`

---

**测试完成后**，请告知我们结果：
- ✅ 修复成功，机器人正常运行
- ⚠️ 部分成功，仍有其他问题
- ❌ 修复无效，仍有相同错误

我们将根据测试结果提供进一步支持。