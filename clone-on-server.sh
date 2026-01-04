#!/bin/bash
# clone-on-server.sh
# 云服务器克隆Git仓库脚本

set -e  # 遇到错误立即退出

echo "=== 云服务器克隆脚本 ==="
echo "版本: 1.0"
echo ""

# 配置信息（请修改以下变量）
GITHUB_USER="您的GitHub用户名"
REPO_NAME="lighter-paradex-arbitrage"
TARGET_DIR="$HOME/projects/lighter-paradex"
USE_SUDO=false  # 是否使用sudo（如果需要在root目录下运行）

# 显示配置
echo "配置信息："
echo "  GitHub用户: $GITHUB_USER"
echo "  仓库名称: $REPO_NAME"
echo "  目标目录: $TARGET_DIR"
echo "  使用sudo: $USE_SUDO"
echo ""

# 确认继续
read -p "是否继续？(y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消"
    exit 0
fi

# 检查并安装Git
echo "检查Git安装状态..."
if ! command -v git &> /dev/null; then
    echo "Git未安装，正在安装..."
    
    # 检测操作系统
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        OS=$(uname -s)
    fi
    
    case $OS in
        ubuntu|debian|pop)
            sudo apt update
            sudo apt install git -y
            ;;
        centos|rhel|fedora)
            sudo yum install git -y
            ;;
        alpine)
            sudo apk add git
            ;;
        *)
            echo "❌ 不支持的操作系统: $OS"
            echo "请手动安装Git: https://git-scm.com/download/linux"
            exit 1
            ;;
    esac
    echo "✅ Git安装完成"
else
    git_version=$(git --version)
    echo "✅ $git_version"
fi

# 配置Git用户信息
echo ""
echo "配置Git用户信息..."
if [ -z "$(git config --global user.name)" ]; then
    git config --global user.name "云服务器"
    echo "✅ 设置用户名: 云服务器"
fi

if [ -z "$(git config --global user.email)" ]; then
    git config --global user.email "server@example.com"
    echo "✅ 设置邮箱: server@example.com"
fi

# 检查SSH密钥
echo ""
echo "检查SSH密钥..."
SSH_KEY_FILE="$HOME/.ssh/id_ed25519"
if [ ! -f "$SSH_KEY_FILE" ]; then
    echo "SSH密钥不存在，是否生成？"
    read -p "生成SSH密钥并添加到GitHub？(y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ssh-keygen -t ed25519 -C "server@example.com" -f "$SSH_KEY_FILE" -N ""
        echo "✅ SSH密钥已生成"
        echo ""
        echo "请将以下公钥添加到GitHub："
        echo "1. 访问 https://github.com/settings/keys"
        echo "2. 点击 'New SSH key'"
        echo "3. 粘贴以下内容："
        echo ""
        cat "${SSH_KEY_FILE}.pub"
        echo ""
        read -p "按回车键继续..." -r
    else
        echo "⚠️  使用HTTPS方式克隆（需要输入密码）"
    fi
else
    echo "✅ SSH密钥已存在"
fi

# 创建目标目录
echo ""
echo "创建目标目录..."
if [ "$USE_SUDO" = true ]; then
    sudo mkdir -p $(dirname "$TARGET_DIR")
    sudo mkdir -p "$TARGET_DIR"
else
    mkdir -p "$TARGET_DIR"
fi
echo "✅ 目录已创建: $TARGET_DIR"

# 克隆仓库
echo ""
echo "克隆仓库..."
REPO_URL="git@github.com:${GITHUB_USER}/${REPO_NAME}.git"

# 测试SSH连接
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH连接到GitHub成功"
    CLONE_CMD="git clone $REPO_URL $TARGET_DIR"
else
    echo "⚠️  SSH连接失败，使用HTTPS"
    REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
    CLONE_CMD="git clone $REPO_URL $TARGET_DIR"
fi

if [ "$USE_SUDO" = true ]; then
    sudo $CLONE_CMD
    sudo chown -R root:root "$TARGET_DIR"
else
    $CLONE_CMD
fi

if [ $? -eq 0 ]; then
    echo "✅ 仓库克隆成功"
else
    echo "❌ 仓库克隆失败"
    echo "尝试使用HTTPS方式..."
    REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
    if [ "$USE_SUDO" = true ]; then
        sudo git clone $REPO_URL $TARGET_DIR
        sudo chown -R root:root "$TARGET_DIR"
    else
        git clone $REPO_URL $TARGET_DIR
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ 克隆失败，请检查："
        echo "1. 仓库地址是否正确"
        echo "2. 仓库是否为私有（需要登录）"
        echo "3. 网络连接是否正常"
        exit 1
    fi
fi

# 设置文件权限
echo ""
echo "设置文件权限..."
if [ "$USE_SUDO" = true ]; then
    sudo chmod 600 "$TARGET_DIR/.env.example" 2>/dev/null || true
    sudo find "$TARGET_DIR" -name "*.py" -exec sudo chmod 755 {} \; 2>/dev/null || true
else
    chmod 600 "$TARGET_DIR/.env.example" 2>/dev/null || true
    find "$TARGET_DIR" -name "*.py" -exec chmod 755 {} \; 2>/dev/null || true
fi
echo "✅ 文件权限已设置"

# 显示克隆结果
echo ""
echo "=" * 50
echo "✅ 克隆完成！"
echo "=" * 50
echo ""
echo "仓库信息："
echo "  目录: $TARGET_DIR"
echo "  大小: $(du -sh "$TARGET_DIR" | cut -f1)"
echo "  文件数: $(find "$TARGET_DIR" -type f | wc -l)"
echo ""
echo "进入目录:"
echo "  cd $TARGET_DIR"
echo ""
echo "查看文件："
echo "  ls -la $TARGET_DIR"
echo ""
echo "下一步操作："
echo "1. 安装Python环境："
echo "   sudo apt install python3.9 python3.9-venv python3.9-dev -y"
echo ""
echo "2. 创建虚拟环境："
echo "   cd $TARGET_DIR"
echo "   python3.9 -m venv venv"
echo "   source venv/bin/activate"
echo ""
echo "3. 安装依赖："
echo "   pip install -r requirements.txt"
echo ""
echo "4. 创建环境变量文件："
echo "   cp .env.example .env"
echo "   vim .env  # 编辑文件，填入API密钥"
echo "   chmod 600 .env"
echo ""
echo "5. 运行机器人："
echo "   python L_P.py --symbol BTC/USDT --size 0.001"
echo ""
echo "详细步骤请参考 README.md 和 DEPLOYMENT_TUTORIAL.md"
echo ""