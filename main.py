"""Main execution file for the algo trading system"""
import pandas as pd
import logging
from datetime import datetime
import time
from data_fetcher import DataFetcher
from strategy import TradingStrategy
from ml_model import MLPredictor
from sheets_logger import SheetsLogger
from telegram_alerts import TelegramAlerter
from config import STOCK_SYMBOLS, BACKTEST_PERIOD, INITIAL_CAPITAL

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('algo_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlgoTradingSystem:
    def __init__(self,strategy_type="working_original"):
        self.data_fetcher = DataFetcher()
        self.strategy = TradingStrategy()
        self.ml_predictor = MLPredictor()
        self.sheets_logger = SheetsLogger()
        self.telegram_alerter = TelegramAlerter()
        self.strategy_type = strategy_type

    def run_backtest(self, period=None):
        """Run complete backtesting pipeline"""
        backtest_period = period if period else BACKTEST_PERIOD
        logger.info(f"Starting backtesting pipeline for period: {backtest_period}...")
        logger.info(f"Using strategy: {self.strategy_type}")

        try:
            # Fetch historical data
            stock_data = self.data_fetcher.fetch_data(period=backtest_period)

            all_trades = []
            all_performance = []
            all_signals = []

            for symbol, df in stock_data.items():
                logger.info(f"Processing {symbol}...")

                # Generate signals (includes indicator calculation)
                df_with_signals = self.strategy.generate_signals(df, strategy_type=self.strategy_type)

                # Backtest strategy
                trades_df, performance_metrics = self.strategy.backtest_strategy(df_with_signals, symbol)

                # Prepare ML features and train model
                df_ml_ready = self.ml_predictor.prepare_features(df_with_signals)
                if not df_ml_ready.empty:
                    ml_results = self.ml_predictor.train_model(df_ml_ready)
                    if ml_results:
                        self.sheets_logger.log_ml_results(ml_results)

                # Get latest signals
                latest_signals = self.get_latest_signals(df_with_signals, symbol)

                # Store results
                if not trades_df.empty:
                    all_trades.append(trades_df)
                all_performance.append(performance_metrics)
                all_signals.extend(latest_signals)

                # Send alerts for strong signals
                self.send_signal_alerts(latest_signals)

            # Log to Google Sheets
            self.log_results_to_sheets(all_trades, all_performance, all_signals)

            # Print summary
            summary_results = self.print_summary(all_performance)

            return summary_results

        except Exception as e:
            error_msg = f"Error in backtesting pipeline: {str(e)}"
            logger.error(error_msg)
            self.telegram_alerter.send_error_alert(error_msg)
            return None

    def get_latest_signals(self, df: pd.DataFrame, symbol: str) -> list:
        """Get latest trading signals"""
        latest_data = df.tail(5)  # Get last 5 days
        signals = []

        for idx, row in latest_data.iterrows():
            if row.get('Signal', 0) != 0:
                # Handle date properly
                if hasattr(row.name, 'strftime'):
                    date_str = row.name.strftime('%Y-%m-%d')
                elif 'Date' in row and hasattr(row['Date'], 'strftime'):
                    date_str = row['Date'].strftime('%Y-%m-%d')
                else:
                    date_str = str(idx)

                signal_data = {
                    'Date': date_str,
                    'Symbol': symbol,
                    'Signal': 'BUY' if row['Signal'] == 1 else 'SELL',
                    'Price': row['Close'],
                    'RSI': row.get('RSI', 0),
                    'SMA_20': row.get('SMA_20', 0),
                    'SMA_50': row.get('SMA_50', 0),
                    'ML_Prediction': 'N/A'
                }
                signals.append(signal_data)

        return signals

    def send_signal_alerts(self, signals: list):
        """Send Telegram alerts for trading signals"""
        for signal in signals:
            if signal['Signal'] in ['BUY', 'SELL']:
                try:
                    self.telegram_alerter.send_trade_alert(
                        symbol=signal['Symbol'],
                        action=signal['Signal'],
                        price=signal['Price']
                    )
                except Exception as e:
                    logger.warning(f"Failed to send telegram alert: {e}")

    def log_results_to_sheets(self, all_trades: list, all_performance: list, all_signals: list):
        """Log all results to Google Sheets"""
        try:
            # Combine all trades
            if all_trades:
                combined_trades = pd.concat([df for df in all_trades if not df.empty], ignore_index=True)
                if not combined_trades.empty:
                    self.sheets_logger.log_trades(combined_trades)

            # Log performance summary
            if all_performance:
                self.sheets_logger.log_summary(all_performance)

            # Log signals
            if all_signals:
                self.sheets_logger.log_signals(all_signals)

            logger.info("Successfully logged all results to Google Sheets")
        except Exception as e:
            logger.error(f"Error logging to sheets: {str(e)}")

    def print_summary(self, all_performance: list):
        """Print performance summary to console"""
        print("\n" + "="*60)
        print("BACKTESTING RESULTS SUMMARY")
        print("="*60)

        total_pnl = 0
        total_trades = 0
        total_winning_trades = 0

        for performance in all_performance:
            symbol = performance.get('Symbol', 'UNKNOWN')
            trades = performance.get('Total_Trades', 0)
            win_rate = performance.get('Win_Rate', 0)
            pnl = performance.get('Total_PnL', 0)
            winning_trades = performance.get('Winning_Trades', 0)

            total_pnl += pnl
            total_trades += trades
            total_winning_trades += winning_trades

            print(f"{symbol:12} | Trades: {trades:3} | Win Rate: {win_rate:6.2f}% | P&L: ₹{pnl:10,.2f}")

        overall_win_rate = (total_winning_trades / total_trades * 100) if total_trades > 0 else 0

        print("-"*60)
        print(f"{'TOTAL':12} | Trades: {total_trades:3} | Win Rate: {overall_win_rate:6.2f}% | P&L: ₹{total_pnl:10,.2f}")
        print("="*60)

        return {
            'total_trades': total_trades,
            'win_rate': overall_win_rate,
            'total_pnl': total_pnl
        }

    def run_live_monitoring(self):
        """Run live monitoring (can be scheduled)"""
        logger.info("Starting live monitoring...")

        try:
            for symbol in STOCK_SYMBOLS:
                # Get latest data
                latest_df = self.data_fetcher.get_latest_data(symbol, period="1mo")

                if not latest_df.empty:
                    # Generate signals
                    df_with_signals = self.strategy.generate_signals(latest_df)

                    # Check for new signals
                    latest_signal = df_with_signals['Signal'].iloc[-1]
                    if latest_signal != 0:
                        signal_type = 'BUY' if latest_signal == 1 else 'SELL'
                        current_price = df_with_signals['Close'].iloc[-1]

                        logger.info(f"New signal for {symbol}: {signal_type} at ₹{current_price:.2f}")

                        # Send alert
                        self.telegram_alerter.send_trade_alert(symbol, signal_type, current_price)

        except Exception as e:
            error_msg = f"Error in live monitoring: {str(e)}"
            logger.error(error_msg)
            self.telegram_alerter.send_error_alert(error_msg)

    def run_multi_period_backtest(self):
        """Test strategy across different time periods"""
        periods = {
            '6 Months': '6mo',
            '1 Year': '1y',
            '2 Years': '2y',
            '3 Years': '3y'
        }

        results_summary = {}
        print("\n" + "="*70)
        print("MULTI-PERIOD BACKTEST ANALYSIS")
        print("="*70)

        for period_name, period_code in periods.items():
            print(f"\n{'='*60}")
            print(f"TESTING PERIOD: {period_name} ({period_code})")
            print(f"{'='*60}")

            try:
                # Run backtest for this period
                results = self.run_backtest(period=period_code)

                if results:
                    # Store results
                    results_summary[period_name] = {
                        'period': period_code,
                        'trades': results['total_trades'],
                        'win_rate': results['win_rate'],
                        'pnl': results['total_pnl']
                    }
                else:
                    results_summary[period_name] = {
                        'period': period_code,
                        'trades': 0,
                        'win_rate': 0,
                        'pnl': 0
                    }

            except Exception as e:
                logger.error(f"Error testing period {period_name}: {e}")
                results_summary[period_name] = {
                    'period': period_code,
                    'trades': 0,
                    'win_rate': 0,
                    'pnl': 0
                }

        # Print comparison summary
        print(f"\n{'='*70}")
        print("PERIOD COMPARISON SUMMARY")
        print(f"{'='*70}")
        print(f"{'Period':15} | {'Trades':8} | {'Win Rate':10} | {'P&L (₹)':15}")
        print("-"*70)

        for period_name, results in results_summary.items():
            trades = results['trades']
            win_rate = results['win_rate']
            pnl = results['pnl']
            print(f"{period_name:15} | {trades:8} | {win_rate:8.2f}% | ₹{pnl:12,.2f}")

        print("="*70)
        return results_summary

def main():
    """Main execution function with strategy selection only"""
    print("Algo Trading System Starting...")

    # Strategy Selection Menu Only
    print("\n" + "="*60)
    print("STRATEGY SELECTION")
    print("="*60)
    print("1. Assignment Compliant (RSI<30 + Uptrend) - Very Conservative")
    print("2. Working Original (RSI<40 Simple) - Previously Successful")
    print("3. Balanced Approach (RSI<35 + Uptrend) - Good Balance")

    strategy_choice = input("Enter strategy choice (1/2/3): ").strip()

    # Map strategy choices
    strategy_map = {
        "1": "assignment_compliant",
        "2": "working_original",
        "3": "balanced"
    }

    selected_strategy = strategy_map.get(strategy_choice, "working_original")
    print(f"✅ Selected Strategy: {selected_strategy}")

    # Execution Options Menu
    print("\n" + "="*60)
    print("EXECUTION OPTIONS")
    print("="*60)
    print("1. Run Backtest (6 months)")
    print("2. Run Live Monitoring")
    print("3. Run Both")
    print("4. Run Multi-Period Analysis")

    choice = input("Enter your choice (1/2/3/4): ").strip()

    # Create system with selected strategy (all stocks by default)
    system = AlgoTradingSystem(strategy_type=selected_strategy)

    if choice == "1":
        system.run_backtest()
    elif choice == "2":
        system.run_live_monitoring()
    elif choice == "3":
        system.run_backtest()
        print("\nStarting live monitoring in 10 seconds...")
        time.sleep(10)
        system.run_live_monitoring()
    elif choice == "4":
        system.run_multi_period_backtest()
    else:
        print("Invalid choice. Running backtest by default.")
        system.run_backtest()

if __name__ == "__main__":
    main()