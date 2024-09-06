#!/bin/bash

# Step 1: Update and upgrade system
echo "Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y

# Step 2: Install Python and required system packages
echo "Installing Python and system dependencies..."
sudo apt-get install -y python3 python3-venv python3-pip python3-dev libffi-dev libssl-dev libi2c-dev libgpiod2 git i2c-tools

# Step 3: Set up Python virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv bioreactor_env
source bioreactor_env/bin/activate

# Step 4: Install Python dependencies from requirements.txt
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Step 5: Configure I2C and SPI
echo "Configuring I2C and SPI..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo modprobe i2c-dev
sudo modprobe spi-dev

# Step 6: Set up environment variables for Telegram bot
echo "Setting environment variables for Telegram bot..."
read -p "Enter your BOT_TOKEN: " BOT_TOKEN
read -p "Enter your CHAT_ID: " CHAT_ID

# Append environment variables to .bashrc for persistence
echo "export BOT_TOKEN=$BOT_TOKEN" >> ~/.bashrc
echo "export CHAT_ID=$CHAT_ID" >> ~/.bashrc
source ~/.bashrc

# Step 7: Set file permissions for sensitive data
echo "Setting file permissions for sensitive data..."
chmod 600 ~/.config/bioreactor_secure_config/secret_key.key
chmod 600 ~/.config/bioreactor_secure_config/encrypted_data.txt

# Step 8: Run Telegram connection test
echo "Running Telegram connection test..."
python3 test_telegram_connection.py

# Step 9: Enable logging for debugging
echo "Setting up logging..."
LOG_FILE="bioreactor_setup.log"
exec > >(tee -i $LOG_FILE)
exec 2>&1

# Step 10: Auto-reboot suggestion
echo "Setup complete. It is recommended to reboot your system."
read -p "Would you like to reboot now? (y/n): " REBOOT

if [[ $REBOOT == "y" || $REBOOT == "Y" ]]; then
    sudo reboot
else
    echo "Please remember to reboot later for the full system configuration to take effect."
fi

# Done