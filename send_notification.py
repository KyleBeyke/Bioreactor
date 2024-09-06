"""
Sends a Telegram message using the provided bot token and chat ID.
Parameters:
- bot_token (str): The bot token for authentication.
- chat_id (str): The chat ID of the recipient.
- message (str): The message to send.
"""
from cryptography.fernet import Fernet
import requests

# Load the encryption key from the file
with open("secret_key.key", "rb") as key_file:
    key = key_file.read()

# Initialize the Fernet cipher suite
cipher_suite = Fernet(key)

# Load the encrypted bot token and chat ID from the file
with open("encrypted_data.txt", "rb") as file:
    encrypted_bot_token = file.readline().strip()
    encrypted_chat_id = file.readline().strip()

# Decrypt the bot token and chat ID
bot_token = cipher_suite.decrypt(encrypted_bot_token).decode()
chat_id = cipher_suite.decrypt(encrypted_chat_id).decode()

# Define the message to send
message = "This is a test message from your bot!"

def send_telegram_message(bot_token, chat_id, message):
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

# Send the test message
send_telegram_message(bot_token, chat_id, message)