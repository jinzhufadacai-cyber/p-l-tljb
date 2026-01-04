# 安装故障排除指南

## 问题：安装卡在 torch 下载
安装过程中卡在下载 `torch`、`triton`、`nvidia-cuda-*` 等深度学习相关包，这些包非常大（总计超过 2GB），下载速度慢且可能不必要。

## 原因分析
`torch` 可能是以下某个包的**间接依赖**：
- `starknet-py` (Starknet Python SDK)
- `paradex-py` (Paradex Python SDK)
- 或其他包的 GPU 加速可选依赖

## 解决方案

### 方案1：分步安装（推荐）
在云服务器上按顺序执行以下命令：

```bash
# 1. 进入项目目录
cd /path/to/lighter-paradex-arbitrage

# 2. 安装基本依赖（不包含 torch）
pip install python-telegram-bot>=20.7 aiohttp>=3.8.0 websockets>=12.0 \
            asyncio>=3.4.3 python-dotenv>=1.0.0 requests>=2.31.0 \
            cryptography>=42.0.0

# 3. 安装轻量级依赖
pip install ccxt>=4.3.0 web3>=6.0.0

# 4. 尝试安装 lighter（应该不会引入 torch）
pip install lighter>=0.1.0

# 5. 尝试安装 starknet-py（可能是 torch 的来源）
# 先尝试不安装可选依赖
pip install starknet-py==0.21.0 --no-deps
# 然后手动安装其依赖（如果有必要）
pip install marshmallow>=3.20.0 dataclasses-json>=0.5.0 typing-extensions>=4.0.0

# 6. 安装 paradex-py（使用特定提交）
pip install git+https://github.com/tradeparadex/paradex-py.git@7eb7aa3825d466b2f14abd3e94f2ce6b002d6a63

# 7. 验证安装
python -c "import lighter; import paradex_py; import starknet_py; print('所有SDK导入成功')"
```

### 方案2：使用最小化 requirements 文件
使用项目中的 `requirements-minimal.txt`：

```bash
# 先安装注释掉的部分
pip install -r requirements-minimal.txt

# 然后逐个取消注释并安装 exchange SDKs
# 编辑 requirements-minimal.txt，取消注释 lighter，安装
pip install lighter>=0.1.0

# 取消注释 paradex-py，安装
pip install git+https://github.com/tradeparadex/paradex-py.git@7eb7aa3825d466b2f14abd3e94f2ce6b002d6a63

# 取消注释 web3，安装
pip install web3>=6.0.0

# 取消注释 starknet-py，安装（可能是 torch 来源）
pip install starknet-py>=0.21.0 --no-deps
```

### 方案3：如果确实需要 torch（CPU版本）
如果某个包确实需要 torch，安装 CPU 版本（较小）：

```bash
# 使用清华镜像源加速
pip install torch==2.7.0 --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 然后安装其他依赖
pip install -r requirements.txt
```

### 方案4：排查具体是哪个包引入了 torch
```bash
# 方法1：使用 pipdeptree 查看依赖树
pip install pipdeptree
pipdeptree | grep -i torch

# 方法2：使用 pip show 检查每个包
for pkg in python-telegram-bot aiohttp websockets asyncio python-dotenv requests cryptography ccxt web3 starknet-py lighter; do
    echo "=== $pkg ==="
    pip show $pkg | grep -i requires || echo "No requires info"
done
```

## 紧急解决方案
如果急需运行程序，可以尝试跳过某些功能：

1. **临时注释掉 paradex_real.py 中的 starknet_py 导入**（第121行）：
   ```python
   # from starknet_py.common import int_from_hex
   # 改为直接转换
   self.l2_private_key = int(self.l2_private_key_hex, 16)
   ```

2. **修改 test_real_exchanges.py** 跳过 starknet-py 测试。

## 验证安装成功
运行测试脚本：
```bash
python test_real_exchanges.py
```

如果显示 SDK 导入成功和环境变量检查通过，说明安装基本完成。

## 后续优化
1. 更新 requirements.txt 添加版本约束，避免自动安装 torch
2. 考虑是否真的需要 starknet-py 的全部功能
3. 提交问题到相关 SDK 仓库询问 torch 依赖的必要性

## 云服务器优化建议
1. 使用国内镜像源加速下载：
   ```bash
   pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
   ```

2. 如果下载仍然缓慢，可以考虑：
   - 使用代理
   - 先在本地下载好包，然后上传到服务器
   - 使用 Docker 镜像预先构建环境

## 🛡️ 安全安装方法（推荐）

为避免 `torch` 等大型深度学习包被意外安装，项目现在提供了安全安装选项：

### 方法1：使用 requirements-safe.txt（推荐）
```bash
# 安装所有依赖，使用 starknet-py==0.20.0 避免 torch
pip install -r requirements-safe.txt
```

### 方法2：使用约束文件排除 torch
```bash
# 使用 constraints.txt 明确排除 torch 和 CUDA 包
pip install -r requirements.txt -c constraints.txt
```

### 方法3：使用安全安装脚本
```bash
# 运行交互式安装脚本
bash install-safe.sh
```

### 方法4：分步安装（完全控制）
```bash
# 1. 基础依赖
pip install python-telegram-bot>=20.7 aiohttp>=3.8.0 websockets>=12.0 python-dotenv>=1.0.0 requests>=2.31.0 cryptography>=42.0.0

# 2. 区块链 SDK
pip install web3>=6.0.0 ccxt>=4.3.0 lighter>=0.1.0

# 3. Paradex SDK
pip install git+https://github.com/tradeparadex/paradex-py.git@7eb7aa3825d466b2f14abd3e94f2ce6b002d6a63

# 4. Starknet SDK（无依赖安装）
pip install starknet-py==0.20.0 --no-deps
pip install marshmallow>=3.20.0 dataclasses-json>=0.5.0 typing-extensions>=4.0.0
```

### 验证安装
```bash
# 检查是否安装了 torch
pip list | grep -i torch || echo "✅ torch 未安装"

# 验证核心 SDK
python -c "import lighter; import paradex_py; print('✅ 核心SDK导入成功')"
```

## 📁 新文件说明
- `requirements-safe.txt` - 安全的依赖配置（使用 starknet-py==0.20.0）
- `constraints.txt` - 排除 torch 和 CUDA 包的约束文件
- `install-safe.sh` - 交互式安全安装脚本
- `requirements-minimal.txt` - 最小化依赖文件（用于诊断）

## ⚠️ 重要提醒
1. **不要**直接运行 `pip install -r requirements.txt`（可能引入 torch）
2. 如果必须使用新版本 `starknet-py`，请先检查其依赖关系
3. 定期运行 `pip list | grep -i torch` 确保未安装 torch
4. 如果意外安装了 torch，使用 `pip uninstall torch torchvision torchaudio triton -y` 卸载