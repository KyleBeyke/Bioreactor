"""
This script automates the setup of environment variables for the bioreactor project and encrypts sensitive information (bot token and chat ID).
It ensures that environment variables are securely stored and made available to the project.
This script also creates a .env file and sets the appropriate permissions to enhance security.

Main Functions:
- generate_key: Generates an encryption key to securely store sensitive information.
- store_encrypted_data: Encrypts and stores bot token and chat ID.
- set_env_variables: Creates a .env file and sets environment variables automatically.
- validate_env_variables: Validates that the environment variables are set correctly.
"""

import os
import base64
from cryptography.fernet import Fernet
import getpass

# Configuration directory
CONFIG_DIR = os.path.expanduser("~/.config/bioreactor_secure_config")
os.makedirs(CONFIG_DIR, exist_ok=True)

# Encryption key file path
KEY_FILE_PATH = os.path.join(CONFIG_DIR, "secret_key.key")

# Function to generate encryption key and save it to a file
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE_PATH, 'wb') as key_file:
        key_file.write(key)
    print(f"Encryption key generated and stored at {KEY_FILE_PATH}")
    return key

# Function to encrypt and store bot token and chat ID securely
def store_encrypted_data(key):
    cipher_suite = Fernet(key)

    bot_token = getpass.getpass(prompt="Enter your bot token: ")
    chat_id = input("Enter your chat ID: ")

    encrypted_bot_token = cipher_suite.encrypt(bot_token.encode())
    encrypted_chat_id = cipher_suite.encrypt(chat_id.encode())

    secure_file_path = os.path.join(CONFIG_DIR, "encrypted_data.txt")
    with open(secure_file_path, 'wb') as file:
        file.write(encrypted_bot_token + b'\n' + encrypted_chat_id)

    # Set file permissions to owner-only access
    os.chmod(secure_file_path, 0o600)
    print(f"Encrypted data stored securely in {secure_file_path}")

# Function to create the .env file with environment variables
def set_env_variables():
    env_file_path = os.path.join(os.getcwd(), ".env")
    with open(env_file_path, 'w') as env_file:
        env_file.write(f"CONFIG_DIR={CONFIG_DIR}\n")
        env_file.write(f"KEY_FILE_PATH={KEY_FILE_PATH}\n")

    # Set file permissions to owner-only access
    os.chmod(env_file_path, 0o600)
    print(f"Environment variables set and stored in {env_file_path}")

# Function to validate that environment variables are set correctly
def validate_env_variables():
    config_dir = os.getenv('CONFIG_DIR')
    key_file_path = os.getenv('KEY_FILE_PATH')

    if not config_dir or not key_file_path:
        print("Environment variables are not set correctly.")
    else:
        print(f"Environment variables loaded successfully: \nCONFIG_DIR: {config_dir}\nKEY_FILE_PATH: {key_file_path}")

# Main setup process
def main():
    print("Setting up bioreactor environment...")

    # Generate encryption key and store encrypted data
    if not os.path.exists(KEY_FILE_PATH):
        key = generate_key()
    else:
        with open(KEY_FILE_PATH, 'rb') as key_file:
            key = key_file.read()
        print("Encryption key loaded from existing file.")

    # Store encrypted bot token and chat ID
    store_encrypted_data(key)

    # Set environment variables
    set_env_variables()

    # Validate environment variables
    validate_env_variables()

if __name__ == "__main__":
    main()