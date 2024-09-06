import os
import requests

# Load the bot token and chat ID from environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not bot_token or not chat_id:
    print("Error: Bot token or chat ID not found in environment variables.")
    print("Make sure you have set the TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
    exit(1)

# Function to send a test message via Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")

# Send a test message to verify the Telegram bot connection
message = "This is a test message from the Bioreactor system."
send_telegram_message(message)
