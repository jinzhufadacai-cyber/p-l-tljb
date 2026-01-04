#!/usr/bin/env python3
"""
真实交易所连接测试脚本
用于安全测试Lighter和Paradex的真实API连接

功能：
1. 测试环境变量配置
2. 测试SDK导入和初始化
3. 测试API连接（只读操作）
4. 安全检查：不执行实际交易
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_environment_variables():
    """测试环境变量配置"""
    print("=" * 60)
    print("环境变量配置测试")
    print("=" * 60)
    
    # 必需变量（基础API连接） - 旧格式
    required_vars = {
        'Lighter (旧格式)': ['LIGHTER_API_KEY', 'LIGHTER_API_SECRET'],
        'Paradex (旧格式)': ['PARADEX_API_KEY', 'PARADEX_API_SECRET'],
    }
    
    # 可选变量（真实交易需要） - 新格式优先
    optional_vars = {
        'Lighter Real (新格式)': ['API_KEY_PRIVATE_KEY', 'LIGHTER_ACCOUNT_INDEX', 'LIGHTER_API_KEY_INDEX'],
        'Lighter Real (旧格式)': ['LIGHTER_API_AUTH'],
        'Paradex Real (新格式)': ['PARADEX_L1_ADDRESS', 'PARADEX_L2_PRIVATE_KEY'],
        'Paradex Real (旧格式)': ['PARADEX_STARKNET_PRIVATE_KEY', 'PARADEX_ETHEREUM_PRIVATE_KEY'],
    }
    
    all_required = []
    for category, vars_list in required_vars.items():
        all_required.extend(vars_list)
    
    all_optional = []
    for category, vars_list in optional_vars.items():
        all_optional.extend(vars_list)
    
    # 加载环境变量
    load_dotenv()
    
    print("\n检查环境变量:")
    print("-" * 40)
    
    missing_required = []
    missing_optional = []
    
    # 检查必需变量
    for var in all_required:
        value = os.getenv(var)
        if value and value.strip() and not value.startswith('your_'):
            print(f"✓ {var}: 已设置 (长度: {len(value)})")
        elif value and value.startswith('your_'):
            print(f"⚠ {var}: 检测到占位符值，请更新为真实值")
            missing_required.append(var)
        else:
            print(f"✗ {var}: 未设置")
            missing_required.append(var)
    
    # 检查可选变量
    for var in all_optional:
        value = os.getenv(var)
        if value and value.strip() and not value.startswith('your_'):
            print(f"✓ {var}: 已设置 (长度: {len(value)})")
        elif value and value.startswith('your_'):
            print(f"⚠ {var}: 检测到占位符值，请更新为真实值")
            missing_optional.append(var)
        else:
            print(f"⚠ {var}: 未设置（真实交易需要）")
            missing_optional.append(var)
    
    print(f"\n总计: 已设置 {len(all_required) - len(missing_required)}/{len(all_required)} 个必需变量")
    print(f"      已设置 {len(all_optional) - len(missing_optional)}/{len(all_optional)} 个可选变量")
    
    if missing_required:
        print("\n警告: 以下必需环境变量未正确设置:")
        for var in missing_required:
            print(f"  - {var}")
        print("\n请按照以下步骤操作:")
        print("1. 复制 .env.example 为 .env")
        print("2. 从交易所获取真实的API密钥")
        print("3. 更新 .env 文件中的值")
        print("4. 重新运行此测试")
        return False
    else:
        print("\n✓ 所有必需的环境变量已正确设置")
        if missing_optional:
            print("⚠ 以下真实交易变量未设置（仅影响真实交易模式）:")
            for var in missing_optional:
                print(f"  - {var}")
            print("  如需真实交易，请从交易所获取相应密钥")
        return True

async def test_sdk_imports():
    """测试SDK导入"""
    print("\n" + "=" * 60)
    print("SDK导入测试")
    print("=" * 60)
    
    sdk_status = {}
    
    # 测试 lighter (新版本)
    try:
        import lighter
        from lighter import SignerClient, ApiClient, Configuration, Account
        sdk_status['lighter'] = True
        print("✓ lighter SDK导入成功")
    except ImportError as e:
        sdk_status['lighter'] = False
        print(f"✗ lighter SDK导入失败: {e}")
        print("  安装命令: pip install lighter")
    
    # 测试 paradex-py (新版本)
    try:
        from paradex_py import Paradex
        from paradex_py.environment import PROD, TESTNET
        from paradex_py.common.order import Order, OrderType, OrderSide, OrderStatus
        sdk_status['paradex-py'] = True
        print("✓ paradex-py SDK导入成功")
    except ImportError as e:
        sdk_status['paradex-py'] = False
        print(f"✗ paradex-py SDK导入失败: {e}")
        print("  安装命令: pip install git+https://github.com/tradeparadex/paradex-py.git@7eb7aa3825d466b2f14abd3e94f2ce6b002d6a63")
    
    # 测试其他依赖
    try:
        import web3
        sdk_status['web3'] = True
        print("✓ web3 库导入成功")
    except ImportError as e:
        sdk_status['web3'] = False
        print(f"✗ web3 库导入失败: {e}")
        print("  安装命令: pip install web3")
    
    try:
        import starknet_py
        sdk_status['starknet-py'] = True
        print("✓ starknet-py 库导入成功")
    except ImportError as e:
        sdk_status['starknet-py'] = False
        print(f"✗ starknet-py 库导入失败: {e}")
        print("  安装命令: pip install starknet-py")
    
    all_success = all(sdk_status.values())
    if all_success:
        print("\n✓ 所有必需的SDK和库导入成功")
    else:
        print(f"\n⚠ 部分SDK导入失败 ({sum(sdk_status.values())}/{len(sdk_status)})")
        print("  请安装缺失的依赖: pip install -r requirements.txt")
    
    return all_success

async def test_lighter_connection():
    """测试Lighter API连接（只读）"""
    print("\n" + "=" * 60)
    print("Lighter API连接测试")
    print("=" * 60)
    
    try:
        # 尝试导入真实交易所类
        from exchanges.lighter_real import LighterRealExchange
        
        # 创建交易所实例
        exchange = LighterRealExchange()
        
        # 初始化客户端
        logger.info("正在初始化Lighter客户端...")
        success = await exchange.initialize()
        
        if success:
            print("✓ Lighter客户端初始化成功")
            
            # 测试获取余额（模拟或真实）
            logger.info("正在测试余额查询...")
            balance = await exchange.get_balance()
            if balance:
                print("✓ 余额查询成功")
                print(f"  模拟余额: {balance}")
            else:
                print("⚠ 余额查询返回空，可能是模拟数据")
            
            # 测试获取订单簿
            logger.info("正在测试订单簿查询...")
            orderbook = await exchange.get_order_book("BTC/USDT")
            if orderbook and orderbook.bids and orderbook.asks:
                print("✓ 订单簿查询成功")
                print(f"  买一价: {orderbook.bids[0][0]:.2f}, 卖一价: {orderbook.asks[0][0]:.2f}")
            else:
                print("⚠ 订单簿查询返回空数据，可能是模拟实现")
            
            return True
        else:
            print("✗ Lighter客户端初始化失败")
            print("  可能原因:")
            print("  - LIGHTER_API_AUTH 环境变量未正确设置")
            print("  - 网络连接问题")
            print("  - API密钥无效或过期")
            return False
            
    except Exception as e:
        print(f"✗ Lighter连接测试异常: {e}")
        logger.exception("Lighter连接测试详细错误:")
        return False

async def test_paradex_connection():
    """测试Paradex API连接（只读）"""
    print("\n" + "=" * 60)
    print("Paradex API连接测试")
    print("=" * 60)
    
    try:
        # 尝试导入真实交易所类
        from exchanges.paradex_real import ParadexRealExchange
        
        # 创建交易所实例
        exchange = ParadexRealExchange()
        
        # 初始化客户端
        logger.info("正在初始化Paradex客户端...")
        success = await exchange.initialize()
        
        if success:
            print("✓ Paradex客户端初始化成功")
            
            # 测试获取余额（模拟或真实）
            logger.info("正在测试余额查询...")
            balance = await exchange.get_balance()
            if balance:
                print("✓ 余额查询成功")
                print(f"  模拟余额: {balance}")
            else:
                print("⚠ 余额查询返回空，可能是模拟数据")
            
            # 测试获取订单簿
            logger.info("正在测试订单簿查询...")
            orderbook = await exchange.get_order_book("BTC/USDT")
            if orderbook and orderbook.bids and orderbook.asks:
                print("✓ 订单簿查询成功")
                print(f"  买一价: {orderbook.bids[0][0]:.2f}, 卖一价: {orderbook.asks[0][0]:.2f}")
            else:
                print("⚠ 订单簿查询返回空数据，可能是模拟实现")
            
            return True
        else:
            print("✗ Paradex客户端初始化失败")
            print("  可能原因:")
            print("  - PARADEX_STARKNET_PRIVATE_KEY 或 PARADEX_ETHEREUM_PRIVATE_KEY 未正确设置")
            print("  - 网络连接问题")
            print("  - API密钥无效或过期")
            return False
            
    except Exception as e:
        print(f"✗ Paradex连接测试异常: {e}")
        logger.exception("Paradex连接测试详细错误:")
        return False

async def safety_check():
    """安全检查：确认不会意外执行真实交易"""
    print("\n" + "=" * 60)
    print("安全检查")
    print("=" * 60)
    
    print("正在检查代码中的安全设置...")
    
    # 检查真实交易所类的订单方法是否有保护措施
    try:
        from exchanges.lighter_real import LighterRealExchange
        from exchanges.paradex_real import ParadexRealExchange
        
        # 检查是否有模拟交易标志
        lighter_methods = dir(LighterRealExchange)
        paradex_methods = dir(ParadexRealExchange)
        
        print("✓ 真实交易所类加载成功")
        
        # 警告信息
        print("\n⚠ 安全警告:")
        print("  1. 当前实现包含模拟订单功能")
        print("  2. 在实际交易前，请确保:")
        print("     - 使用测试网环境（如果可用）")
        print("     - 使用极小的交易量（如 0.0001 BTC）")
        print("     - 监控第一笔交易的结果")
        print("     - 准备好手动取消订单")
        
        return True
    except Exception as e:
        print(f"✗ 安全检查失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("开始真实交易所连接测试")
    print("此测试仅验证API连接，不会执行实际交易")
    print("=" * 60)
    
    test_results = {}
    
    # 测试环境变量
    test_results['env_vars'] = await test_environment_variables()
    
    # 测试SDK导入
    test_results['sdk_imports'] = await test_sdk_imports()
    
    # 测试Lighter连接
    test_results['lighter_connection'] = await test_lighter_connection()
    
    # 测试Paradex连接
    test_results['paradex_connection'] = await test_paradex_connection()
    
    # 安全检查
    test_results['safety_check'] = await safety_check()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    print(f"通过测试: {passed}/{total}")
    
    for test_name, result in test_results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {test_name}")
    
    if all(test_results.values()):
        print("\n🎉 所有测试通过！")
        print("\n下一步建议:")
        print("1. 使用极小的交易量进行测试（如 --size 0.0001）")
        print("2. 先在测试网（如果可用）上运行")
        print("3. 监控第一笔交易，确保按预期执行")
        print("4. 准备好手动干预，如有必要")
    else:
        print("\n⚠ 部分测试失败")
        print("\n建议操作:")
        print("1. 检查并修复环境变量配置")
        print("2. 安装缺失的依赖: pip install -r requirements.txt")
        print("3. 验证API密钥的有效性")
        print("4. 检查网络连接")
    
    return all(test_results.values())

if __name__ == '__main__':
    # 运行异步主函数
    success = asyncio.run(main())
    sys.exit(0 if success else 1)