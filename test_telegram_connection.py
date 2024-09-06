"""
test_telegram_connection.py

This script tests the connection to a Telegram bot by sending a test message to a chat.
It retrieves the bot token and chat ID from secure environment variables to ensure secure communication.

Features:
- Retrieve bot token and chat ID from environment variables.
- Send a test message to verify the connection.
- Log the test result for future reference with timestamp and outcome.
"""

import os
import requests
import time
import logging

# Initialize logging for the test result
LOG_FILE = "telegram_test_log.txt"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Function to send a message via Telegram
def send_telegram_message(bot_token, chat_id, message):
    """Send a test message via Telegram to verify the bot connection."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        logging.info("Message sent successfully!")
        return True
    except requests.RequestException as e:
        logging.error(f"Failed to send message: {e}")
        return False

# Main test function
def test_telegram_connection():
    """Main function to test the Telegram bot connection."""
    # Retrieve bot token and chat ID from environment variables
    bot_token = os.getenv('BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')

    if not bot_token or not chat_id:
        logging.error("BOT_TOKEN or CHAT_ID environment variables not set.")
        print("Error: BOT_TOKEN or CHAT_ID environment variables not set.")
        return

    # Test message with timestamp
    message = f"Test message sent at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"

    # Send test message and log the result
    success = send_telegram_message(bot_token, chat_id, message)
    if success:
        logging.info("Connection test passed.")
        print("Connection test passed.")
    else:
        logging.error("Connection test failed.")
        print("Connection test failed.")

if __name__ == "__main__":
    test_telegram_connection()
