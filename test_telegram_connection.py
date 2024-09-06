"""
Test the connection to Telegram by sending a test message.

This function loads the encryption key and encrypted data from the specified file paths.
It decrypts the bot token and chat ID using the encryption key.
Then, it sends a test message to the specified chat ID via the Telegram API.

Raises:
    Exception: If there is an error during the Telegram connection test.
"""

import os
import requests
from cryptography.fernet import Fernet

def test_telegram_connection():
    try:
        # Load encryption key and encrypted data
        config_dir = os.path.expanduser("~/.config/bioreactor_secure_config")
        key_file_path = os.path.join(config_dir, "secret_key.key")
        secure_file_path = os.path.join(config_dir, "encrypted_data.txt")

        # Load the encryption key
        with open(key_file_path, "rb") as key_file:
            key = key_file.read()
        cipher_suite = Fernet(key)

        # Load the encrypted token and chat ID
        with open(secure_file_path, "rb") as file:
            encrypted_bot_token = file.readline().strip()
            encrypted_chat_id = file.readline().strip()

        # Decrypt the bot token and chat ID
        bot_token = cipher_suite.decrypt(encrypted_bot_token).decode()
        chat_id = cipher_suite.decrypt(encrypted_chat_id).decode()

        # Test sending a message via Telegram
        test_message = "Test: Telegram connection successful!"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': test_message
        }

        response = requests.post(url, data=data)

        if response.status_code == 200:
            print("Test message sent successfully!")
        else:
            print(f"Failed to send test message. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error during Telegram connection test: {e}")

if __name__ == "__main__":
    test_telegram_connection()