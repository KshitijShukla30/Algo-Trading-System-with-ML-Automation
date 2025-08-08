"""Trading strategy implementation"""
import pandas as pd
import numpy as np
import ta
from typing import Tuple, List
import logging
from config import (
    RSI_OVERSOLD_WORKING, RSI_OVERBOUGHT_WORKING,
    SMA_SHORT, SMA_LONG, INITIAL_CAPITAL
)
RSI_OVERSOLD = RSI_OVERSOLD_WORKING  # 40
RSI_OVERBOUGHT = RSI_OVERBOUGHT_WORKING
logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self, initial_capital: float = INITIAL_CAPITAL):
        self.initial_capital = initial_capital
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added technical indicators
        """
        df = df.copy()
        
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=SMA_SHORT).mean()
        df['SMA_50'] = df['Close'].rolling(window=SMA_LONG).mean()
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_histogram'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['Close'])
        df['BB_upper'] = bb.bollinger_hband()
        df['BB_lower'] = bb.bollinger_lband()
        df['BB_middle'] = bb.bollinger_mavg()
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        
        # Price change
        df['Price_Change'] = df['Close'].pct_change()
        
        return df
    def generate_signals(self, df: pd.DataFrame, strategy_type: str = "working_original") -> pd.DataFrame:
        """
        Trading strategy with strategy type parameter
            """
        try:
            # Add all technical indicators (same as before)
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            df['SMA_20'] = ta.trend.SMAIndicator(df['Close'], window=20).sma_indicator()
            df['SMA_50'] = ta.trend.SMAIndicator(df['Close'], window=50).sma_indicator()

            # MACD for ML features
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_signal'] = macd.macd_signal()

            # Bollinger Bands for ML features
            bollinger = ta.volatility.BollingerBands(df['Close'])
            df['BB_upper'] = bollinger.bollinger_hband()
            df['BB_lower'] = bollinger.bollinger_lband()

            # Volume SMA
            df['Volume_SMA'] = ta.trend.SMAIndicator(df['Volume'], window=20).sma_indicator()
            df['Price_Change'] = df['Close'].pct_change()

            # STRATEGY SELECTION BASED ON PARAMETER
            if strategy_type == "assignment_compliant":
                # OPTION 1: Exact Assignment Requirements (RSI < 30 + Uptrend)
                buy_condition = (df['RSI'] < 30) & (df['SMA_20'] > df['SMA_50'])
                sell_condition = (df['RSI'] > 70) | (df['SMA_20'] < df['SMA_50'])

            elif strategy_type == "working_original":
                # OPTION 2: Your Previously Successful Strategy (Simple RSI)
                buy_condition = (df['RSI'] < 40)
                sell_condition = (df['RSI'] > 60)

            elif strategy_type == "balanced":
                # OPTION 3: Balanced Approach (RSI < 35 + Uptrend)
                buy_condition = (df['RSI'] < 35) & (df['SMA_20'] > df['SMA_50'])
                sell_condition = (df['RSI'] > 65)

            else:
                # Default to working original
                buy_condition = (df['RSI'] < 40)
                sell_condition = (df['RSI'] > 60)

            # Create signals
            df['Signal'] = 0
            df.loc[buy_condition, 'Signal'] = 1   # Buy signal
            df.loc[sell_condition, 'Signal'] = -1 # Sell signal

            # Forward fill positions
            df['Position'] = df['Signal'].replace({0: np.nan}).ffill().fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error in generate_signals: {str(e)}")
            df['Signal'] = 0
            df['Position'] = 0
            return df

    # def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
    #     """
    #     Enhanced multi-indicator trading strategy
    #     """
    #     try:
    #         # Add technical indicators directly in this method
    #         # RSI
    #         df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    #
    #         # Moving Averages
    #         df['SMA_20'] = ta.trend.SMAIndicator(df['Close'], window=SMA_SHORT).sma_indicator()
    #         df['SMA_50'] = ta.trend.SMAIndicator(df['Close'], window=SMA_LONG).sma_indicator()
    #
    #         # MACD
    #         macd = ta.trend.MACD(df['Close'])
    #         df['MACD'] = macd.macd()
    #         df['MACD_signal'] = macd.macd_signal()
    #
    #         # Bollinger Bands
    #         bollinger = ta.volatility.BollingerBands(df['Close'])
    #         df['BB_upper'] = bollinger.bollinger_hband()
    #         df['BB_lower'] = bollinger.bollinger_lband()
    #
    #         # Volume SMA
    #         df['Volume_SMA'] = ta.trend.SMAIndicator(df['Volume'], window=20).sma_indicator()
    #
    #         # Trend confirmation using SMAs
    #         bullish_trend = df['SMA_20'] > df['SMA_50']
    #         bearish_trend = df['SMA_20'] < df['SMA_50']
    #
    #         # Momentum confirmation using MACD
    #         macd_bullish = (df['MACD'] > df['MACD_signal']) & (df['MACD'].shift(1) <= df['MACD_signal'].shift(1))
    #         macd_bearish = (df['MACD'] < df['MACD_signal']) & (df['MACD'].shift(1) >= df['MACD_signal'].shift(1))
    #
    #         # Volume confirmation
    #         high_volume = df['Volume'] > df['Volume_SMA']
    #
    #         # Enhanced buy conditions (multiple confirmations)
    #         buy_condition = (
    #                                 (df['RSI'] < RSI_OVERSOLD) &          # Oversold condition
    #                                 bullish_trend &                        # Uptrend confirmation
    #                                 (df['Close'] > df['BB_lower']) &      # Above lower Bollinger Band
    #                                 high_volume                            # Volume confirmation
    #                         ) | (
    #                             # Alternative: Strong MACD signal even if RSI not oversold
    #                                 macd_bullish &
    #                                 bullish_trend &
    #                                 (df['RSI'] < 50) &                    # Not overbought
    #                                 high_volume
    #                         )
    #
    #         # Enhanced sell conditions (multiple confirmations)
    #         sell_condition = (
    #                                  (df['RSI'] > RSI_OVERBOUGHT) &        # Overbought condition
    #                                  bearish_trend &                        # Downtrend confirmation
    #                                  (df['Close'] < df['BB_upper'])        # Below upper Bollinger Band
    #                          ) | (
    #                              # Alternative: Strong MACD sell signal
    #                                  macd_bearish &
    #                                  bearish_trend &
    #                                  (df['RSI'] > 50)                      # Not oversold
    #                          ) | (
    #                              # Risk management: Strong reversal signals
    #                                  (df['RSI'] > 75) &                    # Extremely overbought
    #                                  (df['Close'] < df['BB_upper'])        # Price rejection at upper band
    #                          )
    #
    #         # Create signals
    #         df['Signal'] = 0
    #         df.loc[buy_condition, 'Signal'] = 1   # Buy signal
    #         df.loc[sell_condition, 'Signal'] = -1 # Sell signal
    #
    #         # Forward fill positions
    #         df['Position'] = df['Signal'].replace(0).ffill()
    #
    #         return df
    #
    #     except Exception as e:
    #         logger.error(f"Error in generate_signals: {str(e)}")
    #         # Return dataframe with basic signal structure if there's an error
    #         df['Signal'] = 0
    #         df['Position'] = 0
    #         return df

    # def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
    #     """
    #     Generate buy/sell signals based on strategy
    #
    #     Args:
    #         df: DataFrame with indicators
    #
    #     Returns:
    #         DataFrame with signals
    #     """
    #     try:
    #     # Calculate all technical indicators first
    #         df = self.add_technical_indicators(df)
    #
    #     # Trend confirmation using SMAs
    #         bullish_trend = df['SMA_20'] > df['SMA_50']
    #         bearish_trend = df['SMA_20'] < df['SMA_50']
    #
    #     # Momentum confirmation using MACD
    #         macd_bullish = (df['MACD'] > df['MACD_signal']) & (df['MACD'].shift(1) <= df['MACD_signal'].shift(1))
    #         macd_bearish = (df['MACD'] < df['MACD_signal']) & (df['MACD'].shift(1) >= df['MACD_signal'].shift(1))
    #
    #     # Volume confirmation
    #         high_volume = df['Volume'] > df['Volume_SMA']
    #
    #     # Enhanced buy conditions (multiple confirmations)
    #         buy_condition = (
    #             (df['RSI'] < RSI_OVERSOLD) &          # Oversold condition
    #             bullish_trend &                        # Uptrend confirmation
    #             (df['Close'] > df['BB_lower']) &      # Above lower Bollinger Band
    #             high_volume                            # Volume confirmation
    #         ) | (
    #                         # Alternative: Strong MACD signal even if RSI not oversold
    #             macd_bullish &
    #             bullish_trend &
    #             (df['RSI'] < 50) &                    # Not overbought
    #             high_volume
    #             )
    #
    #     # Enhanced sell conditions (multiple confirmations)
    #         sell_condition = (
    #             (df['RSI'] > RSI_OVERBOUGHT) &        # Overbought condition
    #             bearish_trend &                        # Downtrend confirmation
    #             (df['Close'] < df['BB_upper'])        # Below upper Bollinger Band
    #             ) | (
    #                          # Alternative: Strong MACD sell signal
    #             macd_bearish &
    #             bearish_trend &
    #             (df['RSI'] > 50)                      # Not oversold
    #             ) | (
    #                          # Risk management: Strong reversal signals
    #                 (df['RSI'] > 75) &                    # Extremely overbought
    #                 (df['Close'] < df['BB_upper'])        # Price rejection at upper band
    #     )
    #
    #     # Create signals
    #     df['Signal'] = 0
    #     df.loc[buy_condition, 'Signal'] = 1   # Buy signal
    #     df.loc[sell_condition, 'Signal'] = -1 # Sell signal
    #
    #     # Forward fill positions
    #     df['Position'] = df['Signal'].replace(0).ffill()
    #
    #     return df

    # except Exception as e:
    #     logger.error(f"Error in generate_signals: {str(e)}")
    #     return df
        # df = df.copy()
        #
        # # Initialize signal columns
        # df['Signal'] = 0
        # df['Position'] = 0
        #
        # # Buy signal: RSI < 30 AND 20-SMA crosses above 50-SMA
        # # buy_condition = (
        # #     (df['RSI'] < RSI_OVERSOLD) &
        # #     (df['SMA_20'] > df['SMA_50']) &
        # #     (df['SMA_20'].shift(1) <= df['SMA_50'].shift(1))
        # # )
        # #
        # # # Sell signal: RSI > 70 OR 20-SMA crosses below 50-SMA
        # # sell_condition = (
        # #     (df['RSI'] > RSI_OVERBOUGHT) |
        # #     ((df['SMA_20'] < df['SMA_50']) &
        # #      (df['SMA_20'].shift(1) >= df['SMA_50'].shift(1)))
        # # )
        # buy_condition = (df['RSI'] < RSI_OVERSOLD)  # RSI < 40
        # sell_condition = (df['RSI'] > RSI_OVERBOUGHT)  # RSI > 60
        # df.loc[buy_condition, 'Signal'] = 1
        # df.loc[sell_condition, 'Signal'] = -1
        #
        # # Calculate positions
        # df['Position'] = df['Signal'].replace(to_replace=0).ffill()
        # df['Position'] = df['Position'].fillna(0)
        #
        # return df
    
    def backtest_strategy(self, df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, dict]:
        """
        Backtest the trading strategy
        
        Args:
            df: DataFrame with signals
            symbol: Stock symbol
            
        Returns:
            Tuple of (trades_df, performance_metrics)
        """
        df = df.copy()
        
        # Initialize tracking variables
        position = 0
        entry_price = 0
        trades = []
        portfolio_value = self.initial_capital
        
        for i in range(len(df)):
            current_price = df.iloc[i]['Close']
            signal = df.iloc[i]['Signal']
            date = df.iloc[i]['Date']
            
            if signal == 1 and position == 0:  # Buy signal
                position = portfolio_value / current_price
                entry_price = current_price
                portfolio_value = 0
                
                trades.append({
                    'Date': date,
                    'Symbol': symbol,
                    'Action': 'BUY',
                    'Price': current_price,
                    'Quantity': position,
                    'Value': position * current_price
                })
                
            elif signal == -1 and position > 0:  # Sell signal
                portfolio_value = position * current_price
                pnl = (current_price - entry_price) * position
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                trades.append({
                    'Date': date,
                    'Symbol': symbol,
                    'Action': 'SELL',
                    'Price': current_price,
                    'Quantity': position,
                    'Value': portfolio_value,
                    'PnL': pnl,
                    'PnL_pct': pnl_pct
                })
                
                position = 0
                entry_price = 0
        
        # Create trades DataFrame
        trades_df = pd.DataFrame(trades)
        
        # Calculate performance metrics
        if len(trades_df) > 0:
            total_trades = len(trades_df[trades_df['Action'] == 'SELL'])
            winning_trades = len(trades_df[(trades_df['Action'] == 'SELL') & (trades_df['PnL'] > 0)])
            win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
            total_pnl = trades_df[trades_df['Action'] == 'SELL']['PnL'].sum() if 'PnL' in trades_df.columns else 0
        else:
            total_trades = 0
            winning_trades = 0
            win_rate = 0
            total_pnl = 0
        
        performance_metrics = {
            'Symbol': symbol,
            'Total_Trades': total_trades,
            'Winning_Trades': winning_trades,
            'Win_Rate': win_rate,
            'Total_PnL': total_pnl,
            'Final_Portfolio_Value': portfolio_value if portfolio_value > 0 else self.initial_capital + total_pnl
        }
        
        return trades_df, performance_metrics
