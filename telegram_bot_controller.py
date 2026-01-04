#!/usr/bin/env python3
"""
Telegram Bot Controller for Arbitrage Script
Controls arbitrage script execution with start, stop, status, and configure commands.
Manages the arbitrage process as a subprocess and sends real-time updates to the user.
"""

import os
import sys
import json
import logging
import subprocess
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

import telegram
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from telegram.constants import ChatAction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BotStatus(Enum):
    """Enum for bot status states"""
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ArbitrageConfig:
    """Configuration for arbitrage script"""
    script_path: str = "arbitrage_script.py"
    min_profit_threshold: float = 0.1
    check_interval: int = 60
    max_slippage: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArbitrageConfig':
        return cls(**{k: v for k, v in data.items() if k in asdict(cls())})


class ArbitrageProcessManager:
    """Manages the arbitrage subprocess"""
    
    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.status = BotStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.output_buffer: list = []
        self.error_buffer: list = []
        self.lock = threading.Lock()
    
    def start(self) -> bool:
        """Start the arbitrage subprocess"""
        with self.lock:
            if self.process is not None and self.process.poll() is None:
                logger.warning("Process already running")
                return False
            
            try:
                # Check if script exists
                if not os.path.exists(self.config.script_path):
                    logger.error(f"Script not found: {self.config.script_path}")
                    self.status = BotStatus.ERROR
                    return False
                
                # Start subprocess with arguments
                cmd = [
                    sys.executable,
                    self.config.script_path,
                    f"--min-profit={self.config.min_profit_threshold}",
                    f"--check-interval={self.config.check_interval}",
                    f"--max-slippage={self.config.max_slippage}"
                ]
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                self.status = BotStatus.RUNNING
                self.start_time = datetime.utcnow()
                
                # Start threads to capture output
                threading.Thread(target=self._read_stdout, daemon=True).start()
                threading.Thread(target=self._read_stderr, daemon=True).start()
                
                logger.info(f"Arbitrage process started with PID: {self.process.pid}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start process: {e}")
                self.status = BotStatus.ERROR
                return False
    
    def stop(self) -> bool:
        """Stop the arbitrage subprocess"""
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                logger.warning("No running process to stop")
                self.status = BotStatus.STOPPED
                return False
            
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                
                self.status = BotStatus.STOPPED
                logger.info("Arbitrage process stopped")
                return True
                
            except Exception as e:
                logger.error(f"Error stopping process: {e}")
                self.status = BotStatus.ERROR
                return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the process"""
        with self.lock:
            is_running = self.process is not None and self.process.poll() is None
            
            status_info = {
                "status": self.status.value,
                "running": is_running,
                "pid": self.process.pid if self.process else None,
                "start_time": self.start_time.isoformat() if self.start_time else None,
            }
            
            if is_running and self.start_time:
                uptime = datetime.utcnow() - self.start_time
                status_info["uptime_seconds"] = int(uptime.total_seconds())
            
            status_info["recent_output"] = self.output_buffer[-5:] if self.output_buffer else []
            status_info["recent_errors"] = self.error_buffer[-5:] if self.error_buffer else []
            
            return status_info
    
    def _read_stdout(self):
        """Read stdout from subprocess"""
        try:
            while self.process and self.process.stdout:
                line = self.process.stdout.readline()
                if line:
                    with self.lock:
                        self.output_buffer.append(line.strip())
                        # Keep only last 100 lines
                        if len(self.output_buffer) > 100:
                            self.output_buffer.pop(0)
                else:
                    break
        except Exception as e:
            logger.error(f"Error reading stdout: {e}")
    
    def _read_stderr(self):
        """Read stderr from subprocess"""
        try:
            while self.process and self.process.stderr:
                line = self.process.stderr.readline()
                if line:
                    with self.lock:
                        self.error_buffer.append(line.strip())
                        # Keep only last 100 lines
                        if len(self.error_buffer) > 100:
                            self.error_buffer.pop(0)
                else:
                    break
        except Exception as e:
            logger.error(f"Error reading stderr: {e}")


class TelegramBotController:
    """Telegram bot controller for arbitrage script"""
    
    # Conversation states
    CONFIGURE_MENU = 1
    CONFIGURE_PROFIT = 2
    CONFIGURE_INTERVAL = 3
    CONFIGURE_SLIPPAGE = 4
    
    def __init__(self, token: str, config_file: str = "bot_config.json"):
        self.token = token
        self.config_file = config_file
        self.process_manager: Optional[ArbitrageProcessManager] = None
        self.user_configs: Dict[int, ArbitrageConfig] = {}
        self.authorized_users: set = set()
        self.load_config()
    
    def load_config(self):
        """Load bot configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.authorized_users = set(data.get("authorized_users", []))
                    logger.info(f"Loaded config with {len(self.authorized_users)} authorized users")
            else:
                logger.info("No config file found, starting fresh")
                self.authorized_users = set()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def save_config(self):
        """Save bot configuration to file"""
        try:
            data = {
                "authorized_users": list(self.authorized_users)
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Config saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id in self.authorized_users
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user = update.effective_user
        user_id = user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text(
                f"❌ Unauthorized access. User ID {user_id} is not authorized.\n"
                f"Contact the bot administrator for access."
            )
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            return
        
        keyboard = [
            ["▶️ Start", "⏹️ Stop"],
            ["📊 Status", "⚙️ Configure"],
            ["📜 Help"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        welcome_text = (
            f"🤖 Welcome to Arbitrage Bot, {user.first_name}!\n\n"
            f"Available commands:\n"
            f"▶️ Start - Start the arbitrage script\n"
            f"⏹️ Stop - Stop the arbitrage script\n"
            f"📊 Status - View current status\n"
            f"⚙️ Configure - Configure parameters\n"
            f"📜 Help - Show help information"
        )
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        help_text = (
            "🤖 Arbitrage Bot Help\n\n"
            "Available Commands:\n"
            "▶️ /start - Start arbitrage script\n"
            "⏹️ /stop - Stop arbitrage script\n"
            "📊 /status - Check bot and script status\n"
            "⚙️ /configure - Configure bot parameters\n"
            "📜 /help - Show this help message\n\n"
            "Configuration Parameters:\n"
            "• Min Profit Threshold: Minimum profit % to trigger arbitrage\n"
            "• Check Interval: Seconds between market checks\n"
            "• Max Slippage: Maximum acceptable slippage %\n\n"
            "Status Information:\n"
            "• Process status (running/stopped)\n"
            "• Process ID and uptime\n"
            "• Recent output and errors\n"
            "• Current configuration"
        )
        
        await update.message.reply_text(help_text)
    
    async def start_arbitrage(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle start command"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        user_id = update.effective_user.id
        
        if self.process_manager is None:
            config = self.user_configs.get(user_id, ArbitrageConfig())
            self.process_manager = ArbitrageProcessManager(config)
        
        await update.message.chat.send_action(ChatAction.TYPING)
        
        if self.process_manager.start():
            await update.message.reply_text(
                "✅ Arbitrage script started successfully!\n"
                f"PID: {self.process_manager.process.pid}\n"
                f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            logger.info(f"Arbitrage started by user {user_id}")
        else:
            await update.message.reply_text(
                "❌ Failed to start arbitrage script.\n"
                "Check logs for details."
            )
    
    async def stop_arbitrage(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle stop command"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        user_id = update.effective_user.id
        
        if self.process_manager is None:
            await update.message.reply_text("❌ No process is running.")
            return
        
        await update.message.chat.send_action(ChatAction.TYPING)
        
        if self.process_manager.stop():
            await update.message.reply_text(
                "✅ Arbitrage script stopped successfully!\n"
                f"Stopped at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            logger.info(f"Arbitrage stopped by user {user_id}")
        else:
            await update.message.reply_text(
                "❌ Failed to stop arbitrage script.\n"
                "Process may have already terminated."
            )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle status command"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        await update.message.chat.send_action(ChatAction.TYPING)
        
        if self.process_manager is None:
            status_text = "⚠️ No process manager initialized. Use /start to begin."
        else:
            status_info = self.process_manager.get_status()
            
            status_text = "📊 Arbitrage Bot Status\n\n"
            status_text += f"Status: {status_info['status'].upper()}\n"
            status_text += f"Running: {'✅ Yes' if status_info['running'] else '❌ No'}\n"
            
            if status_info['pid']:
                status_text += f"PID: {status_info['pid']}\n"
            
            if status_info['start_time']:
                status_text += f"Started: {status_info['start_time']}\n"
            
            if 'uptime_seconds' in status_info:
                uptime = status_info['uptime_seconds']
                hours = uptime // 3600
                minutes = (uptime % 3600) // 60
                seconds = uptime % 60
                status_text += f"Uptime: {hours}h {minutes}m {seconds}s\n"
            
            status_text += "\n⚙️ Configuration:\n"
            config = self.user_configs.get(update.effective_user.id, 
                                          (self.process_manager.config if self.process_manager else ArbitrageConfig()))
            status_text += f"Min Profit: {config.min_profit_threshold}%\n"
            status_text += f"Check Interval: {config.check_interval}s\n"
            status_text += f"Max Slippage: {config.max_slippage}%\n"
            
            if status_info['recent_output']:
                status_text += "\n📤 Recent Output:\n"
                for line in status_info['recent_output'][-3:]:
                    status_text += f"└ {line[:60]}...\n" if len(line) > 60 else f"└ {line}\n"
            
            if status_info['recent_errors']:
                status_text += "\n⚠️ Recent Errors:\n"
                for line in status_info['recent_errors'][-3:]:
                    status_text += f"└ {line[:60]}...\n" if len(line) > 60 else f"└ {line}\n"
        
        await update.message.reply_text(status_text)
    
    async def configure(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle configure command"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized access.")
            return ConversationHandler.END
        
        user_id = update.effective_user.id
        current_config = self.user_configs.get(user_id, ArbitrageConfig())
        
        keyboard = [
            [f"💰 Min Profit ({current_config.min_profit_threshold}%)"],
            [f"⏱️ Check Interval ({current_config.check_interval}s)"],
            [f"📉 Max Slippage ({current_config.max_slippage}%)"],
            ["❌ Cancel"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "⚙️ Configure Parameters\n\n"
            "Select a parameter to modify:",
            reply_markup=reply_markup
        )
        
        return self.CONFIGURE_MENU
    
    async def configure_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle configuration menu selection"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized access.")
            return ConversationHandler.END
        
        text = update.message.text
        
        if "Min Profit" in text:
            await update.message.reply_text(
                "Enter minimum profit threshold (%):\n"
                "Example: 0.5 for 0.5%",
                reply_markup=ReplyKeyboardRemove()
            )
            return self.CONFIGURE_PROFIT
        elif "Check Interval" in text:
            await update.message.reply_text(
                "Enter check interval (seconds):\n"
                "Example: 60 for every 60 seconds",
                reply_markup=ReplyKeyboardRemove()
            )
            return self.CONFIGURE_INTERVAL
        elif "Max Slippage" in text:
            await update.message.reply_text(
                "Enter maximum slippage (%):\n"
                "Example: 0.5 for 0.5%",
                reply_markup=ReplyKeyboardRemove()
            )
            return self.CONFIGURE_SLIPPAGE
        elif "Cancel" in text:
            await update.message.reply_text(
                "Configuration cancelled.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text("Invalid option. Please try again.")
            return self.CONFIGURE_MENU
    
    async def configure_profit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle profit threshold configuration"""
        try:
            value = float(update.message.text)
            user_id = update.effective_user.id
            
            if user_id not in self.user_configs:
                self.user_configs[user_id] = ArbitrageConfig()
            
            self.user_configs[user_id].min_profit_threshold = value
            
            if self.process_manager:
                self.process_manager.config.min_profit_threshold = value
            
            await update.message.reply_text(
                f"✅ Minimum profit threshold set to {value}%\n"
                f"Note: Changes will apply to new processes.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ Invalid value. Please enter a number.")
            return self.CONFIGURE_PROFIT
    
    async def configure_interval(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle interval configuration"""
        try:
            value = int(update.message.text)
            user_id = update.effective_user.id
            
            if user_id not in self.user_configs:
                self.user_configs[user_id] = ArbitrageConfig()
            
            self.user_configs[user_id].check_interval = value
            
            if self.process_manager:
                self.process_manager.config.check_interval = value
            
            await update.message.reply_text(
                f"✅ Check interval set to {value} seconds\n"
                f"Note: Changes will apply to new processes.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ Invalid value. Please enter an integer.")
            return self.CONFIGURE_INTERVAL
    
    async def configure_slippage(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle slippage configuration"""
        try:
            value = float(update.message.text)
            user_id = update.effective_user.id
            
            if user_id not in self.user_configs:
                self.user_configs[user_id] = ArbitrageConfig()
            
            self.user_configs[user_id].max_slippage = value
            
            if self.process_manager:
                self.process_manager.config.max_slippage = value
            
            await update.message.reply_text(
                f"✅ Maximum slippage set to {value}%\n"
                f"Note: Changes will apply to new processes.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ Invalid value. Please enter a number.")
            return self.CONFIGURE_SLIPPAGE
    
    async def cancel_configure(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel configuration"""
        await update.message.reply_text(
            "Configuration cancelled.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages and route to appropriate handler"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized access.")
            return
        
        text = update.message.text.lower()
        
        if "start" in text or "▶️" in text:
            await self.start_arbitrage(update, context)
        elif "stop" in text or "⏹️" in text:
            await self.stop_arbitrage(update, context)
        elif "status" in text or "📊" in text:
            await self.status(update, context)
        elif "configure" in text or "⚙️" in text:
            await self.configure(update, context)
        elif "help" in text or "📜" in text:
            await self.help_command(update, context)
        else:
            await update.message.reply_text(
                "Unknown command. Use /help for available commands."
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Telegram Bot Controller...")
        
        application = Application.builder().token(self.token).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("stop", self.stop_arbitrage))
        application.add_handler(CommandHandler("status", self.status))
        
        # Add configuration conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("configure", self.configure)],
            states={
                self.CONFIGURE_MENU: [MessageHandler(filters.TEXT, self.configure_menu)],
                self.CONFIGURE_PROFIT: [MessageHandler(filters.TEXT, self.configure_profit)],
                self.CONFIGURE_INTERVAL: [MessageHandler(filters.TEXT, self.configure_interval)],
                self.CONFIGURE_SLIPPAGE: [MessageHandler(filters.TEXT, self.configure_slippage)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_configure)]
        )
        application.add_handler(conv_handler)
        
        # Add text message handler (for button clicks)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        # Start polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    # Get token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)
    
    # Optional: Get authorized users from environment variable (comma-separated)
    authorized_users = os.getenv("AUTHORIZED_USERS", "")
    
    # Create and run bot
    bot = TelegramBotController(token)
    
    # Load authorized users if provided
    if authorized_users:
        bot.authorized_users = set(int(uid.strip()) for uid in authorized_users.split(",") if uid.strip())
        bot.save_config()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        if bot.process_manager:
            bot.process_manager.stop()


if __name__ == "__main__":
    main()
