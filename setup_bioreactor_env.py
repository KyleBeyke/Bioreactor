

import os
import subprocess
from cryptography.fernet import Fernet

# Define paths for secure storage
config_dir = os.path.expanduser("~/.config/bioreactor_secure_config")
secure_file_path = os.path.join(config_dir, "encrypted_data.txt")
key_file_path = os.path.join(config_dir, "secret_key.key")
service_file_path = "/etc/systemd/system/load-env.service"
shell_script_path = os.path.expanduser("~/load_env_variables.sh")

# Step 1: Create the configuration directory if it doesn't exist
os.makedirs(config_dir, exist_ok=True)

# Step 2: Generate the encryption key if it doesn't exist
if not os.path.exists(key_file_path):
    key = Fernet.generate_key()
    with open(key_file_path, "wb") as key_file:
        key_file.write(key)
    print(f"Encryption key generated and stored securely at {key_file_path}.")
else:
    with open(key_file_path, "rb") as key_file:
        key = key_file.read()
    print(f"Encryption key loaded from {key_file_path}.")

# Step 3: Create or load encrypted bot token and chat ID
cipher_suite = Fernet(key)

if not os.path.exists(secure_file_path):
    bot_token = input("Enter your bot token: ")
    chat_id = input("Enter your chat ID: ")

    encrypted_bot_token = cipher_suite.encrypt(bot_token.encode())
    encrypted_chat_id = cipher_suite.encrypt(chat_id.encode())

    # Save the encrypted values to a file
    with open(secure_file_path, "wb") as file:
        file.write(encrypted_bot_token + b'\n' + encrypted_chat_id)
    print(f"Encrypted data securely stored in {secure_file_path}.")
else:
    print(f"Encrypted data already exists at {secure_file_path}.")

# Set strict file permissions
os.chmod(secure_file_path, 0o600)
os.chmod(key_file_path, 0o600)

# Step 4: Create a shell script to load the environment variables on boot
with open(shell_script_path, "w") as shell_script:
    shell_script.write(f"""#!/bin/bash
CONFIG_DIR="{config_dir}"
ENCRYPTED_DATA="$CONFIG_DIR/encrypted_data.txt"
KEY_FILE="$CONFIG_DIR/secret_key.key"

# Load the encryption key
if [ ! -f "$KEY_FILE" ]; then
  echo "Encryption key not found. Exiting."
  exit 1
fi
ENCRYPTION_KEY=$(cat "$KEY_FILE")

# Load the encrypted data
if [ ! -f "$ENCRYPTED_DATA" ]; then
  echo "Encrypted data not found. Exiting."
  exit 1
fi

BOT_TOKEN_ENC=$(sed -n '1p' "$ENCRYPTED_DATA")
CHAT_ID_ENC=$(sed -n '2p' "$ENCRYPTED_DATA")

# Use Python to decrypt the values (since decryption is easier using Python with Fernet)
BOT_TOKEN=$(python3 -c "from cryptography.fernet import Fernet; key=b'$ENCRYPTION_KEY'; cipher=Fernet(key); print(cipher.decrypt(b'$BOT_TOKEN_ENC').decode())")
CHAT_ID=$(python3 -c "from cryptography.fernet import Fernet; key=b'$ENCRYPTION_KEY'; cipher=Fernet(key); print(cipher.decrypt(b'$CHAT_ID_ENC').decode())")

# Export the environment variables
export BOT_TOKEN="$BOT_TOKEN"
export CHAT_ID="$CHAT_ID"

echo "Environment variables for BOT_TOKEN and CHAT_ID have been set."
""")

# Make the shell script executable
os.chmod(shell_script_path, 0o755)
print(f"Shell script created and set to executable: {shell_script_path}")

# Step 5: Create a systemd service file to run the script at boot
with open(service_file_path, "w") as service_file:
    service_file.write(f"""[Unit]
Description=Load Bioreactor Environment Variables
After=network.target

[Service]
ExecStart=/bin/bash {shell_script_path}
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
""")
print(f"Systemd service file created: {service_file_path}")

# Step 6: Enable and start the systemd service
subprocess.run(["sudo", "systemctl", "daemon-reload"])
subprocess.run(["sudo", "systemctl", "enable", "load-env.service"])
subprocess.run(["sudo", "systemctl", "start", "load-env.service"])

print("Systemd service enabled and started. Environment variables will be loaded on boot.")