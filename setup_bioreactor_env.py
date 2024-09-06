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
os.chmod(secure_file_path, 0o600)
os.chmod(key_file_path, 0o600)

# Suggest adding the config directory to .gitignore
with open(".gitignore", "a") as gitignore:
    gitignore.write(f"\n# Ignore bioreactor secure config\n{config_dir}\n")

# Set environment variables
os.environ['BOT_TOKEN'] = bot_token
os.environ['CHAT_ID'] = chat_id

# Create a .env file for future runs
with open(os.path.join(config_dir, '.env'), 'w') as env_file:
    env_file.write(f"BOT_TOKEN={bot_token}\nCHAT_ID={chat_id}")

print(f"Environment setup complete. Files stored securely in {config_dir}.")
print("Running connection test...")

# Test the Telegram connection
subprocess.run(["python3", "test_telegram_connection.py"])
