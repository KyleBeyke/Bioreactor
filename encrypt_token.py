"""
Encrypts sensitive data and stores it securely in a file.
This script generates a key for encryption and decryption using the Fernet cryptography library. It prompts the user to enter their bot token and chat ID, encrypts the values, and saves them to a file. The encrypted values are stored in a secure configuration directory along with the encryption key. The script also sets strict file permissions to ensure that only the owner can read and write the files.
After encryption, it suggests adding the configuration directory to the .gitignore file to avoid committing it to version control. Finally, it runs a test script to verify the connection to Telegram.
Note: Make sure to keep the 'secret_key.key' file safe as it is required for decryption.
Usage:
    - Run the script and follow the prompts to enter the bot token and chat ID.
    - The encrypted values will be stored in the 'encrypted_data.txt' file.
    - The encryption key will be stored in the 'secret_key.key' file.
    - The configuration directory will be created at '~/.config/bioreactor_secure_config'.
    - The 'encrypted_data.txt' and 'secret_key.key' files will have strict file permissions (read and write only for the owner).
    - The configuration directory will be added to the .gitignore file.
Example:
    $ python encrypt_token.py
    Enter your bot token: <enter bot token>
    Enter your chat ID: <enter chat ID>
    Encryption complete. Files are stored securely in ~/.config/bioreactor_secure_config.
    Remember to keep the 'secret_key.key' file safe!
    Running connection test...
"""

import os
from cryptography.fernet import Fernet
import subprocess

# Generate a key for encryption and decryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# The sensitive data (your bot token and chat ID)
bot_token = input("Enter your bot token: ")
chat_id = input("Enter your chat ID: ")

# Encrypt the bot token and chat ID
encrypted_bot_token = cipher_suite.encrypt(bot_token.encode())
encrypted_chat_id = cipher_suite.encrypt(chat_id.encode())

# Create the config directory if it doesn't exist
config_dir = os.path.expanduser("~/.config/bioreactor_secure_config")
os.makedirs(config_dir, exist_ok=True)

# Save the encrypted values to a file
secure_file_path = os.path.join(config_dir, "encrypted_data.txt")
with open(secure_file_path, "wb") as file:
    file.write(encrypted_bot_token + b'\n' + encrypted_chat_id)

# Save the encryption key to a separate file
key_file_path = os.path.join(config_dir, "secret_key.key")
with open(key_file_path, "wb") as key_file:
    key_file.write(key)

# Set strict file permissions (read and write only for the owner)
os.chmod(secure_file_path, 0o600)  # Owner read/write permissions
os.chmod(key_file_path, 0o600)     # Owner read/write permissions

print(f"Encryption complete. Files are stored securely in {config_dir}.")
print("Remember to keep the 'secret_key.key' file safe!")

# Suggest adding the config directory to .gitignore to avoid committing it to version control
with open(".gitignore", "a") as gitignore:
    gitignore.write(f"\n# Ignore bioreactor secure config\n{config_dir}\n")
    
# After encryption, run the test script to verify Telegram connection
print("Running connection test...")
subprocess.run(["python3", "test_telegram_connection.py"])