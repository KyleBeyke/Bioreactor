"""
test_telegram_connection.py

This script tests the Telegram bot connection by sending a message to the chat ID
using the bot token stored in environment variables.

It verifies whether the bot can successfully send a message and handle errors if the
connection fails.

Environment Variables:
- TELEGRAM_BOT_TOKEN: The bot token obtained from BotFather.
- TELEGRAM_CHAT_ID: The chat ID of the recipient (your Telegram user ID).

Make sure the setup_bioreactor_env.py script has been executed, and the environment
variables are loaded before running this test.
"""

import os
import requests

# Retrieve the bot token and chat ID from environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

# Check if the environment variables are set
if not bot_token or not chat_id:
    raise EnvironmentError("Bot token or chat ID is missing. Please ensure environment variables are set.")

# Function to send a test message via Telegram
def send_test_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Test message sent successfully!")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
            print("Response:", response.text)
    except Exception as e:
        print(f"Error occurred: {e}")

# Send a test message to verify the connection
if __name__ == "__main__":
    test_message = "This is a test message from the Bioreactor system."
    send_test_message(test_message)