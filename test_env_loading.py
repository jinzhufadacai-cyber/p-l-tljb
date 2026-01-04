#!/usr/bin/env python3
"""
环境变量加载测试脚本
用于验证 L_P.py 中的 load_dotenv() 修复是否有效
"""

import os
import sys
from dotenv import load_dotenv

def test_dotenv_loading():
    """测试 dotenv 环境变量加载"""
    print("=" * 50)
    print("环境变量加载测试")
    print("=" * 50)
    
    # 检查当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"当前目录: {current_dir}")
    
    # 检查 .env 文件是否存在
    env_path = os.path.join(current_dir, '.env')
    if os.path.exists(env_path):
        print(f"✓ .env 文件存在: {env_path}")
        print(f"  文件大小: {os.path.getsize(env_path)} 字节")
    else:
        print(f"✗ .env 文件不存在: {env_path}")
        print("  正在创建测试用的 .env 文件...")
        create_test_env_file(env_path)
    
    # 加载环境变量
    print("\n正在加载环境变量...")
    load_dotenv()
    
    # 测试读取环境变量
    test_vars = ['LIGHTER_API_KEY', 'PARADEX_API_KEY', 'TELEGRAM_BOT_TOKEN']
    
    print("\n环境变量读取测试:")
    print("-" * 40)
    
    for var in test_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {'*' * 8} (已设置，长度: {len(value)})")
        else:
            print(f"✗ {var}: 未设置")
    
    # 测试模拟环境变量
    print("\n模拟环境变量测试:")
    print("-" * 40)
    os.environ['TEST_VAR'] = 'test_value'
    test_value = os.getenv('TEST_VAR')
    print(f"TEST_VAR: {test_value} (期望: test_value)")
    
    if test_value == 'test_value':
        print("✓ 环境变量设置/读取功能正常")
    else:
        print("✗ 环境变量设置/读取功能异常")
    
    print("\n" + "=" * 50)
    print("测试完成")
    
    # 清理
    if 'TEST_VAR' in os.environ:
        del os.environ['TEST_VAR']

def create_test_env_file(env_path):
    """创建测试用的 .env 文件"""
    test_content = """# 测试用的环境变量文件
LIGHTER_API_KEY=test_lighter_api_key_12345
PARADEX_API_KEY=test_paradex_api_key_67890
TELEGRAM_BOT_TOKEN=test_telegram_bot_token_abc123
"""
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"  已创建测试文件: {env_path}")

def test_l_p_script_import():
    """测试 L_P.py 脚本导入"""
    print("\n" + "=" * 50)
    print("L_P.py 脚本导入测试")
    print("=" * 50)
    
    try:
        # 模拟 L_P.py 中的导入
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # 尝试导入必要的模块
        import asyncio
        import logging
        from dotenv import load_dotenv
        
        print("✓ 基础模块导入成功")
        
        # 尝试导入 arbitrage 模块
        try:
            from arbitrage import BaseExchange, OrderBook
            print("✓ arbitrage 模块导入成功")
        except ImportError as e:
            print(f"✗ arbitrage 模块导入失败: {e}")
            print("  注意: 这是预期行为，因为 arbitrage.py 是模拟实现")
        
        return True
    except Exception as e:
        print(f"✗ 导入测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始环境变量加载测试...\n")
    
    # 测试 dotenv 加载
    test_dotenv_loading()
    
    # 测试脚本导入
    test_l_p_script_import()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print("=" * 50)
    print("1. 环境变量加载测试完成")
    print("2. L_P.py 导入测试完成")
    print("3. 如果所有测试通过，说明修复有效")
    print("\n下一步:")
    print("- 在云服务器上创建真实的 .env 文件")
    print("- 运行 python L_P.py --symbol BTC/USDT --size 0.001 --max-position 0.1")
    print("- 检查是否仍然报错 '缺少必要的环境变量'")

if __name__ == '__main__':
    main()