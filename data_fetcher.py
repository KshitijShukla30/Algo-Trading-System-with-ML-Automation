import yfinance as yf
import pandas as pd
import logging 
from typing import Dict,List
from config import STOCK_SYMBOLS,BACKTEST_PERIOD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self,symbols:List[str]=STOCK_SYMBOLS):
        self.symbols=symbols
    
    def fetch_data(self,period:str =BACKTEST_PERIOD)-> Dict[str,pd.DataFrame]:
        data = {}
        for symbol in self.symbols:
            try:
                logger.info(f"Fetching data for {symbol}")
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period)
                if df.empty:
                    logger.warning(f"No data for {symbol}")
                    continue
                df.reset_index(inplace=True)
                data[symbol] = df
                logger.info(f"Successfully fetched {len(df)} rows for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")

        return data
    def get_latest_data(self,symbol : str ,period : str = "5d") -> pd.DataFrame:
       try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            df.reset_index(inplace=True)
            return df
       except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()