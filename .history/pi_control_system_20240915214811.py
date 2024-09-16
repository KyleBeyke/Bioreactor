"""
pi_control_system.py

This script communicates with a Raspberry Pi Pico over serial to control a bioreactor system.
It supports sending commands to the Pico, receiving sensor data, and logging both commands and data.
A non-blocking command prompt allows interaction while monitoring the serial data.

Key Features:
- Sends commands to the Pico (including setting temperature, heater control, and CO2 calibration).
- Receives and logs sensor data from the Pico.
- Handles serial communication with retries and error handling.
- Wakes the Pico from deep sleep using GPIO signals.
- Sends Telegram notifications for critical alerts.
- Logs commands and sensor data to CSV and log files for auditing.

Command Input Format:
Commands are issued via a non-blocking prompt and are terminated properly for communication with the Pico ('\n\r').

"""

import serial
import time
import logging
import select
import sys
import os
import csv
import RPi.GPIO as GPIO
from cryptography.fernet import Fernet
import requests
import datetime

# Initialize logging
LOG_FILE = "bioreactor_log.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# GPIO setup for waking up the Pico
WAKE_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(WAKE_PIN, GPIO.OUT, initial=GPIO.LOW)

# Serial setup
SERIAL_PORT = '/dev/ttyACM0'  # Update based on your setup
BAUD_RATE = 115200
TIMEOUT = 1

# CSV file for logging commands on the Pi
COMMAND_LOG_FILE = "commands_log.csv"

co2_threshold = 600  # Threshold for CO2 level
below_threshold_count = 0  # Track consecutive readings below threshold
above_threshold_flag = False  # Track consecutive readings above threshold
calibration_value = 400  # Default calibration value for CO2 sensor

# Initialize the serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
except serial.SerialException as e:
    logging.error(f"Failed to open serial port: {e}")
    sys.exit(f"Failed to open serial port: {e}")

# Load encrypted credentials for Telegram notifications
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

# Send message via Telegram
def send_telegram_message(message):
    """Sends a message to the configured Telegram bot."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {'chat_id': CHAT_ID, 'text': message}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logging.info("Telegram message sent successfully!")
        else:
            logging.error(f"Failed to send message. Status code: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Telegram message failed: {e}")

# Command logging function
def log_command(command):
    """Logs commands sent to the Pico."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        with open(COMMAND_LOG_FILE, mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([timestamp, command])
        logging.info(f"Logged command: {command}")
    except Exception as e:
        logging.error(f"Failed to log command: {e}")

# Send command to the Pico with retry logic
def send_command_to_pico(command, retries=3):
    """Sends a command over serial to the Pico, ensuring it is properly terminated, with retry logic."""
    for attempt in range(retries):
        try:
            full_command = f"{command}\n\r"  # Ensure the command is properly terminated
            ser.write(full_command.encode())
            ser.flush()  # Ensure the command is sent immediately
            log_command(command)
            logging.info(f"Command sent to Pico: {command}")
            return  # Command successfully sent
        except Exception as e:
            logging.error(f"Failed to send command on attempt {attempt + 1}/{retries}: {e}")
            time.sleep(2)  # Wait before retrying

            if attempt == retries - 1:
                logging.error("Max retries reached. Attempting to reconnect.")
                reconnect_serial()  # Reconnect if all retries fail

# Function to reconnect serial communication
def reconnect_serial():
    """Attempts to reconnect to the Pico over serial in case of a disconnection."""
    global ser
    try:
        ser.close()  # Close any existing connection
        time.sleep(2)  # Small delay before retrying
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        logging.info("Reconnected to the Pico successfully.")
    except serial.SerialException as e:
        logging.error(f"Failed to reconnect to the Pico: {e}")

# Function to wake the Pico
def wake_pico():
    """Sends a GPIO signal to wake up the Pico from deep sleep, with checks."""
    try:
        GPIO.output(WAKE_PIN, GPIO.HIGH)
        time.sleep(1)  # Give enough time for the wake signal
        GPIO.output(WAKE_PIN, GPIO.LOW)
        logging.info("Pico woken up from deep sleep")
    except Exception as e:
        logging.error(f"Error waking up Pico: {e}")
        GPIO.cleanup(WAKE_PIN)  # Cleanup specific pin to avoid issues
        raise

# Request RTC time from the Pico
def request_rtc_time():
    """Sends a command to request RTC time from the Pico."""
    send_command_to_pico("REQUEST_RTC_TIME")

# Display the help menu with available commands
def show_help_menu():
    """Displays the available commands."""
    help_menu = """
    /h      : Show this help menu
    /d      : Request sensor data
    /t      : Request RTC time
    /st     : Set RTC time on the Pico
    /f      : Feed - Enter the feed amount in grams
    /cal    : Calibrate - Enter the CO2 value for recalibration
    /th     : Set CO2 warning threshold level
    /alt    : Set altitude for SCD30 sensor
    /p      : Set sea level pressure reference for BMP280 sensor
    /int    : Set CO2 measurement interval for SCD30 sensor
    /cyc    : Set sensor data query cycle duration in minutes
    /set_temp : Set target temperature for the heater
    /incd   : Increase heater duty cycle by specified percent
    /decd   : Decrease heater duty cycle by specified percent
    /s      : Shutdown the system into deep sleep
    /w      : Wake the Pico from deep sleep
    /r      : Reset the Pico
    /e      : Exit the control loop
    """
    print(help_menu)

def handle_user_input(command):
    """Handles user input with enhanced validation for commands requiring numeric values."""
    try:
        if command == '/h':
            show_help_menu()

        elif command == '/d':
            send_command_to_pico("REQUEST_DATA")

        elif command == '/t':
            request_rtc_time()

        elif command == '/st':
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_command_to_pico(f"SYNC_TIME,{current_time}")
            print(f"System time sent to Pico: {current_time}")
            logging.info(f"System time sent to Pico: {current_time}")

        elif command == '/f':
            feed_amount = input("Enter feed amount (grams): ")
            if not feed_amount.isdigit() or int(feed_amount) <= 0:
                print("Feed amount must be a positive number.")
                return
            send_command_to_pico(f"FEED,{feed_amount}")

        elif command == '/cal':
            co2_baseline = input("Enter CO2 value for recalibration: ")
            if not co2_baseline.isdigit() or int(co2_baseline) <= 0:
                print("CO2 value must be a positive number.")
                return
            send_command_to_pico(f"CALIBRATE,{co2_baseline}")

        elif command == '/set_temp':
            target_temp = input("Enter target temperature for the heater (°C): ")
            try:
                target_temp = float(target_temp)
                if target_temp < 0:
                    raise ValueError("Temperature must be a positive number.")
                send_command_to_pico(f"SET_HEATER_TEMP,{target_temp}")
                print(f"Target temperature set to: {target_temp}°C")
            except ValueError as e:
                print(f"Invalid input: {e}")

        elif command == '/incd':
            increase_amount = input("Enter amount to increase heater duty cycle (%): ")
            if not increase_amount.isdigit() or int(increase_amount) <= 0:
                print("Duty cycle increment must be a positive number.")
                return
            send_command_to_pico(f"INCREASE_DUTY_CYCLE,{increase_amount}")

        elif command == '/decd':
            decrease_amount = input("Enter amount to decrease heater duty cycle (%): ")
            if not decrease_amount.isdigit() or int(decrease_amount) <= 0:
                print("Duty cycle decrement must be a positive number.")
                return
            send_command_to_pico(f"DECREASE_DUTY_CYCLE,{decrease_amount}")

        elif command == '/r':
            send_command_to_pico("RESET_PICO")

        elif command == '/s':
            send_command_to_pico("SHUTDOWN")

        elif command == '/w':
            wake_pico()

        elif command == '/e':
            logging.info("Exiting control loop")
            sys.exit(0)

        else:
            print("Invalid command. Type '/h' for the list of available commands.")
            logging.warning("Invalid command entered")

    except Exception as e:
        logging.error(f"Error processing command: {e}")
        print(f"Error processing command: {e}")

# Main control loop
def control_loop():
    """Main loop to handle serial communication, user input, and monitoring sensor data."""
    global co2_threshold  # Threshold for CO2 level
    global below_threshold_count  # Track consecutive readings below threshold
    global above_threshold_flag  # Track consecutive readings above threshold
    global calibration_value  # Default calibration value for CO2 sensor

    prompt_displayed = False
    last_status_check = time.monotonic()  # Track the last status handshake with Pico

    try:
        while True:
            current_time = time.monotonic()

            # Periodic status check every 60 seconds
            if current_time - last_status_check >= 60:
                send_command_to_pico("REQUEST_STATUS")
                last_status_check = current_time

            # Check for incoming serial data from the Pico
            try:
                if ser.in_waiting > 0:
                    serial_data = ser.readline().decode('utf-8').strip()
                    print(f"Data received: {serial_data}")
                    logging.info(f"Received data: {serial_data}")

                    # Handle sensor data received from the Pico
                    if serial_data.startswith("SENSOR DATA:"):
                        data_parts = serial_data.split(":")[1].split(",")
                        if len(data_parts) >= 6:
                            co2_value = float(data_parts[1])  # Extract the CO2 value

                            if co2_value >= co2_threshold:
                                above_threshold_flag = True

                            if co2_value < co2_threshold and above_threshold_flag:
                                below_threshold_count += 1
                            else:
                                below_threshold_count = 0

                            if below_threshold_count >= 3:
                                message = f"WARNING: Bioreactor CO2 is below threshold: {co2_threshold} ppm"
                                send_telegram_message(message)
                                logging.info(f"Telegram alert sent: {message}")
                                above_threshold_flag = False
                                below_threshold_count = 0
                        else:
                            logging.error(f"Malformed sensor data received: {serial_data}")

                    prompt_displayed = False

            except (serial.SerialException, TimeoutError) as e:
                logging.error(f"Error with serial communication: {e}")
                print(f"Error: {e}")
                time.sleep(2)
                continue

            # Non-blocking user input check
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                command = sys.stdin.readline().strip().lower()
                handle_user_input(command)

            if not prompt_displayed:
                print("> ", end="", flush=True)
                prompt_displayed = True

    except KeyboardInterrupt:
        logging.warning("Program interrupted by user")
        print("Program interrupted by user")

    except Exception as e:
        logging.error(f"Unexpected error in control loop: {e}")
        print(f"Unexpected error in control loop: {e}")

    finally:
        ser.close()
        GPIO.cleanup()

# Main program entry point
if __name__ == "__main__":
    control_loop()
