# Git仓库设置与云服务器克隆指南

## 🎯 目标
将本地套利机器人代码上传到Git仓库，然后在云服务器上克隆使用。

## 📋 目录
1. [安装Git（如果未安装）](#1-安装git如果未安装)
2. [配置Git用户信息](#2-配置git用户信息)
3. [初始化本地Git仓库](#3-初始化本地git仓库)
4. [添加文件并提交](#4-添加文件并提交)
5. [创建远程Git仓库](#5-创建远程git仓库)
6. [推送代码到远程仓库](#6-推送代码到远程仓库)
7. [在云服务器上克隆仓库](#7-在云服务器上克隆仓库)
8. [一键脚本](#8-一键脚本)

---

## 1. 安装Git（如果未安装）

### Windows系统
```bash
# 方法1：使用winget（Windows 10/11）
winget install Git.Git

# 方法2：下载安装包
# 访问：https://git-scm.com/download/win
# 下载并运行安装程序，全部使用默认选项

# 方法3：使用Chocolatey（如果已安装）
choco install git
```

### 验证安装
```bash
# 打开新的PowerShell或Git Bash
git --version
# 应该显示类似：git version 2.42.0.windows.2
```

---

## 2. 配置Git用户信息

```bash
# 配置全局用户名和邮箱
git config --global user.name "您的姓名"
git config --global user.email "您的邮箱@example.com"

# 查看配置
git config --list

# 可选：配置默认编辑器（推荐VSCode）
git config --global core.editor "code --wait"
```

---

## 3. 初始化本地Git仓库

打开PowerShell或Git Bash，进入项目目录：

### 不同环境的路径格式：

| 环境 | 路径格式 | 示例 |
|------|----------|------|
| **PowerShell (Windows)** | Windows标准路径 | `cd C:\Users\Jinzhu\Documents\trae_projects\1` |
| **Git Bash (MINGW64)** | Unix风格路径 | `cd /c/Users/Jinzhu/Documents/trae_projects/1` |
| **Linux/macOS终端** | Unix路径 | `cd ~/Documents/trae_projects/1` |

```bash
# 根据您的环境选择正确的路径格式

# 对于PowerShell用户：
# cd C:\Users\Jinzhu\Documents\trae_projects\1

# 对于Git Bash用户：
cd /c/Users/Jinzhu/Documents/trae_projects/1

# 初始化Git仓库
git init

# 查看状态（应该显示未跟踪的文件）
git status
```

---

## 4. 添加文件并提交

### 4.1 创建.gitignore文件（已创建）
已为您创建了`.gitignore`文件，包含以下排除规则：
- Python缓存文件
- 虚拟环境
- 环境变量文件（.env）
- 日志文件
- IDE配置文件
- 临时目录

### 4.2 添加文件到暂存区
```bash
# 添加所有文件（除.gitignore中排除的）
git add .

# 或者选择性添加
git add L_P.py arbitrage.py telegram_control.py requirements.txt .env.example README.md DEPLOYMENT_TUTORIAL.md

# 添加exchanges目录
git add exchanges/

# 查看已添加的文件
git status
```

### 4.3 提交更改
```bash
# 提交到本地仓库
git commit -m "初始提交：Lighter和Paradex套利机器人"

# 查看提交历史
git log --oneline
```

---

## 5. 创建远程Git仓库

### 5.1 选择Git服务商
- **GitHub**：https://github.com（全球最流行）
- **GitLab**：https://gitlab.com（企业级功能）
- **Gitee**：https://gitee.com（国内访问快）

### 5.2 GitHub创建步骤
1. **登录/注册** GitHub账户
2. **点击右上角 "+" → "New repository"**
3. **填写仓库信息**：
   - Repository name: `lighter-paradex-arbitrage`
   - Description: `Lighter和Paradex对冲套利机器人`
   - Visibility: `Public`（公开）或 `Private`（私有）
   - **不要勾选** "Initialize this repository with a README"
4. **点击 "Create repository"**
5. **复制仓库地址**：
   - SSH地址: `git@github.com:您的用户名/lighter-paradex-arbitrage.git`
   - HTTPS地址: `https://github.com/您的用户名/lighter-paradex-arbitrage.git`

### 5.3 配置SSH密钥（推荐）
```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "您的邮箱@example.com"

# 一路按回车使用默认设置
# 查看公钥内容
cat ~/.ssh/id_ed25519.pub

# 将公钥添加到GitHub：
# 1. 登录GitHub → Settings → SSH and GPG keys
# 2. 点击 "New SSH key"
# 3. 粘贴公钥内容
# 4. 点击 "Add SSH key"
```

---

## 6. 推送代码到远程仓库

### 6.1 添加远程仓库地址
```bash
# 使用SSH地址（推荐）
git remote add origin git@github.com:您的用户名/lighter-paradex-arbitrage.git

# 或者使用HTTPS地址
git remote add origin https://github.com/您的用户名/lighter-paradex-arbitrage.git

# 查看远程仓库
git remote -v
```

### 6.2 推送代码
```bash
# 重命名主分支（如果需要）
git branch -M main

# 首次推送
git push -u origin main

# 如果遇到错误，可能是因为远程仓库有文件
# 使用强制推送（谨慎使用）
git push -u origin main --force

# 后续推送
git push
```

### 6.3 验证推送成功
1. 刷新GitHub仓库页面
2. 应该能看到所有文件
3. 检查提交历史

---

## 7. 在云服务器上克隆仓库

### 7.1 连接到云服务器
```bash
# 使用SSH连接
ssh jinzhufadacai@136.110.123.34

# 如果需要root权限
sudo su -
```

### 7.2 安装Git（如果服务器未安装）
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install git -y

# CentOS/RHEL
sudo yum install git -y

# 验证安装
git --version
```

### 7.3 配置服务器Git用户信息
```bash
# 配置全局用户信息
git config --global user.name "云服务器"
git config --global user.email "server@example.com"
```

### 7.4 克隆仓库
#### 方法1：使用SSH克隆（推荐）
```bash
# 在服务器上生成SSH密钥并添加到GitHub
ssh-keygen -t ed25519 -C "server@example.com"
cat ~/.ssh/id_ed25519.pub
# 将公钥添加到GitHub账户的SSH keys中

# 克隆仓库
cd ~
git clone git@github.com:您的用户名/lighter-paradex-arbitrage.git

# 进入项目目录
cd lighter-paradex-arbitrage
```

#### 方法2：使用HTTPS克隆（需要密码）
```bash
# 克隆仓库
cd ~
git clone https://github.com/您的用户名/lighter-paradex-arbitrage.git

# 如果仓库是私有的，需要输入用户名和密码
# 或者使用个人访问令牌（PAT）
```

#### 方法3：使用sudo克隆到特定目录
```bash
# 如果需要在root目录下运行
sudo git clone git@github.com:您的用户名/lighter-paradex-arbitrage.git /root/projects/lighter-paradex

# 设置权限
sudo chown -R root:root /root/projects/lighter-paradex
```

### 7.5 配置Python环境
```bash
# 进入项目目录
cd lighter-paradex-arbitrage

# 安装Python 3.9
sudo apt install python3.9 python3.9-venv python3.9-dev -y

# 创建虚拟环境
python3.9 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建环境变量文件
cp .env.example .env
# 编辑.env文件，填入真实的API密钥
vim .env
# 设置权限
chmod 600 .env
```

### 7.6 运行套利机器人
```bash
# 测试运行
python L_P.py --help

# 带参数运行
python L_P.py --symbol BTC/USDT --size 0.001 --max-position 0.1

# 使用Telegram控制
python L_P.py --symbol BTC/USDT --size 0.001 --telegram-token YOUR_BOT_TOKEN --telegram-chat-id YOUR_CHAT_ID
```

### 7.7 设置系统服务（可选）
```bash
# 创建systemd服务文件
sudo vim /etc/systemd/system/arbitrage-bot.service

# 内容参考DEPLOYMENT_TUTORIAL.md第6.3节

# 启动服务
sudo systemctl start arbitrage-bot
sudo systemctl enable arbitrage-bot
```

---

## 8. 一键脚本

### 8.1 本地初始化脚本 `setup-git-local.ps1`
```powershell
# setup-git-local.ps1
Write-Host "=== Git仓库初始化脚本 ===" -ForegroundColor Green

# 检查Git是否安装
try {
    git --version | Out-Null
    Write-Host "✅ Git已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ Git未安装，请先安装Git" -ForegroundColor Red
    Write-Host "下载地址: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# 进入项目目录
Set-Location "C:\Users\Jinzhu\Documents\trae_projects\1"

# 初始化仓库
Write-Host "初始化Git仓库..." -ForegroundColor Cyan
git init

# 添加文件
Write-Host "添加文件到暂存区..." -ForegroundColor Cyan
git add .

# 提交
Write-Host "提交更改..." -ForegroundColor Cyan
git commit -m "初始提交：Lighter和Paradex套利机器人"

Write-Host "✅ 本地仓库初始化完成！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 在GitHub上创建新仓库" -ForegroundColor Yellow
Write-Host "2. 运行: git remote add origin git@github.com:用户名/仓库名.git" -ForegroundColor Yellow
Write-Host "3. 运行: git branch -M main" -ForegroundColor Yellow
Write-Host "4. 运行: git push -u origin main" -ForegroundColor Yellow
```

### 8.2 服务器克隆脚本 `clone-on-server.sh`
```bash
#!/bin/bash
# clone-on-server.sh

echo "=== 云服务器克隆脚本 ==="

# 配置信息
GITHUB_USER="您的用户名"
REPO_NAME="lighter-paradex-arbitrage"
TARGET_DIR="~/projects/lighter-paradex"

# 安装Git
echo "安装Git..."
sudo apt update
sudo apt install git -y

# 配置Git
echo "配置Git用户信息..."
git config --global user.name "云服务器"
git config --global user.email "server@example.com"

# 克隆仓库
echo "克隆仓库..."
git clone git@github.com:${GITHUB_USER}/${REPO_NAME}.git ${TARGET_DIR}

# 设置权限
echo "设置文件权限..."
chmod 600 ${TARGET_DIR}/.env.example

echo "✅ 克隆完成！"
echo "目录: ${TARGET_DIR}"
echo "进入目录: cd ${TARGET_DIR}"
```

### 8.3 服务器环境配置脚本 `setup-server-env.sh`
```bash
#!/bin/bash
# setup-server-env.sh

echo "=== 服务器环境配置脚本 ==="

PROJECT_DIR="~/projects/lighter-paradex"

cd ${PROJECT_DIR}

# 安装Python
echo "安装Python 3.9..."
sudo apt install python3.9 python3.9-venv python3.9-dev -y

# 创建虚拟环境
echo "创建虚拟环境..."
python3.9 -m venv venv

# 激活环境并安装依赖
echo "安装Python依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 创建环境变量文件
echo "创建环境变量文件..."
cp .env.example .env
chmod 600 .env

echo "✅ 环境配置完成！"
echo "请编辑.env文件: vim .env"
echo "运行机器人: source venv/bin/activate && python L_P.py --help"
```

---

## 🔄 后续开发工作流程

### 本地开发 → 推送 → 服务器更新

```bash
# 1. 本地开发
# 修改代码...

# 2. 提交更改
git add .
git commit -m "更新功能：xxxx"

# 3. 推送到GitHub
git push

# 4. 在服务器上更新
ssh jinzhufadacai@136.110.123.34
cd ~/projects/lighter-paradex
git pull origin main

# 5. 重启服务（如果使用systemd）
sudo systemctl restart arbitrage-bot
```

### 自动更新脚本 `auto-update.sh`
```bash
#!/bin/bash
# auto-update.sh - 自动更新脚本

PROJECT_DIR="~/projects/lighter-paradex"

cd ${PROJECT_DIR}

# 拉取最新代码
git fetch origin
git pull origin main

# 安装新依赖（如果有）
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl restart arbitrage-bot

echo "✅ 更新完成：$(date)"
```

---

## ⚠️ 注意事项

### 安全注意事项
1. **不要提交敏感信息**：确保.env文件在.gitignore中
2. **使用SSH密钥**：避免在服务器上使用HTTPS密码
3. **定期更新**：保持Git和Python依赖更新
4. **备份仓库**：定期备份本地和远程仓库

### 常见问题
1. **推送被拒绝**：
   ```bash
   git pull origin main --rebase
   git push origin main
   ```

2. **SSH连接失败**：
   ```bash
   ssh -T git@github.com  # 测试连接
   ssh-keygen -t ed25519 -C "email"  # 重新生成密钥
   ```

3. **权限问题**：
   ```bash
   sudo chown -R $USER:$USER ~/projects/lighter-paradex
   ```

4. **Python版本问题**：
   ```bash
   # 指定Python版本
   python3.9 -m venv venv
   ```

---

## 📞 技术支持

遇到问题：
1. **查看Git文档**：`git help <command>`
2. **搜索错误信息**：在GitHub Issues或Stack Overflow搜索
3. **查看日志**：`git log --oneline --graph --all`
4. **撤销操作**：
   ```bash
   git reset --soft HEAD~1  # 撤销提交但保留更改
   git reset --hard HEAD~1  # 彻底撤销提交
   ```

---

## 🎉 完成状态检查

✅ **本地完成**：
- [ ] Git已安装
- [ ] 用户信息已配置
- [ ] 本地仓库已初始化
- [ ] 文件已提交
- [ ] 远程仓库已创建
- [ ] 代码已推送

✅ **服务器完成**：
- [ ] Git已安装
- [ ] 仓库已克隆
- [ ] Python环境已配置
- [ ] 依赖已安装
- [ ] 环境变量已设置
- [ ] 机器人可运行

现在您可以通过Git高效地管理代码，并在云服务器上轻松部署和更新套利机器人了！