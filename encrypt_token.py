"""
This script provides functions for encrypting and storing sensitive data, such as a Telegram bot token and chat ID, in a secure file with restricted access. It also includes a function for decrypting the stored data when needed.
Functions:
- generate_key(): Generates an encryption key using the Fernet encryption algorithm.
- get_telegram_credentials(): Prompts the user for the Telegram bot token and chat ID.
- encrypt_data(encryption_key, bot_token, chat_id): Encrypts the bot token and chat ID using the provided encryption key.
- store_encrypted_data(encryption_key, encrypted_bot_token, encrypted_chat_id): Stores the encrypted data in a secure file with restricted access.
- decrypt_data(): Decrypts the stored bot token and chat ID.
Usage:
1. Generate the encryption key using the generate_key() function.
2. Get the Telegram bot token and chat ID from the user using the get_telegram_credentials() function.
3. Encrypt the bot token and chat ID using the encrypt_data() function.
4. Store the encrypted data in a secure file using the store_encrypted_data() function.
5. When needed, decrypt the stored bot token and chat ID using the decrypt_data() function.
Note: The secure file path is set to "~/.config/bioreactor_secure_config" and the file is readable only by the user.
"""

import os
import base64
import subprocess
from cryptography.fernet import Fernet

# Step 1: Generate an encryption key
def generate_key():
    key = Fernet.generate_key()
    print(f"Generated encryption key: {key.decode()}")
    return key

# Step 2: Prompt the user for the Telegram bot token and chat ID
def get_telegram_credentials():
    bot_token = input("Enter your Telegram bot token: ")
    chat_id = input("Enter your Telegram chat ID: ")
    return bot_token, chat_id

# Step 3: Encrypt the bot token and chat ID
def encrypt_data(encryption_key, bot_token, chat_id):
    cipher_suite = Fernet(encryption_key)
    encrypted_bot_token = cipher_suite.encrypt(bot_token.encode())
    encrypted_chat_id = cipher_suite.encrypt(chat_id.encode())
    return encrypted_bot_token, encrypted_chat_id

# Step 4: Store the encrypted data in a secure file with restricted access
def store_encrypted_data(encryption_key, encrypted_bot_token, encrypted_chat_id):
    secure_file_path = os.path.expanduser("~/.config/bioreactor_secure_config")
    print(f"Storing encrypted data in {secure_file_path} with restricted permissions...")

    # Write the encrypted data to the secure file
    with open(secure_file_path, "w") as f:
        f.write(f"ENCRYPTION_KEY={base64.urlsafe_b64encode(encryption_key).decode()}\n")
        f.write(f"ENCRYPTED_BOT_TOKEN={encrypted_bot_token.decode()}\n")
        f.write(f"ENCRYPTED_CHAT_ID={encrypted_chat_id.decode()}\n")

    # Restrict file access (readable only by the user)
    os.chmod(secure_file_path, 0o600)
    print(f"Encrypted data stored in {secure_file_path} with restricted permissions.")

# Step 5: Decrypt the stored bot token and chat ID when needed
def decrypt_data():
    secure_file_path = os.path.expanduser("~/.config/bioreactor_secure_config")
    
    # Load the encrypted data from the file
    with open(secure_file_path) as f:
        lines = f.readlines()
        encryption_key = base64.urlsafe_b64decode(lines[0].split('=')[1].strip())
        encrypted_bot_token = lines[1].split('=')[1].strip()
        encrypted_chat_id = lines[2].split('=')[1].strip()

    # Decrypt the bot token and chat ID
    cipher_suite = Fernet(encryption_key)
    bot_token = cipher_suite.decrypt(encrypted_bot_token.encode()).decode()
    chat_id = cipher_suite.decrypt(encrypted_chat_id.encode()).decode()

    return bot_token, chat_id

if __name__ == "__main__":
    # Generate the encryption key
    encryption_key = generate_key()

    # Get Telegram credentials from the user
    bot_token, chat_id = get_telegram_credentials()

    # Encrypt the bot token and chat ID
    encrypted_bot_token, encrypted_chat_id = encrypt_data(encryption_key, bot_token, chat_id)

    # Store the encrypted data in a secure file with restricted access
    store_encrypted_data(encryption_key, encrypted_bot_token, encrypted_chat_id)

    # Test: Decrypt the stored values
    decrypted_bot_token, decrypted_chat_id = decrypt_data()
    print(f"\nDecrypted Bot Token: {decrypted_bot_token}")
    print(f"Decrypted Chat ID: {decrypted_chat_id}")