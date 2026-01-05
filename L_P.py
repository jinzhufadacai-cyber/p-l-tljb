#!/usr/bin/env python3
"""
Lighter和Paradex对冲套利脚本
基于cross-exchange-arbitrage策略，在Paradex下限价单（做市单），在Lighter上执行市价单对冲

主要功能：
1. 实时监控Lighter和Paradex的订单簿
2. 检测价差机会（Paradex买一价 vs Lighter卖一价）
3. 当价差超过阈值时执行套利：
   - 在Lighter上执行市价单（买入/卖出）
   - 在Paradex下限价单（做市单，低手续费）
4. 仓位管理和风险控制

环境变量配置（参考.env.example）：
- LIGHTER_API_KEY: Lighter API私钥
- LIGHTER_API_SECRET: Lighter账户索引和API密钥索引（格式：account_index,api_key_index）
- PARADEX_API_KEY: Paradex API密钥
- PARADEX_API_SECRET: Paradex API私钥

命令行参数：
--symbol: 交易对（默认：BTC/USDT）
--size: 每笔订单数量（默认：0.001）
--max-position: 最大持仓限制（默认：0.1）
--long-threshold: 做多套利触发阈值（Paradex买一价高于Lighter卖一价超过该值，默认：10）
--short-threshold: 做空套利触发阈值（Lighter买一价高于Paradex卖一价超过该值，默认：10）
--fill-timeout: 限价单成交超时时间（秒，默认：30）
--spread-threshold: 价差阈值（百分比，默认：0.001）
--scan-interval: 扫描间隔（秒，默认：2.0）
"""

import asyncio
import logging
import os
import sys
import time
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# 添加项目根目录到路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from arbitrage import (
        BaseExchange, OrderBook, Order, Position, ArbitrageOpportunity,
        OrderBookManager, PositionTracker, DataLogger,
        GenericArbitrageStrategy, WebSocketManager
    )
    # 导入真实交易所实现
    try:
        from exchanges.lighter_real import LighterRealExchange
        from exchanges.paradex_real import ParadexRealExchange
        # 使用真实交易所类
        LighterExchange = LighterRealExchange
        ParadexExchange = ParadexRealExchange
        REAL_EXCHANGES = True
        print("使用真实交易所实现")
    except ImportError as e:
        print(f"真实交易所模块导入失败，使用测试交易所: {e}")
        from arbitrage import LighterExchange, ParadexExchange
        REAL_EXCHANGES = False
        print("使用测试交易所实现")
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 arbitrage.py 在同一目录下")
    IMPORT_SUCCESS = False

# Telegram 控制模块（可选）
try:
    from telegram_bot import TelegramBotControl, start_telegram_control
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("注意: telegram_control 模块未找到，Telegram 控制功能将不可用")

@dataclass
class LighterParadexConfig:
    """Lighter和Paradex套利配置"""
    symbol: str = "BTC/USDT"
    order_size: float = 0.001
    max_position: float = 0.1
    long_threshold: float = 10.0  # 单位：价格差（USD）
    short_threshold: float = 10.0  # 单位：价格差（USD）
    fill_timeout: int = 30
    spread_threshold: float = 0.001  # 价差阈值（百分比）
    scan_interval: float = 2.0
    log_dir: str = "logs"
    use_real_exchanges: bool = True  # 是否使用真实交易所实现

class LighterParadexArbitrageBot:
    """Lighter和Paradex套利机器人"""
    
    def __init__(self, config: LighterParadexConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running = False
        
        # 交易所实例
        self.lighter_exchange: Optional[LighterExchange] = None
        self.paradex_exchange: Optional[ParadexExchange] = None
        
        # 策略模块
        self.ws_manager: Optional[WebSocketManager] = None
        self.order_book_manager: Optional[OrderBookManager] = None
        self.position_tracker: Optional[PositionTracker] = None
        self.data_logger: Optional[DataLogger] = None
        self.strategy: Optional[GenericArbitrageStrategy] = None
        
        # Telegram通知（由外部设置）
        self.telegram_bot = None
        
        # 交易统计
        self.total_profit = 0.0
        self.trade_count = 0
        
        # 后台任务
        self._task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """初始化所有组件"""
        self.logger.info("初始化Lighter和Paradex套利机器人")
        
        # 从环境变量加载API密钥（支持新旧两种格式）
        # Lighter: 优先使用新格式 API_KEY_PRIVATE_KEY，否则使用旧格式 LIGHTER_API_KEY
        lighter_api_key = os.getenv('API_KEY_PRIVATE_KEY') or os.getenv('LIGHTER_API_KEY')
        lighter_api_secret = os.getenv('LIGHTER_API_SECRET', '')
        
        # 如果使用新格式，构建包含索引的配置
        if os.getenv('API_KEY_PRIVATE_KEY'):
            account_index = os.getenv('LIGHTER_ACCOUNT_INDEX', '0')
            api_key_index = os.getenv('LIGHTER_API_KEY_INDEX', '0')
            # 将索引信息附加到 secret 中供 lighter_real.py 使用
            lighter_api_secret = f"{account_index},{api_key_index}"
        
        # Paradex: 优先使用新格式 PARADEX_L1_ADDRESS，否则使用旧格式 PARADEX_API_KEY
        paradex_api_key = os.getenv('PARADEX_L1_ADDRESS') or os.getenv('PARADEX_API_KEY')
        paradex_api_secret = os.getenv('PARADEX_L2_PRIVATE_KEY') or os.getenv('PARADEX_API_SECRET')
        
        if not lighter_api_key or not paradex_api_key:
            self.logger.error("缺少API密钥配置，请设置环境变量")
            self.logger.error("Lighter需要: API_KEY_PRIVATE_KEY 或 LIGHTER_API_KEY")
            self.logger.error("Paradex需要: PARADEX_L1_ADDRESS 或 PARADEX_API_KEY")
            raise ValueError("缺少必要的API密钥")
        
        # 创建交易所实例
        self.lighter_exchange = LighterExchange(
            api_key=lighter_api_key,
            api_secret=lighter_api_secret
        )
        
        self.paradex_exchange = ParadexExchange(
            api_key=paradex_api_key,
            api_secret=paradex_api_secret
        )
        
        self.logger.info("交易所实例创建成功")
        
        # 初始化WebSocket管理器
        self.ws_manager = WebSocketManager(
            exchange1=self.paradex_exchange,  # 限价单交易所（做市单）
            exchange2=self.lighter_exchange,  # 市价单交易所
            exchange1_name='paradex',
            exchange2_name='lighter',
            symbol=self.config.symbol
        )
        
        # 初始化订单簿管理器
        self.order_book_manager = OrderBookManager(
            symbol=self.config.symbol
        )
        
        # 初始化仓位跟踪器
        self.position_tracker = PositionTracker(
            max_position=self.config.max_position
        )
        
        # 初始化数据记录器
        self.data_logger = DataLogger(
            log_dir=self.config.log_dir
        )
        
        # 初始化套利策略
        self.strategy = GenericArbitrageStrategy(
            exchange1=self.paradex_exchange,
            exchange2=self.lighter_exchange,
            order_book_manager=self.order_book_manager,
            position_tracker=self.position_tracker,
            data_logger=self.data_logger,
            exchange1_name='paradex',
            exchange2_name='lighter',
            spread_threshold=self.config.spread_threshold,
            order_timeout=self.config.fill_timeout,
            symbol=self.config.symbol,
            scan_interval=self.config.scan_interval
        )
        
        self.logger.info("初始化完成")
    
    async def get_all_balances(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """获取两个交易所的余额"""
        try:
            self.logger.info("正在获取交易所余额...")
            paradex_balance = await self.paradex_exchange.get_balance()
            lighter_balance = await self.lighter_exchange.get_balance()
            self.logger.info(f"Paradex余额: {paradex_balance}, Lighter余额: {lighter_balance}")
            return paradex_balance, lighter_balance
        except Exception as e:
            self.logger.error(f"获取余额失败: {e}", exc_info=True)
            return {}, {}
    
    async def send_startup_balance_report(self):
        """启动时发送余额报告到Telegram"""
        if not self.telegram_bot:
            self.logger.info("Telegram机器人未配置，跳过余额报告")
            return
        
        try:
            paradex_balance, lighter_balance = await self.get_all_balances()
            
            # 发送余额报告
            await self.telegram_bot.send_balance_report(
                paradex_balance, 
                lighter_balance,
                title="🚀 *套利机器人启动 - 初始余额*"
            )
            self.logger.info("启动余额报告已发送到Telegram")
        except Exception as e:
            self.logger.error(f"发送启动余额报告失败: {e}")
    
    async def send_trade_notification(self, trade_result: Dict):
        """交易完成后发送通知"""
        if not self.telegram_bot:
            return
        
        try:
            # 获取当前余额
            paradex_balance, lighter_balance = await self.get_all_balances()
            
            # 发送交易完成通知
            await self.telegram_bot.send_trade_complete_notification(
                trade_result,
                paradex_balance,
                lighter_balance
            )
        except Exception as e:
            self.logger.error(f"发送交易通知失败: {e}")
    
    async def start(self):
        """启动套利机器人"""
        if self.running:
            self.logger.warning("机器人已经在运行中")
            return
        
        self.logger.info("启动Lighter和Paradex套利机器人...")
        self.running = True
        
        # 发送启动余额报告到Telegram
        await self.send_startup_balance_report()
        
        # 启动WebSocket连接
        await self.ws_manager.start()
        
        # 启动策略
        await self.strategy.start()
        
        # 创建后台任务运行主循环
        self._task = asyncio.create_task(self._run_loop())
        self.logger.info("机器人主循环已启动")
    
    async def _run_loop(self):
        """运行主循环"""
        try:
            last_status_log_time = time.time()
            last_arbitrage_time = 0
            arbitrage_cooldown = 2  # 套利冷却时间（秒）
            
            while self.running:
                current_time = time.time()
                
                # 检查套利机会（带冷却时间）
                if current_time - last_arbitrage_time >= arbitrage_cooldown:
                    opportunity = await self._check_arbitrage_opportunity()
                    if opportunity:
                        trade_result = await self._execute_arbitrage(opportunity)
                        if trade_result:
                            last_arbitrage_time = current_time
                            # 发送交易通知到Telegram
                            await self.send_trade_notification(trade_result)
                
                # 更新仓位信息
                await self.position_tracker.update_positions()
                
                # 记录数据
                await self.data_logger.log_data()
                
                # 每30秒输出一次状态日志
                if current_time - last_status_log_time >= 30:
                    await self._log_status_update()
                    last_status_log_time = current_time
                
                # 短暂休眠
                await asyncio.sleep(max(self.config.scan_interval, 0.5))
                
        except asyncio.CancelledError:
            self.logger.info("机器人主循环被取消")
            raise
        except KeyboardInterrupt:
            self.logger.info("接收到中断信号，正在停止...")
        except Exception as e:
            self.logger.error(f"运行过程中发生错误: {e}")
        finally:
            # 如果机器人仍在运行（异常退出），则停止
            if self.running:
                await self.stop()
    
    async def _check_arbitrage_opportunity(self) -> Optional[Dict]:
        """检查套利机会"""
        try:
            # 获取两个交易所的订单簿
            lighter_orderbook = await self.lighter_exchange.get_order_book(self.config.symbol)
            paradex_orderbook = await self.paradex_exchange.get_order_book(self.config.symbol)
            
            if not lighter_orderbook or not paradex_orderbook:
                return None
            
            # 存储订单簿数据供其他模块使用
            self.order_book_manager.order_books['lighter'] = lighter_orderbook
            self.order_book_manager.order_books['paradex'] = paradex_orderbook
            
            # 获取最优买卖价
            if not lighter_orderbook.bids or not lighter_orderbook.asks:
                return None
            if not paradex_orderbook.bids or not paradex_orderbook.asks:
                return None
            
            lighter_bid = lighter_orderbook.bids[0][0]  # Lighter最高买价
            lighter_ask = lighter_orderbook.asks[0][0]  # Lighter最低卖价
            paradex_bid = paradex_orderbook.bids[0][0]  # Paradex最高买价
            paradex_ask = paradex_orderbook.asks[0][0]  # Paradex最低卖价
            
            # 计算价差
            # 做多套利: Lighter买一价 > Paradex卖一价 (在Lighter卖，在Paradex买)
            spread_long = lighter_bid - paradex_ask
            # 做空套利: Paradex买一价 > Lighter卖一价 (在Paradex卖，在Lighter买)
            spread_short = paradex_bid - lighter_ask
            
            # 获取当前净仓位
            current_position = self.position_tracker.get_net_position() if hasattr(self.position_tracker, 'get_net_position') else 0
            
            # 检查做多套利机会
            if spread_long >= self.config.long_threshold:
                if abs(current_position - self.config.order_size) <= self.config.max_position:
                    return {
                        'direction': 'LONG',
                        'spread': spread_long,
                        'lighter_price': lighter_bid,
                        'paradex_price': paradex_ask,
                        'size': self.config.order_size
                    }
            
            # 检查做空套利机会
            if spread_short >= self.config.short_threshold:
                if abs(current_position + self.config.order_size) <= self.config.max_position:
                    return {
                        'direction': 'SHORT',
                        'spread': spread_short,
                        'lighter_price': lighter_ask,
                        'paradex_price': paradex_bid,
                        'size': self.config.order_size
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"检查套利机会失败: {e}")
            return None
    
    async def _execute_arbitrage(self, opportunity: Dict) -> Optional[Dict]:
        """执行套利交易"""
        direction = opportunity['direction']
        spread = opportunity['spread']
        size = opportunity['size']
        lighter_price = opportunity['lighter_price']
        paradex_price = opportunity['paradex_price']
        
        self.logger.info(f"🎯 发现套利机会! 方向: {direction}, 价差: ${spread:.2f}")
        
        start_time = time.time()
        success = False
        
        try:
            if direction == 'LONG':
                # 做多套利: 在Lighter卖出，在Paradex买入
                self.logger.info(f"执行做多套利: Lighter卖@{lighter_price:.2f}, Paradex买@{paradex_price:.2f}")
                
                # 在Lighter执行市价卖单
                lighter_order = await self.lighter_exchange.place_market_order(
                    symbol=self.config.symbol,
                    side='sell',
                    amount=size
                )
                
                # 在Paradex执行限价买单
                paradex_order = await self.paradex_exchange.place_limit_order(
                    symbol=self.config.symbol,
                    side='buy',
                    price=paradex_price,
                    amount=size
                )
                
                success = lighter_order is not None and paradex_order is not None
                
            else:  # SHORT
                # 做空套利: 在Paradex卖出，在Lighter买入
                self.logger.info(f"执行做空套利: Paradex卖@{paradex_price:.2f}, Lighter买@{lighter_price:.2f}")
                
                # 在Paradex执行限价卖单
                paradex_order = await self.paradex_exchange.place_limit_order(
                    symbol=self.config.symbol,
                    side='sell',
                    price=paradex_price,
                    amount=size
                )
                
                # 在Lighter执行市价买单
                lighter_order = await self.lighter_exchange.place_market_order(
                    symbol=self.config.symbol,
                    side='buy',
                    amount=size
                )
                
                success = lighter_order is not None and paradex_order is not None
            
            execution_time = time.time() - start_time
            profit = spread * size
            
            if success:
                self.trade_count += 1
                self.total_profit += profit
                self.logger.info(f"✅ 套利交易成功! 执行时间: {execution_time:.2f}秒, 预计利润: ${profit:.4f}")
            else:
                self.logger.warning(f"❌ 套利交易部分失败")
            
            # 返回交易结果
            return {
                'direction': direction,
                'spread': spread,
                'size': size,
                'profit': profit,
                'lighter_price': lighter_price,
                'paradex_price': paradex_price,
                'execution_time': execution_time,
                'success': success,
                'trade_count': self.trade_count,
                'total_profit': self.total_profit
            }
            
        except Exception as e:
            self.logger.error(f"执行套利交易失败: {e}")
            return {
                'direction': direction,
                'spread': spread,
                'size': size,
                'profit': 0,
                'lighter_price': lighter_price,
                'paradex_price': paradex_price,
                'execution_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
    
    async def _log_status_update(self):
        """输出状态日志"""
        try:
            # 获取交易所余额
            paradex_balance = await self.paradex_exchange.get_balance()
            lighter_balance = await self.lighter_exchange.get_balance()
            
            # 获取价差
            spread = self.order_book_manager.get_spread()
            
            # 获取性能指标
            metrics = self.position_tracker.get_performance_metrics()
            
            # 构建日志消息
            message = (
                f"=== Lighter/Paradex 套利状态 ===\n"
                f"交易对: {self.config.symbol}\n"
                f"当前价差: {spread:.4f}\n"
                f"总交易次数: {metrics.get('total_trades', 0)}\n"
                f"总交易量: {self.position_tracker.total_volume:.6f}\n"
                f"总利润: {metrics.get('total_profit', 0):.4f} USDT\n"
                f"总手续费: {metrics.get('total_fees', 0):.4f} USDT\n"
                f"净利润: {metrics.get('net_profit', 0):.4f} USDT\n"
                f"Paradex 余额: USDT={paradex_balance.get('USDT', 0):.2f}, BTC={paradex_balance.get('BTC', 0):.6f}\n"
                f"Lighter 余额: USDT={lighter_balance.get('USDT', 0):.2f}, BTC={lighter_balance.get('BTC', 0):.6f}"
            )
            
            self.logger.info(message)
            
        except Exception as e:
            self.logger.error(f"输出状态日志失败: {e}")
    
    async def stop(self):
        """停止套利机器人"""
        if not self.running:
            return
        
        self.logger.info("停止Lighter和Paradex套利机器人...")
        self.running = False
        
        # 取消后台任务（如果存在）
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.logger.error(f"停止任务时发生错误: {e}")
        
        # 停止策略
        if self.strategy:
            await self.strategy.stop()
        
        # 停止WebSocket连接
        if self.ws_manager:
            await self.ws_manager.stop()
        
        # 取消所有未完成订单
        if self.paradex_exchange:
            await self.paradex_exchange.cancel_all_orders()
        if self.lighter_exchange:
            await self.lighter_exchange.cancel_all_orders()
        
        # 清理任务引用
        self._task = None
        
        self.logger.info("机器人已停止")

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'lighter_paradex_arbitrage_{time.strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    
    # 降低敏感库的日志级别，避免在日志中暴露API密钥等敏感信息
    # httpx库会记录完整的HTTP请求URL，其中可能包含Telegram bot token
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    # 其他可能记录敏感信息的库
    logging.getLogger('telegram').setLevel(logging.WARNING)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Lighter和Paradex对冲套利机器人')
    
    parser.add_argument('--symbol', type=str, default='BTC/USDT',
                       help='交易对（默认：BTC/USDT）')
    parser.add_argument('--size', type=float, default=0.001,
                       help='每笔订单数量（默认：0.001）')
    parser.add_argument('--max-position', type=float, default=0.1,
                       help='最大持仓限制（默认：0.1）')
    parser.add_argument('--long-threshold', type=float, default=10.0,
                       help='做多套利触发阈值（Paradex买一价高于Lighter卖一价超过该值，默认：10）')
    parser.add_argument('--short-threshold', type=float, default=10.0,
                       help='做空套利触发阈值（Lighter买一价高于Paradex卖一价超过该值，默认：10）')
    parser.add_argument('--fill-timeout', type=int, default=30,
                       help='限价单成交超时时间（秒，默认：30）')
    parser.add_argument('--spread-threshold', type=float, default=0.001,
                       help='价差阈值（百分比，默认：0.001）')
    parser.add_argument('--scan-interval', type=float, default=2.0,
                       help='扫描间隔（秒，默认：2.0）')
    parser.add_argument('--log-dir', type=str, default='logs',
                       help='日志目录默认（：logs）')
    parser.add_argument('--telegram-token', type=str, default='',
                       help='Telegram Bot Token (可选，从 @BotFather 获取)')
    parser.add_argument('--telegram-chat-id', type=str, default='',
                       help='Telegram Chat ID (可选，限制访问的聊天ID)')
    
    return parser.parse_args()

async def main():
    """主函数"""
    if not IMPORT_SUCCESS:
        print("导入失败，请检查依赖")
        return
    
    # 加载环境变量
    load_dotenv()
    
    # 解析命令行参数
    args = parse_args()
    
    # 如果未通过命令行提供Telegram token，尝试从环境变量读取
    if not args.telegram_token:
        env_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if env_token:
            args.telegram_token = env_token
            print(f"从环境变量读取Telegram Bot Token")
    
    if not args.telegram_chat_id:
        env_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if env_chat_id:
            args.telegram_chat_id = env_chat_id
            print(f"从环境变量读取Telegram Chat ID")
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 创建配置
    config = LighterParadexConfig(
        symbol=args.symbol,
        order_size=args.size,
        max_position=args.max_position,
        long_threshold=args.long_threshold,
        short_threshold=args.short_threshold,
        fill_timeout=args.fill_timeout,
        spread_threshold=args.spread_threshold,
        scan_interval=args.scan_interval,
        log_dir=args.log_dir
    )
    
    logger.info(f"启动Lighter和Paradex套利机器人，配置：{config}")
    
    # 检查必要的环境变量（支持新旧两种格式）
    # Lighter: 需要 API_KEY_PRIVATE_KEY 或 LIGHTER_API_KEY
    lighter_configured = os.getenv('API_KEY_PRIVATE_KEY') or os.getenv('LIGHTER_API_KEY')
    # Paradex: 需要 PARADEX_L1_ADDRESS 或 PARADEX_API_KEY
    paradex_configured = os.getenv('PARADEX_L1_ADDRESS') or os.getenv('PARADEX_API_KEY')
    
    missing_configs = []
    if not lighter_configured:
        missing_configs.append("Lighter (设置 API_KEY_PRIVATE_KEY 或 LIGHTER_API_KEY)")
    if not paradex_configured:
        missing_configs.append("Paradex (设置 PARADEX_L1_ADDRESS 或 PARADEX_API_KEY)")
    
    if missing_configs:
        logger.error(f"缺少必要的环境变量配置:")
        for config in missing_configs:
            logger.error(f"  - {config}")
        logger.error("请设置环境变量或创建.env文件")
        return
    
    # 创建并启动机器人
    bot = LighterParadexArbitrageBot(config)
    
    # Telegram 机器人控制（可选）
    telegram_bot = None
    if args.telegram_token and TELEGRAM_AVAILABLE:
        try:
            logger.info("正在启动 Telegram 控制机器人...")
            telegram_bot = await start_telegram_control(
                token=args.telegram_token,
                chat_id=args.telegram_chat_id if args.telegram_chat_id else None,
                arbitrage_bot=bot
            )
            if telegram_bot:
                logger.info("Telegram 控制机器人启动成功")
                # 将telegram_bot引用传递给套利机器人，以便发送交易通知
                bot.telegram_bot = telegram_bot
                # 发送启动通知
                await telegram_bot.send_notification(
                    f"🤖 *Lighter-Paradex 套利机器人已启动*\n"
                    f"交易对: {config.symbol}\n"
                    f"订单大小: {config.order_size}\n"
                    f"最大持仓: {config.max_position}\n"
                    f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
        except Exception as e:
            logger.error(f"启动 Telegram 控制失败: {e}")
            telegram_bot = None
    
    try:
        await bot.initialize()
        await bot.start()
        
        # 保持运行直到被中断
        while bot.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止...")
    except Exception as e:
        logger.error(f"机器人运行失败: {e}")
        # 发送错误通知
        if telegram_bot:
            await telegram_bot.send_error_alert(str(e))
        raise
    finally:
        await bot.stop()
        # 停止 Telegram 机器人
        if telegram_bot:
            await telegram_bot.stop()

if __name__ == "__main__":
    asyncio.run(main())