Installation Steps
Step 1: Clone the Repository

git clone https://github.com/yourusername/algo-trading-system.git

cd algo-trading-system
Step 2: Create Virtual Environment

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
Step 3: Install Dependencies
bash
pip install -r requirements.txt

Search and enable:
Google Sheets API
Google Drive API
Step 2: Create Service Account
Go to "APIs & Services" → "Credentials"
Click "Create Credentials" → "Service Account"
Enter service account name and click "Create"
Skip role assignment, click "Continue" then "Done"

Step 3: Generate Credentials
Click on your service account
Go to "Keys" tab → "Add Key" → "Create New Key"
Select JSON format and download
Rename the file to credentials.json and place in project folder

Step 4: Create Google Sheet
Open Google Sheets
Create new spreadsheet named: AlgoTrading_Portfolio
Click Share button
Add the service account email (from credentials.json file)
Give "Editor" permissions and click "Send"

Telegram Bot Setup
Step 1: Create Bot
Open Telegram and search: @BotFather
Send: /newbot
Choose bot name (e.g., "My Trading Bot")
Choose username (e.g., "MyTradingBot123")
Save the bot token provided

Step 2: Get Your Chat ID

Method 1:
Start your bot and send any message
Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
Find "chat" section and copy the "id" number

Method 2:
Search @userinfobot on Telegram
Send /start and copy the ID number
Edit config.py file with your settings

Start the Application
bash
python main.py
