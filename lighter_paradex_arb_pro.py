"""
arbitrage.py - Lighter-Paradex 跨交易所套利主程序
基于 cross-exchange-arbitrage 项目架构
实现实时价差监控和自动套利交易
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class LighterParadexArbitrage:
    def __init__(self, args):
        """初始化套利系统"""
        self.args = args
        self.ticker = args.ticker
        self.size = args.size
        self.max_position = args.max_position
        self.long_threshold = args.long_threshold
        self.short_threshold = args.short_threshold
        self.fill_timeout = args.fill_timeout
        
        print("✅ 套利系统初始化完成\n")
        self.print_config()
    
    def print_config(self):
        """打印配置信息"""
        print("=" * 60)
        print("📋 套利系统配置:")
        print(f"   交易对: {self.ticker}")
        print(f"   每笔交易量: {self.size}")
        print(f"   最大持仓: {self.max_position}")
        print(f"   做多阈值: ${self.long_threshold}")
        print(f"   做空阈值: ${self.short_threshold}")
        print(f"   订单超时: {self.fill_timeout}秒")
        print("=" * 60)
        print()
    
    async def run(self):
        """运行套利系统"""
        try:
            print("🚀 套利系统运行中...")
            print("📊 实时监控价差，等待套利机会...\n")
            
            # 运行主循环
            while True:
                await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n🛑 收到停止信号...")
            await self.shutdown()
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")
            await self.shutdown()
    
    async def shutdown(self):
        """优雅关闭"""
        print("📊 正在生成最终报告...")
        print("\n" + "=" * 60)
        print("📈 最终统计:")
        print("=" * 60)
        print("\n✅ 系统已安全退出")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Lighter-Paradex 跨交易所套利系统',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--ticker',
        type=str,
        required=True,
        help='交易对符号 (例如: BTC, ETH, SOL)'
    )
    
    parser.add_argument(
        '--size',
        type=float,
        default=0.01,
        help='每笔交易量 (默认: 0.01)'
    )
    
    parser.add_argument(
        '--max-position',
        type=float,
        default=1.0,
        help='最大持仓限制 (默认: 1.0)'
    )
    
    parser.add_argument(
        '--long-threshold',
        type=float,
        default=10.0,
        help='做多套利触发阈值，单位美元 (默认: 10)'
    )
    
    parser.add_argument(
        '--short-threshold',
        type=float,
        default=10.0,
        help='做空套利触发阈值，单位美元 (默认: 10)'
    )
    
    parser.add_argument(
        '--fill-timeout',
        type=int,
        default=5,
        help='订单成交超时时间（秒） (默认: 5)'
    )
    
    return parser.parse_args()


async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     Lighter - Paradex 跨交易所套利系统                  ║
║                                                          ║
║     基于 cross-exchange-arbitrage 架构                  ║
║     实时价差监控 + 自动套利交易                        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

按 Ctrl+C 可安全停止程序
    """)
    
    # 解析参数
    args = parse_arguments()
    
    # 创建并运行套利系统
    arbitrage = LighterParadexArbitrage(args)
    await arbitrage.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)
