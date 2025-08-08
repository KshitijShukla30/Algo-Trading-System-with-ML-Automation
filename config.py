"""Configuration file for the algo trading system"""

# Stock symbols for NIFTY 50
STOCK_SYMBOLS = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS','SBIN.NS','LICI.NS','HINDUNILVR.NS']  # Fixed: HDFC.NS → HDFCBANK.NS

# Trading parameters
# Enhanced strategy parameters
RSI_OVERSOLD_STRICT = 30
RSI_OVERBOUGHT_STRICT = 70

# Working original
RSI_OVERSOLD_WORKING = 40
RSI_OVERBOUGHT_WORKING = 60

# Balanced approach
RSI_OVERSOLD_BALANCED = 35
RSI_OVERBOUGHT_BALANCED = 65
SMA_SHORT = 20
SMA_LONG = 50

# Additional parameters for enhanced strategy
VOLUME_THRESHOLD = 1.2  # 20% above average volume
BB_PERIOD = 20
BB_STD = 2

# Backtest parameters
BACKTEST_PERIOD = '6mo'  # Default period
INITIAL_CAPITAL = 100000  # 1 Lakh

# Google Sheets configuration
GOOGLE_SHEETS_NAME = "AlgoTrading_Portfolio"        
GOOGLE_CREDENTIALS_FILE = "credentials.json"        
# Telegram Bot configuration
TELEGRAM_BOT_TOKEN = "enter your token"
TELEGRAM_CHAT_ID = "user number"

# ML Model parameters
ML_FEATURES = ['RSI', 'MACD', 'MACD_signal', 'BB_upper', 'BB_lower', 'Volume_SMA', 'Price_Change']
