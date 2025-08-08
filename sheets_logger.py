"""Google Sheets integration for logging trades and analytics"""
import pandas as pd
import gspread
import datetime

from google.oauth2.service_account import Credentials
import logging
from typing import List, Dict
from config import GOOGLE_SHEETS_NAME, GOOGLE_CREDENTIALS_FILE

logger = logging.getLogger(__name__)

class SheetsLogger:
    def __init__(self, credentials_file: str = GOOGLE_CREDENTIALS_FILE):
        self.credentials_file = credentials_file
        self.client = None
        self.spreadsheet = None
        self.connect()
    
    def connect(self):
        """Connect to Google Sheets"""
        try:
            # Define the scope
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scope
            )
            
            # Create client
            self.client = gspread.authorize(creds)
            
            # Open or create spreadsheet
            try:
                self.spreadsheet = self.client.open(GOOGLE_SHEETS_NAME)
            except gspread.SpreadsheetNotFound:
                self.spreadsheet = self.client.create(GOOGLE_SHEETS_NAME)
                logger.info(f"Created new spreadsheet: {GOOGLE_SHEETS_NAME}")
            
            self.setup_sheets()
            logger.info("Successfully connected to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error connecting to Google Sheets: {str(e)}")
    
    def setup_sheets(self):
        """Setup required sheets with headers"""
        sheet_configs = {
            'Trade_Log': [
                'Date', 'Symbol', 'Action', 'Price', 'Quantity', 'Value', 'PnL', 'PnL_pct'
            ],
            'Summary': [
                'Symbol', 'Total_Trades', 'Winning_Trades', 'Win_Rate', 'Total_PnL', 'Final_Portfolio_Value'
            ],
            'Signals': [
                'Date', 'Symbol', 'Signal', 'Price', 'RSI', 'SMA_20', 'SMA_50', 'ML_Prediction'
            ],
            'ML_Results': [
                'Date', 'Model_Type', 'Accuracy', 'Features_Used', 'Training_Samples', 'Test_Samples'
            ]
        }
        
        for sheet_name, headers in sheet_configs.items():
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name, rows=1000, cols=len(headers)
                )
                # FIXED: Use batch_update instead of append_row
                worksheet.batch_update([{
                    'range': 'A1',
                    'values': [headers]
                }])
                logger.info(f"Created sheet: {sheet_name}")
    
    def log_trades(self, trades_df: pd.DataFrame):
        """Log trades to Google Sheets"""
        if trades_df.empty:
            return

        try:
            worksheet = self.spreadsheet.worksheet('Trade_Log')

            # Convert Timestamps to strings (e.g. ISO format)
            trades_df = trades_df.map(lambda x: x.isoformat() if isinstance(x, pd.Timestamp) else x)

            # Fill NaNs and convert DataFrame to list of lists
            data = trades_df.fillna('').values.tolist()

            worksheet.append_rows(data)
            logger.info(f"Logged {len(data)} trades to Google Sheets")

        except Exception as e:
            logger.error(f"Error logging trades: {str(e)}")

    def log_summary(self, performance_metrics: List[Dict]):
        """Log performance summary to Google Sheets"""
        try:
            worksheet = self.spreadsheet.worksheet('Summary')
            
            # Clear existing data (except headers)
            worksheet.clear()
            headers = ['Symbol', 'Total_Trades', 'Winning_Trades', 'Win_Rate', 'Total_PnL', 'Final_Portfolio_Value']
            
            # FIXED: Use batch_update for headers
            worksheet.batch_update([{
                'range': 'A1',
                'values': [headers]
            }])
            
            # Prepare all data rows
            data_rows = []
            for metrics in performance_metrics:
                row = [
                    metrics.get('Symbol', ''),
                    metrics.get('Total_Trades', 0),
                    metrics.get('Winning_Trades', 0),
                    metrics.get('Win_Rate', 0),
                    metrics.get('Total_PnL', 0),
                    metrics.get('Final_Portfolio_Value', 0)
                ]
                data_rows.append(row)
            
            # FIXED: Use append_rows for multiple rows at once
            if data_rows:
                worksheet.append_rows(data_rows)
            
            logger.info("Updated summary in Google Sheets")
            
        except Exception as e:
            logger.error(f"Error logging summary: {str(e)}")
    
    def log_signals(self, signals_data: List[Dict]):
        """Log current signals to Google Sheets"""
        try:
            worksheet = self.spreadsheet.worksheet('Signals')
            
            # Clear existing data (except headers)
            worksheet.clear()
            headers = ['Date', 'Symbol', 'Signal', 'Price', 'RSI', 'SMA_20', 'SMA_50', 'ML_Prediction']
            
            # FIXED: Use batch_update for headers
            worksheet.batch_update([{
                'range': 'A1',
                'values': [headers]
            }])
            
            # Prepare all data rows
            data_rows = []
            for signal in signals_data:
                row = [
                    signal.get('Date', ''),
                    signal.get('Symbol', ''),
                    signal.get('Signal', ''),
                    signal.get('Price', 0),
                    signal.get('RSI', 0),
                    signal.get('SMA_20', 0),
                    signal.get('SMA_50', 0),
                    signal.get('ML_Prediction', '')
                ]
                data_rows.append(row)
            
            # FIXED: Use append_rows for multiple rows at once
            if data_rows:
                worksheet.append_rows(data_rows)
            
            logger.info("Updated signals in Google Sheets")
            
        except Exception as e:
            logger.error(f"Error logging signals: {str(e)}")
    
    def log_ml_results(self, ml_results: Dict):
        """Log ML model results to Google Sheets"""
        try:
            worksheet = self.spreadsheet.worksheet('ML_Results')
            
            row = [
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ml_results.get('Model_Type', ''),
                ml_results.get('Accuracy', 0),
                ', '.join(ml_results.get('Features_Used', [])),
                ml_results.get('Training_Samples', 0),
                ml_results.get('Test_Samples', 0)
            ]
            
            # FIXED: Use append_rows with a list containing the single row
            worksheet.append_rows([row])
            
            logger.info("Logged ML results to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error logging ML results: {str(e)}")
