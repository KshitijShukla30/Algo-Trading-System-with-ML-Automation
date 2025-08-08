"""Telegram bot integration for alerts"""
import asyncio
import pandas as pd
from telegram import Bot
from telegram.error import TelegramError
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramAlerter:
    def __init__(self, bot_token: str = TELEGRAM_BOT_TOKEN, chat_id: str = TELEGRAM_CHAT_ID):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token) if bot_token != "YOUR_BOT_TOKEN_HERE" else None
    
    async def send_message(self, message: str):
        """Send message to Telegram chat"""
        if not self.bot:
            logger.warning("Telegram bot not configured")
            return
        
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            logger.info("Telegram alert sent successfully")
        except TelegramError as e:
            logger.error(f"Error sending Telegram alert: {str(e)}")
    
    def send_alert(self, message: str):
        """Send alert (synchronous wrapper)"""
        if not self.bot:
            return
        
        try:
            asyncio.run(self.send_message(message))
        except Exception as e:
            logger.error(f"Error in send_alert: {str(e)}")
    
    def send_trade_alert(self, symbol: str, action: str, price: float, signal_strength: str = "Medium"):
        """Send formatted trade alert"""
        message = f"""
🚨 Trading Alert 🚨

Symbol: {symbol}
Action: {action}
Price: ₹{price:.2f}
Signal Strength: {signal_strength}
Time: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.send_alert(message.strip())
    
    def send_error_alert(self, error_message: str):
        """Send error notification"""
        message = f"❌ Error in Algo Trading System:\n{error_message}"
        self.send_alert(message)
