"""
Telegram 机器人控制系统 for Lighter-Paradex 套利机器人
基于 python-telegram-bot 库，提供远程控制功能
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        filters,
        ContextTypes,
        CallbackContext
    )
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("警告: python-telegram-bot 未安装，Telegram 控制功能将不可用")
    print("请运行: pip install python-telegram-bot==20.7")


class TelegramBotControl:
    """Telegram 机器人控制类"""
    
    def __init__(self, token: str, chat_id: Optional[str] = None, 
                 arbitrage_bot=None):
        """
        初始化 Telegram 机器人
        
        Args:
            token: Telegram Bot Token (从 @BotFather 获取)
            chat_id: 允许控制的聊天ID (可选，不设置则允许所有用户)
            arbitrage_bot: LighterParadexArbitrageBot 实例的引用
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot 未安装")
            
        self.token = token
        self.chat_id = chat_id
        self.arbitrage_bot = arbitrage_bot
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 创建 Telegram 应用
        self.application = ApplicationBuilder().token(token).build()
        
        # 注册命令处理器
        self._setup_handlers()
        
        # 运行状态
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
    def _setup_handlers(self):
        """设置命令处理器"""
        
        # 开始/帮助命令
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        
        # 机器人控制命令
        self.application.add_handler(CommandHandler("run", self._cmd_run))
        self.application.add_handler(CommandHandler("stop", self._cmd_stop))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        
        # 配置命令
        self.application.add_handler(CommandHandler("config", self._cmd_config))
        self.application.add_handler(CommandHandler("balance", self._cmd_balance))
        self.application.add_handler(CommandHandler("performance", self._cmd_performance))
        
        # 紧急命令
        self.application.add_handler(CommandHandler("emergency_stop", self._cmd_emergency_stop))
        self.application.add_handler(CommandHandler("cancel_all", self._cmd_cancel_all))
        
        # 键盘按钮
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self._handle_message
        ))
    
    async def _check_access(self, update: Update) -> bool:
        """检查用户是否有权限访问"""
        if self.chat_id is None:
            return True
            
        user_chat_id = str(update.effective_chat.id)
        if user_chat_id != self.chat_id:
            await update.message.reply_text(
                "⛔ 未经授权的访问。请联系管理员获取权限。"
            )
            return False
        return True
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        if not await self._check_access(update):
            return
            
        welcome_text = """
🤖 *Lighter-Paradex 套利机器人控制面板*

欢迎使用套利机器人控制系统！以下命令可用：

*基本控制*
/start - 显示此帮助信息
/help - 显示详细帮助
/status - 查看机器人状态
/run - 启动套利机器人
/stop - 停止套利机器人

*信息查询*
/config - 查看当前配置
/balance - 查看交易所余额
/performance - 查看交易性能

*紧急操作*
/emergency_stop - 紧急停止所有交易
/cancel_all - 取消所有挂单

*快捷键盘*
点击下方键盘按钮快速操作
        """
        
        # 创建自定义键盘
        keyboard = [
            [KeyboardButton("📊 状态"), KeyboardButton("▶️ 启动")],
            [KeyboardButton("⏹️ 停止"), KeyboardButton("💰 余额")],
            [KeyboardButton("⚙️ 配置"), KeyboardButton("📈 性能")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        if not await self._check_access(update):
            return
            
        help_text = """
📖 *详细帮助文档*

*套利策略*
- 在 Paradex 上挂 post-only 限价单（做市单）
- 在 Lighter 上执行市价单对冲
- 实时监控两个交易所的订单簿
- 自动检测价差机会

*命令说明*
/run - 启动套利策略，开始监控和执行交易
/stop - 优雅停止，完成当前交易后停止
/status - 显示当前状态：运行状态、价差、仓位等
/config - 显示当前配置参数
/balance - 显示两个交易所的余额
/performance - 显示交易统计数据

*紧急命令*
/emergency_stop - 立即停止所有交易活动，取消所有订单
/cancel_all - 仅取消所有挂单，不停止机器人

*配置说明*
配置通过环境变量和命令行参数设置：
- LIGHTER_API_KEY, LIGHTER_API_SECRET
- PARADEX_API_KEY, PARADEX_API_SECRET
- 命令行参数：--symbol, --size, --max-position 等

*注意事项*
⚠️ 套利交易存在风险，请谨慎使用
⚠️ 建议先在小额资金下测试
⚠️ 确保网络连接稳定
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def _cmd_run(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /run 命令 - 启动机器人"""
        if not await self._check_access(update):
            return
            
        if not self.arbitrage_bot:
            await update.message.reply_text("❌ 未连接到套利机器人实例")
            return
            
        if self.arbitrage_bot.running:
            await update.message.reply_text("✅ 机器人已经在运行中")
            return
            
        try:
            await update.message.reply_text("🔄 正在启动套利机器人...")
            await self.arbitrage_bot.start()
            await update.message.reply_text("✅ 套利机器人启动成功")
        except Exception as e:
            self.logger.error(f"启动机器人失败: {e}")
            await update.message.reply_text(f"❌ 启动失败: {str(e)}")
    
    async def _cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /stop 命令 - 停止机器人"""
        if not await self._check_access(update):
            return
            
        if not self.arbitrage_bot:
            await update.message.reply_text("❌ 未连接到套利机器人实例")
            return
            
        if not self.arbitrage_bot.running:
            await update.message.reply_text("✅ 机器人已经停止")
            return
            
        try:
            await update.message.reply_text("🔄 正在停止套利机器人...")
            await self.arbitrage_bot.stop()
            await update.message.reply_text("✅ 套利机器人已停止")
        except Exception as e:
            self.logger.error(f"停止机器人失败: {e}")
            await update.message.reply_text(f"❌ 停止失败: {str(e)}")
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令 - 查看状态"""
        if not await self._check_access(update):
            return
            
        if not self.arbitrage_bot:
            status_text = """
🤖 *机器人状态*
状态: ❌ 未连接到套利机器人
请确保机器人已正确初始化
            """
            await update.message.reply_text(status_text, parse_mode='Markdown')
            return
            
        try:
            # 获取机器人状态信息
            bot_running = self.arbitrage_bot.running
            config = self.arbitrage_bot.config
            
            status_text = f"""
🤖 *机器人状态*
状态: {'✅ 运行中' if bot_running else '⏸️ 已停止'}
交易对: {config.symbol}
订单大小: {config.order_size}
最大持仓: {config.max_position}
价差阈值: {config.spread_threshold:.4%}
扫描间隔: {config.scan_interval}秒
            """
            
            # 如果运行中，尝试获取更多信息
            if bot_running and hasattr(self.arbitrage_bot, 'order_book_manager'):
                try:
                    spread = self.arbitrage_bot.order_book_manager.get_spread()
                    status_text += f"\n当前价差: {spread:.4f}"
                except:
                    status_text += "\n当前价差: 获取中..."
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"获取状态失败: {e}")
            await update.message.reply_text(f"❌ 获取状态失败: {str(e)}")
    
    async def _cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /config 命令 - 查看配置"""
        if not await self._check_access(update):
            return
            
        if not self.arbitrage_bot:
            await update.message.reply_text("❌ 未连接到套利机器人实例")
            return
            
        try:
            config = self.arbitrage_bot.config
            
            config_text = f"""
⚙️ *当前配置*

*交易设置*
交易对: {config.symbol}
订单大小: {config.order_size}
最大持仓: {config.max_position}

*策略参数*
做多阈值: {config.long_threshold}
做空阈值: {config.short_threshold}
价差阈值: {config.spread_threshold:.4%}
成交超时: {config.fill_timeout}秒
扫描间隔: {config.scan_interval}秒

*路径设置*
日志目录: {config.log_dir}
            """
            
            await update.message.reply_text(config_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"获取配置失败: {e}")
            await update.message.reply_text(f"❌ 获取配置失败: {str(e)}")
    
    async def _cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /balance 命令 - 查看余额"""
        if not await self._check_access(update):
            return
            
        if not self.arbitrage_bot:
            await update.message.reply_text("❌ 未连接到套利机器人实例")
            return
            
        try:
            # 获取交易所余额
            paradex_balance = await self.arbitrage_bot.paradex_exchange.get_balance()
            lighter_balance = await self.arbitrage_bot.lighter_exchange.get_balance()
            
            balance_text = """
💰 *交易所余额*

*Paradex 余额*
"""
            for asset, amount in paradex_balance.items():
                balance_text += f"{asset}: {amount:.6f}\n"
            
            balance_text += "\n*Lighter 余额*\n"
            for asset, amount in lighter_balance.items():
                balance_text += f"{asset}: {amount:.6f}\n"
            
            await update.message.reply_text(balance_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"获取余额失败: {e}")
            await update.message.reply_text(f"❌ 获取余额失败: {str(e)}")
    
    async def _cmd_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /performance 命令 - 查看性能"""
        if not await self._check_access(update):
            return
            
        if not self.arbitrage_bot:
            await update.message.reply_text("❌ 未连接到套利机器人实例")
            return
            
        try:
            # 获取性能指标
            if hasattr(self.arbitrage_bot, 'position_tracker'):
                metrics = self.arbitrage_bot.position_tracker.get_performance_metrics()
                
                perf_text = f"""
📈 *交易性能统计*

总交易次数: {metrics.get('total_trades', 0)}
总交易量: {self.arbitrage_bot.position_tracker.total_volume:.6f}
总利润: {metrics.get('total_profit', 0):.4f} USDT
总手续费: {metrics.get('total_fees', 0):.4f} USDT
净利润: {metrics.get('net_profit', 0):.4f} USDT

*状态*
运行时间: 获取中...
最后交易: 获取中...
                """
            else:
                perf_text = """
📈 *交易性能统计*
暂无交易数据
机器人可能未运行或未进行交易
                """
            
            await update.message.reply_text(perf_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"获取性能数据失败: {e}")
            await update.message.reply_text(f"❌ 获取性能数据失败: {str(e)}")
    
    async def _cmd_emergency_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /emergency_stop 命令 - 紧急停止"""
        if not await self._check_access(update):
            return
            
        await update.message.reply_text("🆘 正在执行紧急停止...")
        
        # 停止机器人
        if self.arbitrage_bot:
            try:
                self.arbitrage_bot.running = False
                await self.arbitrage_bot.stop()
            except Exception as e:
                self.logger.error(f"紧急停止失败: {e}")
        
        # 取消所有订单
        try:
            if self.arbitrage_bot and self.arbitrage_bot.paradex_exchange:
                await self.arbitrage_bot.paradex_exchange.cancel_all_orders()
            if self.arbitrage_bot and self.arbitrage_bot.lighter_exchange:
                await self.arbitrage_bot.lighter_exchange.cancel_all_orders()
        except Exception as e:
            self.logger.error(f"取消订单失败: {e}")
        
        await update.message.reply_text("✅ 紧急停止完成，所有交易已停止，所有订单已取消")
    
    async def _cmd_cancel_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /cancel_all 命令 - 取消所有订单"""
        if not await self._check_access(update):
            return
            
        await update.message.reply_text("🔄 正在取消所有订单...")
        
        try:
            if self.arbitrage_bot and self.arbitrage_bot.paradex_exchange:
                await self.arbitrage_bot.paradex_exchange.cancel_all_orders()
            if self.arbitrage_bot and self.arbitrage_bot.lighter_exchange:
                await self.arbitrage_bot.lighter_exchange.cancel_all_orders()
            await update.message.reply_text("✅ 所有订单已取消")
        except Exception as e:
            self.logger.error(f"取消订单失败: {e}")
            await update.message.reply_text(f"❌ 取消订单失败: {str(e)}")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文本消息（键盘按钮）"""
        if not await self._check_access(update):
            return
            
        text = update.message.text
        
        if text == "📊 状态":
            await self._cmd_status(update, context)
        elif text == "▶️ 启动":
            await self._cmd_run(update, context)
        elif text == "⏹️ 停止":
            await self._cmd_stop(update, context)
        elif text == "💰 余额":
            await self._cmd_balance(update, context)
        elif text == "⚙️ 配置":
            await self._cmd_config(update, context)
        elif text == "📈 性能":
            await self._cmd_performance(update, context)
        else:
            await update.message.reply_text(
                "请使用命令或点击下方按钮进行操作。输入 /help 查看帮助。"
            )
    
    async def start(self):
        """启动 Telegram 机器人"""
        if self.running:
            self.logger.warning("Telegram 机器人已经在运行中")
            return
            
        self.logger.info("启动 Telegram 控制机器人...")
        self.running = True
        
        # 启动 Telegram bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        self.logger.info("Telegram 控制机器人启动成功")
    
    async def stop(self):
        """停止 Telegram 机器人"""
        if not self.running:
            return
            
        self.logger.info("停止 Telegram 控制机器人...")
        self.running = False
        
        # 停止 Telegram bot
        await self.application.stop()
        
        self.logger.info("Telegram 控制机器人已停止")
    
    async def send_notification(self, message: str, parse_mode: str = 'Markdown'):
        """发送通知消息到授权聊天"""
        if not self.running or not self.chat_id:
            return
            
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
        except TelegramError as e:
            self.logger.error(f"发送 Telegram 通知失败: {e}")
    
    async def send_trade_alert(self, trade_info: Dict[str, Any]):
        """发送交易提醒"""
        if not self.running or not self.chat_id:
            return
            
        try:
            symbol = trade_info.get('symbol', 'Unknown')
            side = trade_info.get('side', 'Unknown')
            amount = trade_info.get('amount', 0)
            price = trade_info.get('price', 0)
            exchange = trade_info.get('exchange', 'Unknown')
            profit = trade_info.get('profit', 0)
            
            message = f"""
💼 *新交易执行*
交易对: {symbol}
方向: {side}
数量: {amount}
价格: {price}
交易所: {exchange}
预估利润: {profit:.4f} USDT
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await self.send_notification(message)
            
        except Exception as e:
            self.logger.error(f"发送交易提醒失败: {e}")
    
    async def send_error_alert(self, error_message: str):
        """发送错误提醒"""
        if not self.running or not self.chat_id:
            return
            
        try:
            message = f"""
🚨 *系统错误*
错误信息: {error_message}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
请立即检查系统状态！
            """
            
            await self.send_notification(message)
            
        except Exception as e:
            self.logger.error(f"发送错误提醒失败: {e}")
    
    async def send_balance_report(self, paradex_balance: Dict[str, float], 
                                   lighter_balance: Dict[str, float],
                                   title: str = "💰 账户余额报告"):
        """发送余额报告到Telegram"""
        if not self.chat_id:
            self.logger.warning("未设置chat_id，无法发送余额报告")
            return
            
        try:
            # 构建余额消息
            message = f"""
{title}

*Paradex 余额*
"""
            for asset, amount in paradex_balance.items():
                if amount > 0:
                    message += f"  {asset}: {amount:.6f}\n"
            
            message += "\n*Lighter 余额*\n"
            for asset, amount in lighter_balance.items():
                if amount > 0:
                    message += f"  {asset}: {amount:.6f}\n"
            
            message += f"\n⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await self.send_notification(message)
            self.logger.info("余额报告已发送到Telegram")
            
        except Exception as e:
            self.logger.error(f"发送余额报告失败: {e}")
    
    async def send_trade_complete_notification(self, trade_result: Dict[str, Any],
                                                paradex_balance: Dict[str, float],
                                                lighter_balance: Dict[str, float]):
        """发送交易完成通知，包含利润和余额信息"""
        if not self.chat_id:
            return
            
        try:
            direction = trade_result.get('direction', 'Unknown')
            spread = trade_result.get('spread', 0)
            size = trade_result.get('size', 0)
            profit = trade_result.get('profit', spread * size)
            lighter_price = trade_result.get('lighter_price', 0)
            paradex_price = trade_result.get('paradex_price', 0)
            execution_time = trade_result.get('execution_time', 0)
            success = trade_result.get('success', True)
            
            # 状态图标
            status_icon = "✅" if success else "❌"
            direction_icon = "📈" if direction == 'LONG' else "📉"
            
            message = f"""
{status_icon} *套利交易{'成功' if success else '失败'}*

{direction_icon} 方向: {direction}
💵 价差: ${spread:.2f}
📊 交易量: {size}
💰 预计利润: ${profit:.4f}

*价格详情*
  Lighter: ${lighter_price:,.2f}
  Paradex: ${paradex_price:,.2f}

⏱️ 执行时间: {execution_time:.2f}秒

━━━━━━━━━━━━━━━━━━━━
*当前余额*

*Paradex*
"""
            for asset, amount in paradex_balance.items():
                if amount > 0:
                    message += f"  {asset}: {amount:.6f}\n"
            
            message += "\n*Lighter*\n"
            for asset, amount in lighter_balance.items():
                if amount > 0:
                    message += f"  {asset}: {amount:.6f}\n"
            
            message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await self.send_notification(message)
            
        except Exception as e:
            self.logger.error(f"发送交易完成通知失败: {e}")


async def start_telegram_control(token: str, chat_id: Optional[str] = None, 
                                 arbitrage_bot=None):
    """
    启动 Telegram 控制系统的快捷函数
    
    Args:
        token: Telegram Bot Token
        chat_id: 允许控制的聊天ID
        arbitrage_bot: LighterParadexArbitrageBot 实例
    
    Returns:
        TelegramBotControl 实例
    """
    if not TELEGRAM_AVAILABLE:
        logging.warning("python-telegram-bot 未安装，跳过 Telegram 控制功能")
        return None
    
    try:
        bot_control = TelegramBotControl(token, chat_id, arbitrage_bot)
        await bot_control.start()
        return bot_control
    except Exception as e:
        logging.error(f"启动 Telegram 控制失败: {e}")
        return None