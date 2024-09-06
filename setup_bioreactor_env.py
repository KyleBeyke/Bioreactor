"""
setup_bioreactor_env.py

This script sets up the environment for the bioreactor project by configuring environment variables 
for the bot token and chat ID. It uses encryption to securely store these sensitive values and ensures 
they are loaded from an .env file. The script also automates the setup process, validates Telegram connection, 
and sets file permissions for security.

Features:
- Set environment variables for bot token and chat ID.
- Encrypt sensitive data using Fernet encryption.
- Store encrypted data in a secure location.
- Automate the setup process and run a connection test.
- Use a .env file for secure storage of credentials.
"""

import os
from cryptography.fernet import Fernet
import subprocess
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path('.') / '.env'
if not env_path.exists():
    # Create an empty .env file if it doesn't exist
    with open(env_path, 'w') as f:
        pass

# Define the secure config directory
config_dir = os.path.expanduser("~/.config/bioreactor_secure_config")
os.makedirs(config_dir, exist_ok=True)

# Path to store the encryption key and encrypted data
key_file_path = os.path.join(config_dir, "secret_key.key")
secure_file_path = os.path.join(config_dir, "encrypted_data.txt")

# Function to generate a new encryption key
def generate_encryption_key():
    """Generate a new Fernet encryption key and store it in a secure file."""
    key = Fernet.generate_key()
    with open(key_file_path, "wb") as key_file:
        key_file.write(key)
    os.chmod(key_file_path, 0o600)  # Set file permissions (read/write for the owner only)
    print(f"Encryption key saved at: {key_file_path}")
    return key

# Function to load the encryption key
def load_encryption_key():
    """Load the encryption key from the secure key file."""
    with open(key_file_path, "rb") as key_file:
        return key_file.read()

# Function to encrypt and store sensitive data
def encrypt_and_store_data(bot_token, chat_id):
    """Encrypt and store the bot token and chat ID in a secure file."""
    cipher_suite = Fernet(load_encryption_key())
    encrypted_bot_token = cipher_suite.encrypt(bot_token.encode())
    encrypted_chat_id = cipher_suite.encrypt(chat_id.encode())

    with open(secure_file_path, "wb") as file:
        file.write(encrypted_bot_token + b'\n' + encrypted_chat_id)

    os.chmod(secure_file_path, 0o600)  # Set file permissions (read/write for the owner only)
    print(f"Encrypted data saved at: {secure_file_path}")

# Function to set environment variables from encrypted data
def set_env_from_encrypted_data():
    """Decrypt the stored bot token and chat ID, then set them as environment variables."""
    cipher_suite = Fernet(load_encryption_key())

    with open(secure_file_path, "rb") as file:
        encrypted_bot_token = file.readline().strip()
        encrypted_chat_id = file.readline().strip()

    bot_token = cipher_suite.decrypt(encrypted_bot_token).decode()
    chat_id = cipher_suite.decrypt(encrypted_chat_id).decode()

    # Write decrypted values to .env file
    with open(env_path, 'w') as f:
        f.write(f"BOT_TOKEN={bot_token}\n")
        f.write(f"CHAT_ID={chat_id}\n")

    os.environ['BOT_TOKEN'] = bot_token
    os.environ['CHAT_ID'] = chat_id
    print("Environment variables BOT_TOKEN and CHAT_ID have been set.")

# Function to run the connection test
def run_connection_test():
    """Run a test script to verify the Telegram connection."""
    print("Running connection test...")
    result = subprocess.run(["python3", "test_telegram_connection.py"], capture_output=True)
    if result.returncode == 0:
        print("Connection test passed.")
    else:
        print(f"Connection test failed. Output: {result.stdout.decode()}\n{result.stderr.decode()}")

# Main setup function
def main():
    """Main function to set up the environment and test the connection."""
    if not os.path.exists(key_file_path):
        print("No encryption key found. Generating a new key...")
        generate_encryption_key()

    bot_token = input("Enter your bot token: ")
    chat_id = input("Enter your chat ID: ")

    encrypt_and_store_data(bot_token, chat_id)
    set_env_from_encrypted_data()
    run_connection_test()

    # Suggest adding the config directory to .gitignore
    with open(".gitignore", "a") as gitignore:
        gitignore.write(f"\n# Ignore bioreactor secure config\n{config_dir}\n")
    print(f"{config_dir} has been added to .gitignore.")

if __name__ == "__main__":
    main()
