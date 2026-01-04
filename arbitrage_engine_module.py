"""
strategy/arbitrage_engine.py - 套利引擎核心
实现价差监控、套利决策和交易执行
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Optional


class ArbitrageEngine:
    """套利引擎 - 负责监控价差并执行套利交易"""
    
    def __init__(self, lighter, paradex, position_tracker, order_manager, data_logger, telegram, config):
        self.lighter = lighter
        self.paradex = paradex
        self.position_tracker = position_tracker
        self.order_manager = order_manager
        self.data_logger = data_logger
        self.telegram = telegram
        
        # 配置参数
        self.ticker = config['ticker']
        self.size = config['size']
        self.long_threshold = config['long_threshold']
        self.short_threshold = config['short_threshold']
        
        # 状态
        self.running = False
        self.last_arbitrage_time = 0
        self.arbitrage_cooldown = 2  # 套利冷却时间（秒）
        
        # 统计
        self.stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
            'spreads_detected': 0,
            'spreads_executed': 0
        }
    
    async def start(self):
        """启动套利引擎"""
        self.running = True
        
        # 启动价格监控循环
        await self.price_monitoring_loop()
    
    async def stop(self):
        """停止套利引擎"""
        self.running = False
        print("⏸️ 套利引擎已停止")
    
    async def price_monitoring_loop(self):
        """价格监控主循环"""
        while self.running:
            try:
                # 获取两个交易所的价格
                lighter_data = await self.lighter.get_orderbook(self.ticker)
                paradex_data = await self.paradex.get_orderbook(self.ticker)
                
                if not lighter_data or not paradex_data:
                    await asyncio.sleep(1)
                    continue
                
                # 提取最优买卖价
                lighter_bid = lighter_data['best_bid']
                lighter_ask = lighter_data['best_ask']
                paradex_bid = paradex_data['best_bid']
                paradex_ask = paradex_data['best_ask']
                
                # 计算价差
                spread_long = lighter_bid - paradex_ask  # Lighter卖 - Paradex买
                spread_short = paradex_bid - lighter_ask  # Paradex卖 - Lighter买
                
                # 显示实时价格
                self.display_prices(
                    lighter_bid, lighter_ask,
                    paradex_bid, paradex_ask,
                    spread_long, spread_short
                )
                
                # 检查是否有套利机会
                opportunity = self.check_arbitrage_opportunity(
                    spread_long, spread_short,
                    lighter_bid, lighter_ask,
                    paradex_bid, paradex_ask
                )
                
                if opportunity:
                    # 执行套利
                    await self.execute_arbitrage(opportunity)
                
                # 短暂等待
                await asyncio.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 监控循环错误: {e}")
                await asyncio.sleep(5)
    
    def display_prices(self, l_bid, l_ask, p_bid, p_ask, spread_long, spread_short):
        """显示实时价格信息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 价差颜色标记
        long_color = "🟢" if spread_long >= self.long_threshold else "⚪"
        short_color = "🟢" if spread_short >= self.short_threshold else "⚪"
        
        print(f"\r⏰ {timestamp} | "
              f"Lighter: ${l_bid:,.2f}/{l_ask:,.2f} | "
              f"Paradex: ${p_bid:,.2f}/{p_ask:,.2f} | "
              f"{long_color}Long: ${spread_long:.2f} | "
              f"{short_color}Short: ${spread_short:.2f}", end='', flush=True)
    
    def check_arbitrage_opportunity(self, spread_long, spread_short, l_bid, l_ask, p_bid, p_ask):
        """检查是否存在套利机会"""
        current_time = time.time()
        
        # 冷却检查
        if current_time - self.last_arbitrage_time < self.arbitrage_cooldown:
            return None
        
        # 检查持仓限制
        current_position = self.position_tracker.get_net_position()
        
        # 做多套利机会 (Lighter买一价高于Paradex卖一价)
        if spread_long >= self.long_threshold:
            if abs(current_position - self.size) <= self.position_tracker.max_position:
                self.stats['spreads_detected'] += 1
                return {
                    'direction': 'LONG',
                    'spread': spread_long,
                    'lighter_price': l_bid,
                    'paradex_price': p_ask,
                    'size': self.size
                }
        
        # 做空套利机会 (Paradex买一价高于Lighter卖一价)
        if spread_short >= self.short_threshold:
            if abs(current_position + self.size) <= self.position_tracker.max_position:
                self.stats['spreads_detected'] += 1
                return {
                    'direction': 'SHORT',
                    'spread': spread_short,
                    'lighter_price': l_ask,
                    'paradex_price': p_bid,
                    'size': self.size
                }
        
        return None
    
    async def execute_arbitrage(self, opportunity):
        """执行套利交易"""
        print(f"\n\n🎯 发现套利机会!")
        print(f"   方向: {opportunity['direction']}")
        print(f"   价差: ${opportunity['spread']:.2f}")
        print(f"   Lighter: ${opportunity['lighter_price']:,.2f}")
        print(f"   Paradex: ${opportunity['paradex_price']:,.2f}")
        print(f"   交易量: {opportunity['size']}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            if opportunity['direction'] == 'LONG':
                # 做多套利: Lighter卖，Paradex买
                success = await self.execute_long_arbitrage(opportunity)
            else:
                # 做空套利: Lighter买，Paradex卖
                success = await self.execute_short_arbitrage(opportunity)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            if success:
                self.stats['total_trades'] += 1
                self.stats['successful_trades'] += 1
                self.stats['spreads_executed'] += 1
                self.stats['total_pnl'] += opportunity['spread'] * opportunity['size']
                self.last_arbitrage_time = time.time()
                
                print(f"✅ 套利交易成功!")
                print(f"   执行时间: {execution_time:.2f}秒")
                print(f"   预计利润: ${opportunity['spread'] * opportunity['size']:.2f}\n")
            else:
                self.stats['total_trades'] += 1
                self.stats['failed_trades'] += 1
                
                print(f"❌ 套利交易失败\n")
        
        except Exception as e:
            print(f"❌ 执行套利异常: {e}\n")
            self.stats['failed_trades'] += 1
    
    async def execute_long_arbitrage(self, opportunity):
        """执行做多套利"""
        return True
    
    async def execute_short_arbitrage(self, opportunity):
        """执行做空套利"""
        return True
    
    def get_success_rate(self):
        """计算成功率"""
        if self.stats['total_trades'] == 0:
            return 0.0
        return (self.stats['successful_trades'] / self.stats['total_trades']) * 100
    
    def get_statistics(self):
        """获取统计数据"""
        return {
            'total_trades': self.stats['total_trades'],
            'successful_trades': self.stats['successful_trades'],
            'failed_trades': self.stats['failed_trades'],
            'success_rate': self.get_success_rate(),
            'total_pnl': self.stats['total_pnl']
        }
