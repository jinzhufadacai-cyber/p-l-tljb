#!/usr/bin/env python3
"""
Telegram 机器人控制系统 for Lighter-Paradex 套利机器人
整合了控制模块和机器人控制器功能

功能：
1. TelegramBotControl - 被 L_P.py 使用，提供通知和控制功能
2. TelegramBotController - 独立运行，管理套利脚本作为子进程
3. start_telegram_control - 快捷启动函数
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import time
import threading
import atexit
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

# Windows 文件锁支持
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False

try:
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
    from telegram.ext import (
        Application, ApplicationBuilder,
        CommandHandler, MessageHandler, ConversationHandler,
        filters, ContextTypes
    )
    from telegram.constants import ChatAction
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("警告: python-telegram-bot 未安装，Telegram 控制功能将不可用")
    print("请运行: pip install python-telegram-bot>=20.7")


# ============================================================
# 第一部分: TelegramBotControl - 被 L_P.py 使用
# ============================================================

class TelegramBotControl:
    """Telegram 机器人控制类 - 被 L_P.py 使用"""
    
    def __init__(self, token: str, chat_id: Optional[str] = None, 
                 arbitrage_bot=None):
        """
        初始化 Telegram 机器人
        
        Args:
            token: Telegram Bot Token (从 @BotFather 获取)
            chat_id: 允许控制的聊天ID (可选)
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
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("run", self._cmd_run))
        self.application.add_handler(CommandHandler("stop", self._cmd_stop))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("config", self._cmd_config))
        self.application.add_handler(CommandHandler("balance", self._cmd_balance))
        self.application.add_handler(CommandHandler("performance", self._cmd_performance))
        self.application.add_handler(CommandHandler("emergency_stop", self._cmd_emergency_stop))
        self.application.add_handler(CommandHandler("cancel_all", self._cmd_cancel_all))
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
                f"⛔ 未经授权的访问。您的用户ID: {user_chat_id}\n请联系管理员获取权限。"
            )
            return False
        return True
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        if not await self._check_access(update):
            return
        welcome_text = """
🤖 *Lighter-Paradex 套利机器人控制面板*

欢迎使用套利机器人控制系统！

*基本控制*
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
        """
        keyboard = [
            [KeyboardButton("📊 状态"), KeyboardButton("▶️ 启动")],
            [KeyboardButton("⏹️ 停止"), KeyboardButton("💰 余额")],
            [KeyboardButton("⚙️ 配置"), KeyboardButton("📈 性能")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        if not await self._check_access(update):
            return
        help_text = """
📖 *详细帮助*

*套利策略*
• 在 Paradex 上挂限价单（做市单）
• 在 Lighter 上执行市价单对冲
• 实时监控两个交易所的订单簿

*命令说明*
/run - 启动套利策略
/stop - 优雅停止
/status - 显示当前状态
/config - 显示配置参数
/balance - 显示余额
/performance - 显示统计数据

*紧急命令*
/emergency_stop - 立即停止所有交易
/cancel_all - 仅取消所有挂单
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def _cmd_run(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /run 命令"""
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
        """处理 /stop 命令"""
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
        """处理 /status 命令"""
        if not await self._check_access(update):
            return
        if not self.arbitrage_bot:
            await update.message.reply_text("❌ 未连接到套利机器人实例", parse_mode='Markdown')
            return
        try:
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
            if bot_running and hasattr(self.arbitrage_bot, 'order_book_manager'):
                try:
                    spread = self.arbitrage_bot.order_book_manager.get_spread()
                    status_text += f"\n当前价差: {spread:.4f}"
                except:
                    pass
            await update.message.reply_text(status_text, parse_mode='Markdown')
        except Exception as e:
            self.logger.error(f"获取状态失败: {e}")
            await update.message.reply_text(f"❌ 获取状态失败: {str(e)}")
    
    async def _cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /config 命令"""
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
            """
            await update.message.reply_text(config_text, parse_mode='Markdown')
        except Exception as e:
            self.logger.error(f"获取配置失败: {e}")
            await update.message.reply_text(f"❌ 获取配置失败: {str(e)}")
    
    async def _cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /balance 命令"""
        if not await self._check_access(update):
            return
        if not self.arbitrage_bot:
            await update.message.reply_text("❌ 未连接到套利机器人实例")
            return
        try:
            paradex_balance = await self.arbitrage_bot.paradex_exchange.get_balance()
            lighter_balance = await self.arbitrage_bot.lighter_exchange.get_balance()
            balance_text = "💰 *交易所余额*\n\n*Paradex*\n"
            for asset, amount in paradex_balance.items():
                balance_text += f"  {asset}: {amount:.6f}\n"
            balance_text += "\n*Lighter*\n"
            for asset, amount in lighter_balance.items():
                balance_text += f"  {asset}: {amount:.6f}\n"
            await update.message.reply_text(balance_text, parse_mode='Markdown')
        except Exception as e:
            self.logger.error(f"获取余额失败: {e}")
            await update.message.reply_text(f"❌ 获取余额失败: {str(e)}")
    
    async def _cmd_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /performance 命令"""
        if not await self._check_access(update):
            return
        if not self.arbitrage_bot:
            await update.message.reply_text("❌ 未连接到套利机器人实例")
            return
        try:
            if hasattr(self.arbitrage_bot, 'position_tracker'):
                metrics = self.arbitrage_bot.position_tracker.get_performance_metrics()
                perf_text = f"""
📈 *交易性能统计*
总交易次数: {metrics.get('total_trades', 0)}
总交易量: {self.arbitrage_bot.position_tracker.total_volume:.6f}
总利润: {metrics.get('total_profit', 0):.4f} USDT
总手续费: {metrics.get('total_fees', 0):.4f} USDT
净利润: {metrics.get('net_profit', 0):.4f} USDT
                """
            else:
                perf_text = "📈 *交易性能统计*\n暂无交易数据"
            await update.message.reply_text(perf_text, parse_mode='Markdown')
        except Exception as e:
            self.logger.error(f"获取性能数据失败: {e}")
            await update.message.reply_text(f"❌ 获取性能数据失败: {str(e)}")
    
    async def _cmd_emergency_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /emergency_stop 命令"""
        if not await self._check_access(update):
            return
        await update.message.reply_text("🆘 正在执行紧急停止...")
        if self.arbitrage_bot:
            try:
                self.arbitrage_bot.running = False
                await self.arbitrage_bot.stop()
            except Exception as e:
                self.logger.error(f"紧急停止失败: {e}")
        try:
            if self.arbitrage_bot and self.arbitrage_bot.paradex_exchange:
                await self.arbitrage_bot.paradex_exchange.cancel_all_orders()
            if self.arbitrage_bot and self.arbitrage_bot.lighter_exchange:
                await self.arbitrage_bot.lighter_exchange.cancel_all_orders()
        except Exception as e:
            self.logger.error(f"取消订单失败: {e}")
        await update.message.reply_text("✅ 紧急停止完成")
    
    async def _cmd_cancel_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /cancel_all 命令"""
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
            await update.message.reply_text("请使用命令或点击下方按钮。输入 /help 查看帮助。")
    
    async def start(self):
        """启动 Telegram 机器人"""
        if self.running:
            self.logger.warning("Telegram 机器人已经在运行中")
            return
        self.logger.info("启动 Telegram 控制机器人...")
        self.running = True
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
        await self.application.stop()
        self.logger.info("Telegram 控制机器人已停止")
    
    async def send_notification(self, message: str, parse_mode: str = 'Markdown'):
        """发送通知消息"""
        if not self.running or not self.chat_id:
            return
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode=parse_mode
            )
        except TelegramError as e:
            self.logger.error(f"发送通知失败: {e}")
    
    async def send_trade_alert(self, trade_info: Dict[str, Any]):
        """发送交易提醒"""
        if not self.running or not self.chat_id:
            return
        try:
            message = f"""
💼 *新交易执行*
交易对: {trade_info.get('symbol', 'Unknown')}
方向: {trade_info.get('side', 'Unknown')}
数量: {trade_info.get('amount', 0)}
价格: {trade_info.get('price', 0)}
交易所: {trade_info.get('exchange', 'Unknown')}
预估利润: {trade_info.get('profit', 0):.4f} USDT
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
            """
            await self.send_notification(message)
        except Exception as e:
            self.logger.error(f"发送错误提醒失败: {e}")
    
    async def send_balance_report(self, paradex_balance: Dict[str, float], 
                                   lighter_balance: Dict[str, float],
                                   title: str = "💰 账户余额报告"):
        """发送余额报告"""
        if not self.chat_id:
            return
        try:
            message = f"{title}\n\n*Paradex*\n"
            if paradex_balance:
                has_balance = False
                for asset, amount in paradex_balance.items():
                    if amount > 0:
                        message += f"  {asset}: {amount:.6f}\n"
                        has_balance = True
                if not has_balance:
                    message += "  暂无余额数据\n"
            else:
                message += "  获取余额失败或暂无数据\n"
            
            message += "\n*Lighter*\n"
            if lighter_balance:
                has_balance = False
                for asset, amount in lighter_balance.items():
                    if amount > 0:
                        message += f"  {asset}: {amount:.6f}\n"
                        has_balance = True
                if not has_balance:
                    message += "  暂无余额数据\n"
            else:
                message += "  获取余额失败或暂无数据\n"
            
            message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await self.send_notification(message)
        except Exception as e:
            self.logger.error(f"发送余额报告失败: {e}")
    
    async def send_trade_complete_notification(self, trade_result: Dict[str, Any],
                                                paradex_balance: Dict[str, float],
                                                lighter_balance: Dict[str, float]):
        """发送交易完成通知"""
        if not self.chat_id:
            return
        try:
            direction = trade_result.get('direction', 'Unknown')
            spread = trade_result.get('spread', 0)
            size = trade_result.get('size', 0)
            profit = trade_result.get('profit', spread * size)
            success = trade_result.get('success', True)
            status_icon = "✅" if success else "❌"
            direction_icon = "📈" if direction == 'LONG' else "📉"
            
            message = f"""
{status_icon} *套利交易{'成功' if success else '失败'}*

{direction_icon} 方向: {direction}
💵 价差: ${spread:.2f}
📊 交易量: {size}
💰 预计利润: ${profit:.4f}

*价格*
  Lighter: ${trade_result.get('lighter_price', 0):,.2f}
  Paradex: ${trade_result.get('paradex_price', 0):,.2f}

⏱️ 执行: {trade_result.get('execution_time', 0):.2f}秒

━━━━━━━━━━━━━━━━
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


# ============================================================
# 第二部分: TelegramBotController - 独立运行的控制器
# ============================================================

class BotStatus(Enum):
    """机器人状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ArbitrageConfig:
    """套利脚本配置"""
    script_path: str = "L_P.py"
    symbol: str = "BTC/USDT"
    size: float = 0.001
    max_position: float = 0.1
    long_threshold: float = 10.0
    short_threshold: float = 10.0
    scan_interval: float = 2.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ArbitrageProcessManager:
    """套利进程管理器"""
    
    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.status = BotStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.output_buffer: list = []
        self.error_buffer: list = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def start(self) -> bool:
        """启动套利进程"""
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                self.logger.warning("进程已在运行")
                return False
            try:
                if not os.path.exists(self.config.script_path):
                    self.logger.error(f"脚本不存在: {self.config.script_path}")
                    self.status = BotStatus.ERROR
                    return False
                
                cmd = [
                    sys.executable,
                    self.config.script_path,
                    f"--symbol={self.config.symbol}",
                    f"--size={self.config.size}",
                    f"--max-position={self.config.max_position}",
                    f"--long-threshold={self.config.long_threshold}",
                    f"--short-threshold={self.config.short_threshold}",
                    f"--scan-interval={self.config.scan_interval}"
                ]
                
                env = os.environ.copy()
                self.process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, bufsize=1, env=env, cwd=os.getcwd()
                )
                
                time.sleep(1.0)  # 增加等待时间，让进程有足够时间输出错误信息
                if self.process.poll() is not None:
                    # 读取错误输出以获取退出原因
                    error_output = ""
                    stdout_output = ""
                    try:
                        if self.process.stderr:
                            error_output = self.process.stderr.read()
                        if self.process.stdout:
                            stdout_output = self.process.stdout.read()
                    except Exception as e:
                        self.logger.warning(f"读取进程输出时出错: {e}")
                    exit_code = self.process.returncode
                    self.logger.error(f"进程立即退出，退出码: {exit_code}")
                    if error_output:
                        self.logger.error(f"错误输出: {error_output[:500]}")
                    if stdout_output:
                        self.logger.error(f"标准输出: {stdout_output[:500]}")
                    # 保存错误信息以便后续查询
                    with self.lock:
                        if error_output:
                            self.error_buffer.append(f"进程退出 (code={exit_code}): {error_output[:200]}")
                    self.status = BotStatus.ERROR
                    return False
                
                self.status = BotStatus.RUNNING
                self.start_time = datetime.now()
                
                threading.Thread(target=self._read_stdout, daemon=True).start()
                threading.Thread(target=self._read_stderr, daemon=True).start()
                
                self.logger.info(f"套利进程启动 PID: {self.process.pid}")
                return True
            except Exception as e:
                self.logger.error(f"启动失败: {e}")
                self.status = BotStatus.ERROR
                return False
    
    def stop(self) -> bool:
        """停止套利进程"""
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                self.status = BotStatus.STOPPED
                self.process = None
                return True
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                self.status = BotStatus.STOPPED
                self.process = None
                self.logger.info("套利进程已停止")
                return True
            except Exception as e:
                self.logger.error(f"停止失败: {e}")
                return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取进程状态"""
        with self.lock:
            is_running = self.process is not None and self.process.poll() is None
            info = {
                "status": self.status.value,
                "running": is_running,
                "pid": self.process.pid if self.process else None,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "recent_output": self.output_buffer[-5:],
                "recent_errors": self.error_buffer[-5:]
            }
            if is_running and self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
                info["uptime_seconds"] = int(uptime)
            return info
    
    def _read_stdout(self):
        try:
            while self.process and self.process.stdout:
                line = self.process.stdout.readline()
                if line:
                    with self.lock:
                        self.output_buffer.append(line.strip())
                        if len(self.output_buffer) > 100:
                            self.output_buffer.pop(0)
                else:
                    break
        except Exception as e:
            self.logger.error(f"读取stdout错误: {e}")
    
    def _read_stderr(self):
        try:
            while self.process and self.process.stderr:
                line = self.process.stderr.readline()
                if line:
                    with self.lock:
                        self.error_buffer.append(line.strip())
                        if len(self.error_buffer) > 100:
                            self.error_buffer.pop(0)
                else:
                    break
        except Exception as e:
            self.logger.error(f"读取stderr错误: {e}")


class TelegramBotController:
    """Telegram机器人控制器 - 独立运行管理套利脚本"""
    
    def __init__(self, token: str):
        self.token = token
        self.process_manager: Optional[ArbitrageProcessManager] = None
        self.config = ArbitrageConfig()
        self.authorized_users: set = set()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def is_authorized(self, user_id: int) -> bool:
        if not self.authorized_users:
            return True
        return user_id in self.authorized_users
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text(f"❌ 未授权访问。您的ID: {user_id}")
            return
        keyboard = [
            ["▶️ 启动", "⏹️ 停止"],
            ["📊 状态", "⚙️ 配置"],
            ["📜 帮助"]
        ]
        await update.message.reply_text(
            f"🤖 *Lighter-Paradex 套利控制器*\n\n欢迎, {update.effective_user.first_name}!",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    
    async def cmd_run(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ 未授权")
            return
        if self.process_manager is None:
            self.process_manager = ArbitrageProcessManager(self.config)
        await update.message.chat.send_action(ChatAction.TYPING)
        if self.process_manager.start():
            await update.message.reply_text(f"✅ 套利脚本启动成功\nPID: {self.process_manager.process.pid}")
        else:
            # 获取错误信息
            status = self.process_manager.get_status()
            error_msg = "❌ 启动失败"
            if status.get('recent_errors'):
                error_details = '\n'.join(status['recent_errors'][-3:])
                # 限制错误信息长度
                if len(error_details) > 500:
                    error_details = error_details[:500] + "..."
                error_msg += f"\n\n错误信息:\n{error_details}"
            else:
                error_msg += "\n请检查日志文件或确保环境变量配置正确"
            await update.message.reply_text(error_msg)
    
    async def cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ 未授权")
            return
        if self.process_manager is None:
            await update.message.reply_text("❌ 没有运行中的进程")
            return
        if self.process_manager.stop():
            await update.message.reply_text("✅ 套利脚本已停止")
        else:
            await update.message.reply_text("❌ 停止失败")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ 未授权")
            return
        if self.process_manager is None:
            await update.message.reply_text("⚠️ 没有初始化进程。使用 /run 启动")
            return
        info = self.process_manager.get_status()
        text = f"""
📊 *套利脚本状态*
状态: {info['status'].upper()}
运行中: {'✅' if info['running'] else '❌'}
PID: {info['pid'] or 'N/A'}
"""
        if info.get('uptime_seconds'):
            h, m, s = info['uptime_seconds']//3600, (info['uptime_seconds']%3600)//60, info['uptime_seconds']%60
            text += f"运行时间: {h}h {m}m {s}s\n"
        if info['recent_output']:
            text += "\n📤 最近输出:\n"
            for line in info['recent_output'][-3:]:
                text += f"└ {line[:50]}...\n" if len(line) > 50 else f"└ {line}\n"
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            return
        await update.message.reply_text("""
📜 *帮助*
/run - 启动套利脚本
/stop - 停止套利脚本
/status - 查看状态
/config - 查看配置
        """, parse_mode='Markdown')
    
    async def cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            return
        text = f"""
⚙️ *配置*
脚本: {self.config.script_path}
交易对: {self.config.symbol}
数量: {self.config.size}
最大持仓: {self.config.max_position}
做多阈值: {self.config.long_threshold}
做空阈值: {self.config.short_threshold}
扫描间隔: {self.config.scan_interval}s
        """
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_authorized(update.effective_user.id):
            return
        text = update.message.text
        if "启动" in text or "▶️" in text:
            await self.cmd_run(update, context)
        elif "停止" in text or "⏹️" in text:
            await self.cmd_stop(update, context)
        elif "状态" in text or "📊" in text:
            await self.cmd_status(update, context)
        elif "配置" in text or "⚙️" in text:
            await self.cmd_config(update, context)
        elif "帮助" in text or "📜" in text:
            await self.cmd_help(update, context)
    
    def run(self):
        """运行机器人"""
        # 再次检查单实例（防止在检查后、启动前有新的实例启动）
        lock_file = Path('telegram_bot.lock')
        pid_file = Path('telegram_bot.pid')
        if lock_file.exists() and pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    saved_pid = int(f.read().strip())
                if saved_pid != os.getpid():
                    # 有其他进程的PID，检查是否还在运行
                    if sys.platform == 'win32':
                        result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {saved_pid}'],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                        )
                        if result.returncode == 0 and str(saved_pid) in result.stdout and 'python.exe' in result.stdout:
                            self.logger.error(f"检测到另一个实例正在运行 (PID: {saved_pid})，退出")
                            sys.exit(1)
            except:
                pass
        
        self.logger.info("启动Telegram控制器...")
        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("run", self.cmd_run))
        app.add_handler(CommandHandler("stop", self.cmd_stop))
        app.add_handler(CommandHandler("status", self.cmd_status))
        app.add_handler(CommandHandler("config", self.cmd_config))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        app.run_polling(allowed_updates=Update.ALL_TYPES)


# ============================================================
# 第三部分: 辅助函数
# ============================================================

async def start_telegram_control(token: str, chat_id: Optional[str] = None, 
                                 arbitrage_bot=None) -> Optional[TelegramBotControl]:
    """
    启动 Telegram 控制系统的快捷函数
    """
    if not TELEGRAM_AVAILABLE:
        logging.warning("python-telegram-bot 未安装")
        return None
    try:
        bot_control = TelegramBotControl(token, chat_id, arbitrage_bot)
        await bot_control.start()
        return bot_control
    except Exception as e:
        logging.error(f"启动 Telegram 控制失败: {e}")
        return None


def check_single_instance():
    """检查是否已有实例在运行，确保只有一个进程"""
    lock_file = Path('telegram_bot.lock')
    pid_file = Path('telegram_bot.pid')
    
    # 如果锁文件存在，检查对应的进程是否还在运行
    if lock_file.exists() and pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # 检查进程是否存在（Windows）
            try:
                if sys.platform == 'win32':
                    result = subprocess.run(
                        ['tasklist', '/FI', f'PID eq {old_pid}'],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                    # 检查是否在输出中找到进程（tasklist成功时会在输出中包含PID）
                    if result.returncode == 0 and str(old_pid) in result.stdout and 'python.exe' in result.stdout:
                        print(f"错误: 已有一个机器人实例在运行 (PID: {old_pid})")
                        print("请先停止现有实例，或删除 lock 文件: telegram_bot.lock")
                        print("提示: 可以运行 'taskkill /PID {old_pid} /F' 来停止该进程")
                        return False
            except Exception as e:
                # 如果检查失败，尝试删除旧文件并继续
                pass
            
            # 进程不存在，删除旧文件
            lock_file.unlink(missing_ok=True)
            pid_file.unlink(missing_ok=True)
        except (ValueError, FileNotFoundError):
            # PID 文件损坏或不存在，删除旧文件
            lock_file.unlink(missing_ok=True)
            pid_file.unlink(missing_ok=True)
    
    # 创建锁文件和 PID 文件
    try:
        lock_file.write_text('locked')
        pid_file.write_text(str(os.getpid()))
        
        # 注册退出时清理
        def cleanup():
            try:
                lock_file.unlink(missing_ok=True)
                pid_file.unlink(missing_ok=True)
            except:
                pass
        atexit.register(cleanup)
        
        return True
    except Exception as e:
        print(f"创建锁文件失败: {e}")
        return False


def main():
    """主入口 - 独立运行控制器"""
    # 检查单实例（必须在日志配置之前，避免日志文件冲突）
    if not check_single_instance():
        sys.exit(1)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('telegram_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("错误: 未设置 TELEGRAM_BOT_TOKEN 环境变量")
        sys.exit(1)
    
    authorized_users = os.getenv("AUTHORIZED_USERS", "")
    
    bot = TelegramBotController(token)
    if authorized_users:
        bot.authorized_users = set(int(uid.strip()) for uid in authorized_users.split(",") if uid.strip())
        print(f"已授权用户: {bot.authorized_users}")
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n机器人已停止")
        if bot.process_manager:
            bot.process_manager.stop()
    finally:
        # 清理锁文件
        lock_file = Path('telegram_bot.lock')
        pid_file = Path('telegram_bot.pid')
        lock_file.unlink(missing_ok=True)
        pid_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

