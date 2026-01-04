# setup-git-local.ps1
# Git本地仓库初始化脚本

Write-Host "=== Git仓库初始化脚本 ===" -ForegroundColor Green
Write-Host "版本: 1.0" -ForegroundColor Gray
Write-Host ""

# 检查Git是否安装
Write-Host "检查Git安装状态..." -ForegroundColor Cyan
try {
    $gitVersion = git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $gitVersion" -ForegroundColor Green
    } else {
        throw "Git未正确安装"
    }
} catch {
    Write-Host "❌ Git未安装或未在PATH中" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装Git：" -ForegroundColor Yellow
    Write-Host "1. 下载地址: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "2. 运行安装程序，全部使用默认选项" -ForegroundColor Yellow
    Write-Host "3. 安装完成后重新打开PowerShell" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "或者使用winget安装：" -ForegroundColor Yellow
    Write-Host "   winget install Git.Git" -ForegroundColor White
    Write-Host ""
    exit 1
}

# 检查当前目录
$currentDir = Get-Location
Write-Host "当前目录: $currentDir" -ForegroundColor Gray

# 确认用户信息
Write-Host ""
Write-Host "检查Git用户配置..." -ForegroundColor Cyan
$userName = git config --global user.name
$userEmail = git config --global user.email

if (-not $userName) {
    Write-Host "⚠️  Git用户名未配置" -ForegroundColor Yellow
    $userName = Read-Host "请输入您的姓名（用于Git提交）"
    git config --global user.name $userName
    Write-Host "✅ 用户名已设置: $userName" -ForegroundColor Green
} else {
    Write-Host "✅ 用户名: $userName" -ForegroundColor Green
}

if (-not $userEmail) {
    Write-Host "⚠️  Git邮箱未配置" -ForegroundColor Yellow
    $userEmail = Read-Host "请输入您的邮箱（用于Git提交）"
    git config --global user.email $userEmail
    Write-Host "✅ 邮箱已设置: $userEmail" -ForegroundColor Green
} else {
    Write-Host "✅ 邮箱: $userEmail" -ForegroundColor Green
}

# 检查是否已经是Git仓库
Write-Host ""
Write-Host "检查Git仓库状态..." -ForegroundColor Cyan
if (Test-Path ".git") {
    Write-Host "⚠️  当前目录已经是Git仓库" -ForegroundColor Yellow
    $choice = Read-Host "是否重新初始化？(y/n)"
    if ($choice -ne 'y') {
        Write-Host "操作已取消" -ForegroundColor Gray
        exit 0
    }
    # 备份现有.git目录
    $backupDir = ".git_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Move-Item -Path ".git" -Destination $backupDir -Force
    Write-Host "✅ 原.git目录已备份到: $backupDir" -ForegroundColor Green
}

# 初始化Git仓库
Write-Host ""
Write-Host "初始化Git仓库..." -ForegroundColor Cyan
git init
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git初始化失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Git仓库初始化成功" -ForegroundColor Green

# 检查.gitignore文件
Write-Host ""
Write-Host "检查.gitignore文件..." -ForegroundColor Cyan
if (-not (Test-Path ".gitignore")) {
    Write-Host "⚠️  .gitignore文件不存在，正在创建..." -ForegroundColor Yellow
    # 创建.gitignore文件
    @"
# Python
__pycache__/
*.py[cod]
*`$py.class
.Python
pycache/

# Virtual Environment
venv/
env/
ENV/

# Environment Variables (DO NOT COMMIT SECRETS!)
.env
*.key
*.pem
*.secret

# IDE
.vscode/
.idea/
*.swp
*.swo
*.sublime-project
*.sublime-workspace

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Build outputs
dist/
build/
*.egg-info/

# Temporary directories
lighter-paradex-arbitrage/
temp/
tmp/

# Project specific
*.db
*.sqlite3

# Backup files
*.bak
*.backup

# Certificate files
*.crt
*.cer
*.cert
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8
    Write-Host "✅ .gitignore文件已创建" -ForegroundColor Green
} else {
    Write-Host "✅ .gitignore文件已存在" -ForegroundColor Green
}

# 添加文件到暂存区
Write-Host ""
Write-Host "添加文件到暂存区..." -ForegroundColor Cyan

# 列出要添加的文件
$filesToAdd = @(
    "L_P.py",
    "arbitrage.py", 
    "telegram_control.py",
    "requirements.txt",
    ".env.example",
    "README.md",
    "DEPLOYMENT_TUTORIAL.md",
    "GIT_SETUP_GUIDE.md",
    "setup-git-local.ps1"
)

# 添加存在的文件
$addedFiles = @()
foreach ($file in $filesToAdd) {
    if (Test-Path $file) {
        git add $file
        if ($LASTEXITCODE -eq 0) {
            $addedFiles += $file
        }
    }
}

# 添加exchanges目录
if (Test-Path "exchanges") {
    git add exchanges/
    if ($LASTEXITCODE -eq 0) {
        $addedFiles += "exchanges/"
    }
}

# 添加.gitignore
git add .gitignore

Write-Host "✅ 已添加 $($addedFiles.Count) 个文件到暂存区" -ForegroundColor Green

# 显示暂存区状态
Write-Host ""
Write-Host "当前暂存区状态:" -ForegroundColor Cyan
git status --short

# 提交更改
Write-Host ""
Write-Host "提交更改到本地仓库..." -ForegroundColor Cyan
$commitMessage = "初始提交：Lighter和Paradex套利机器人"
git commit -m $commitMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 提交失败" -ForegroundColor Red
    Write-Host "尝试使用空提交..." -ForegroundColor Yellow
    git commit --allow-empty -m $commitMessage
}

Write-Host "✅ 提交成功: $commitMessage" -ForegroundColor Green

# 显示提交历史
Write-Host ""
Write-Host "提交历史:" -ForegroundColor Cyan
git log --oneline -5

# 完成提示
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "✅ 本地Git仓库初始化完成！" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 在GitHub/GitLab/Gitee上创建新仓库" -ForegroundColor White
Write-Host "2. 获取仓库的SSH或HTTPS地址" -ForegroundColor White
Write-Host "3. 运行以下命令连接远程仓库：" -ForegroundColor White
Write-Host ""
Write-Host "   # 添加远程仓库（替换为您的地址）" -ForegroundColor Gray
Write-Host "   git remote add origin git@github.com:您的用户名/lighter-paradex-arbitrage.git" -ForegroundColor Cyan
Write-Host ""
Write-Host "   # 或者使用HTTPS地址" -ForegroundColor Gray
Write-Host "   git remote add origin https://github.com/您的用户名/lighter-paradex-arbitrage.git" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. 重命名主分支并推送代码：" -ForegroundColor White
Write-Host ""
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. 如果需要强制推送（如果远程仓库有文件）：" -ForegroundColor White
Write-Host "   git push -u origin main --force" -ForegroundColor Cyan
Write-Host ""
Write-Host "有用的命令：" -ForegroundColor Yellow
Write-Host "   git status                 # 查看状态" -ForegroundColor Gray
Write-Host "   git log --oneline          # 查看提交历史" -ForegroundColor Gray
Write-Host "   git remote -v              # 查看远程仓库" -ForegroundColor Gray
Write-Host "   git branch -a              # 查看所有分支" -ForegroundColor Gray
Write-Host ""
Write-Host "文档：" -ForegroundColor Yellow
Write-Host "   详细步骤请参考 GIT_SETUP_GUIDE.md 文件" -ForegroundColor White
Write-Host ""