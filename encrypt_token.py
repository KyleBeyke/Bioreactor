"""
Encrypts sensitive data using the Fernet encryption algorithm and saves the encrypted values to a file.
"""
from cryptography.fernet import Fernet

# Generate a key for encryption and decryption
# You must keep this key safe! Store it securely.
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# The sensitive data (your bot token and chat ID)
bot_token = " BOT TOKEN HERE " # Replace with your bot token
chat_id = " CHAT ID HERE " # Replace with your chat ID

# Encrypt the bot token and chat ID
encrypted_bot_token = cipher_suite.encrypt(bot_token.encode())
encrypted_chat_id = cipher_suite.encrypt(chat_id.encode())

# Save the encrypted values to a file
with open("encrypted_data.txt", "wb") as file:
    file.write(encrypted_bot_token + b'\n' + encrypted_chat_id)

# Save the encryption key to a separate file
with open("secret_key.key", "wb") as key_file:
    key_file.write(key)

print("Encryption complete. Store the 'secret_key.key' file securely.")