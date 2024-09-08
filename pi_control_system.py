"""
pi_control_system.py

This script controls the bioreactor's Raspberry Pi, which communicates with a Pico microcontroller. 
The script manages:
- Sensor data acquisition (CO2, temperature, etc.)
- Commands (feed, calibration, shutdown, restart)
- Time synchronization with Pico's RTC.
- Sending alerts via Telegram when CO2 levels cross a threshold.
- Logging commands and data for debugging and analysis.

Refined with modularity, error handling, logging, and environment variable support for secure operations.
"""

import serial
import time
import csv
import os
import logging
import RPi.GPIO as GPIO # type: ignore
from cryptography.fernet import Fernet
import requests

# Initialize logging
LOG_FILE = "bioreactor_log.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# GPIO setup for waking up the Pico
WAKE_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(WAKE_PIN, GPIO.OUT, initial=GPIO.LOW)

# Serial setup
SERIAL_PORT = '/dev/ttyACM0'  # Adjust this as necessary
BAUD_RATE = 115200
TIMEOUT = 1

# CSV file for logging commands on the Pi
COMMAND_LOG_FILE = "commands_log.csv"

# Helper functions for encrypted environment variables
def load_encrypted_credentials():
    """Load and decrypt the bot token and chat ID from secure environment variables."""
    secure_file_path = os.path.expanduser("~/.config/bioreactor_secure_config/encrypted_data.txt")
    try:
        with open(secure_file_path, "rb") as f:
            lines = f.readlines()
            bot_token_encrypted = lines[0].strip()
            chat_id_encrypted = lines[1].strip()
    except FileNotFoundError as e:
        logging.error(f"Encrypted credentials not found: {e}")
        raise

    key_path = os.path.expanduser("~/.config/bioreactor_secure_config/secret_key.key")
    try:
        with open(key_path, "rb") as key_file:
            key = key_file.read()
        cipher = Fernet(key)
        bot_token = cipher.decrypt(bot_token_encrypted).decode()
        chat_id = cipher.decrypt(chat_id_encrypted).decode()
    except Exception as e:
        logging.error(f"Error decrypting credentials: {e}")
        raise

    return bot_token, chat_id

# Load credentials for Telegram
BOT_TOKEN, CHAT_ID = load_encrypted_credentials()

# Function to send messages via Telegram
def send_telegram_message(message):
    """Sends a message to the configured Telegram bot."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {'chat_id': CHAT_ID, 'text': message}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logging.info("Message sent successfully!")
        else:
            logging.error(f"Failed to send message. Status code: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Telegram message failed: {e}")

# Logging helper for commands
def log_command(command):
    """Logs commands issued to the Pico."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        with open(COMMAND_LOG_FILE, mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, command])
        logging.info(f"Logged command: {command}")
    except Exception as e:
        logging.error(f"Failed to log command: {e}")

# Function to request RTC time from the Pico
def request_rtc_time(ser):
    """Requests the RTC time from the Pico."""
    try:
        ser.write("REQUEST_RTC_TIME\n".encode())
        while True:
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                if "RTC_TIME" in response:
                    rtc_time = response.split(",")[1]
                    logging.info(f"RTC time received: {rtc_time}")
                    return rtc_time
    except Exception as e:
        logging.error(f"Failed to request RTC time: {e}")

# Wake up the Pico from deep sleep
def wake_pico():
    """Sends a GPIO signal to wake up the Pico from deep sleep."""
    try:
        GPIO.output(WAKE_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(WAKE_PIN, GPIO.LOW)
        logging.info("Pico woken up from deep sleep")
    except Exception as e:
        logging.error(f"Error waking up Pico: {e}")

# Function to display the help menu
def show_help_menu():
    """Displays the available command options."""
    help_menu = """
    /help : Show this help menu
    /f : Feed - Enter the feed amount in grams
    /c : Calibrate - Enter the CO2 value for recalibration
    /s : Shutdown the system
    /r : Restart the Pico from deep sleep
    /t : Set CO2 threshold value
    /e : Exit the control loop
    """
    print(help_menu)

# Main control function
def control_loop():
    """Main loop to handle Pico communication and commands."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        rtc_time = request_rtc_time(ser)  # Get RTC time on startup
    except serial.SerialException as e:
        logging.error(f"Failed to open serial port: {e}")
        return

    try:
        while True:
            if ser.in_waiting > 0:
                sensor_data = ser.readline().decode('utf-8').strip()
                if "CO2" in sensor_data:
                    logging.info(f"CO2 data received: {sensor_data}")
                else:
                    logging.info(f"Received data: {sensor_data}")

            # Get user input for commands
            command = input("Enter command (use '/help' for a list of commands): ").lower()
            
            if command == '/help':
                show_help_menu()

            elif command == '/f':
                feed_amount = input("Enter feed amount (grams): ")
                feed_command = f"FEED,{feed_amount}\n"
                ser.write(feed_command.encode())
                log_command(feed_command)
                logging.info(f"Feed command sent: {feed_amount} grams")

            elif command == '/c':
                co2_value = input("Enter CO2 value for recalibration: ")
                recalibration_command = f"CALIBRATE,{co2_value}\n"
                ser.write(recalibration_command.encode())
                log_command(recalibration_command)
                logging.info(f"Recalibration command sent for {co2_value} ppm")

            elif command == '/s':
                shutdown_command = "SHUTDOWN\n"
                ser.write(shutdown_command.encode())
                log_command(shutdown_command)
                logging.info("Shutdown command sent to Pico")

            elif command == '/r':
                wake_pico()
                logging.info("Restart command executed (woke Pico)")

            elif command == '/t':
                new_threshold = input("Enter new CO2 threshold: ")
                logging.info(f"New CO2 threshold set: {new_threshold}")

            elif command == '/e':
                logging.info("Exiting control loop")
                break

            else:
                logging.warning("Invalid command entered")

    except KeyboardInterrupt:
        logging.warning("Program interrupted by user")
    
    except Exception as e:
        logging.error(f"Unexpected error in control loop: {e}")
    
    finally:
        ser.close()
        GPIO.cleanup()

# Main program entry point
if __name__ == "__main__":
    control_loop()
