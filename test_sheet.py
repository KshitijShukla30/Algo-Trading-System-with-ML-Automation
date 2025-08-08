# test_sheet.py
import gspread
from google.oauth2.service_account import Credentials

def test_sheets_connection():
    try:
        # Define scope
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Load credentials
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Open your sheet
        sheet = client.open("AlgoTrading_Portfolio")
        worksheet = sheet.sheet1
        
        # Test write using batch_update (most reliable)
        worksheet.batch_update([{
            'range': 'A1',
            'values': [['Test Connection']]
        }])
        print("✅ Google Sheets connection successful!")
        
        # Test read
        value = worksheet.get('A1')
        print(f"✅ Read test successful: {value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_sheets_connection()
