"""
pi_control_system.py

This script communicates with a Raspberry Pi Pico over serial to control a bioreactor system.
It supports sending commands to the Pico, receiving sensor data, and logging both commands and data.
A non-blocking command prompt allows interaction while monitoring the serial data.
"""

import serial
import time
import logging
import select
import sys
import csv
import RPi.GPIO as GPIO
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
SERIAL_PORT = '/dev/ttyACM0'  # Update based on your setup
BAUD_RATE = 115200
TIMEOUT = 1

# CSV file for logging commands on the Pi
COMMAND_LOG_FILE = "commands_log.csv"

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

# Send command to the Pico
def send_command_to_pico(command):
    """Sends a command over serial to the Pico, ensuring it is properly terminated."""
    try:
        full_command = f"{command}\n"  # Ensure the command is properly terminated
        ser.write(full_command.encode())
        ser.flush()  # Ensure the command is sent immediately
        log_command(command)
        logging.info(f"Command sent to Pico: {command}")
    except Exception as e:
        logging.error(f"Failed to send command: {e}")

# Function to wake the Pico
def wake_pico():
    """Sends a GPIO signal to wake up the Pico from deep sleep."""
    try:
        GPIO.output(WAKE_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(WAKE_PIN, GPIO.LOW)
        logging.info("Pico woken up from deep sleep")
    except Exception as e:
        logging.error(f"Error waking up Pico: {e}")

# Request RTC time from the Pico
def request_rtc_time():
    """Sends a command to request RTC time from the Pico."""
    send_command_to_pico("REQUEST_RTC_TIME")

# Display the help menu
def show_help_menu():
    """Displays the available commands."""
    help_menu = """
    /h   : Show this help menu
    /d   : Request sensor data
    /f   : Feed - Enter the feed amount in grams
    /cal : Calibrate - Enter the CO2 value for recalibration
    /alt : Set altitude for SCD30 sensor
    /p   : Set sea level pressure reference for BMP280 sensor
    /int : Set CO2 measurement interval for SCD30 sensor
    /cyc : Set sensor data query cycle duration in minutes
    /s   : Shutdown the system into deep sleep
    /w   : Wake the Pico from deep sleep
    /r   : Reset the Pico
    /e   : Exit the control loop
    """
    print(help_menu)

# Main control loop
def control_loop():
    """Main loop to handle serial communication and user input."""
    prompt_displayed = False  # Track if the prompt has been displayed
    try:
        while True:
            # Check for incoming serial data from the Pico
            try:
                if ser.in_waiting > 0:
                    serial_data = ser.readline().decode('utf-8').strip()
                    print(f"Data received: {serial_data}")
                    logging.info(f"Received data: {serial_data}")
                    prompt_displayed = False  # Clear prompt flag to redisplay after data is processed
            except (serial.SerialException, TimeoutError) as e:
                logging.error(f"Error with serial communication: {e}")
                print(f"Error: {e}")

            # Non-blocking user input check
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)  # Non-blocking input
            if rlist:
                command = sys.stdin.readline().strip().lower()

                # Handle the user command
                try:
                    if command == '/h':
                        show_help_menu()

                    elif command == '/d':
                        send_command_to_pico("REQUEST_DATA")

                    elif command == '/f':
                        try:
                            feed_amount = int(input("Enter feed amount (grams): "))
                            if feed_amount <= 0:
                                print("Feed amount must be a positive number.")
                                continue
                            send_command_to_pico(f"FEED,{feed_amount}")
                        except ValueError:
                            print("Invalid input. Please enter a valid number.")
                            logging.warning("Invalid input for feed amount.")

                    elif command == '/cal':
                        try:
                            co2_value = int(input("Enter CO2 value for recalibration: "))
                            send_command_to_pico(f"CALIBRATE,{co2_value}")
                        except ValueError:
                            print("Invalid input. Please enter a valid CO2 value.")
                            logging.warning("Invalid input for CO2 recalibration.")

                    elif command == '/alt':
                        try:
                            altitude = int(input("Enter new altitude for SCD30 sensor (meters): "))
                            if altitude < 0:
                                print("Altitude cannot be negative.")
                                continue
                            send_command_to_pico(f"SET_ALTITUDE,{altitude}")
                        except ValueError:
                            print("Invalid input. Please enter a valid altitude.")
                            logging.warning("Invalid input for altitude.")

                    elif command == '/p':
                        try:
                            pressure = int(input("Enter new pressure reference for BMP280 sensor (hPa): "))
                            if pressure <= 0:
                                print("Pressure must be a positive number.")
                                continue
                            send_command_to_pico(f"SET_PRESSURE,{pressure}")
                        except ValueError:
                            print("Invalid input. Please enter a valid pressure reference.")
                            logging.warning("Invalid input for pressure reference.")

                    elif command == '/int':
                        try:
                            interval = int(input("Enter CO2 measurement interval for SCD30 sensor (seconds): "))
                            if interval < 2:
                                print("CO2 interval must be greater than 1 second.")
                                continue
                            send_command_to_pico(f"SET_CO2_INTERVAL,{interval}")
                        except ValueError:
                            print("Invalid input. Please enter a valid CO2 measurement interval.")
                            logging.warning("Invalid input for CO2 interval.")

                    elif command == '/cyc':
                        try:
                            new_cycle = int(input("Enter new sensor data query cycle duration (minutes): "))
                            if new_cycle < 1:
                                print("Cycle duration must be at least 1 minute.")
                                continue
                            send_command_to_pico(f"SET_CYCLE_MINS,{new_cycle}")
                        except ValueError:
                            print("Invalid input. Please enter a valid number.")
                            logging.warning("Invalid input for cycle duration.")

                    elif command == '/r':
                        send_command_to_pico("RESET_PICO")

                    elif command == '/s':
                        send_command_to_pico("SHUTDOWN")

                    elif command == '/w':
                        wake_pico()

                    elif command == '/e':
                        logging.info("Exiting control loop")
                        break

                    else:
                        print("Invalid command. Type '/h' for the list of available commands.")
                        logging.warning("Invalid command entered")

                except Exception as e:
                    logging.error(f"Error processing command: {e}")
                    print(f"Error processing command: {e}")

            # Display the prompt if it hasn't been displayed yet
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