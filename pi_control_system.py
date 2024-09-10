"""
pi_control_system.py

This script controls the bioreactor's Raspberry Pi, which communicates with a Pico microcontroller.
The script manages:
- Sensor data acquisition (CO2, temperature, etc.)
- Commands (feed, calibration, shutdown, reset, set altitude, set pressure, set CO2 interval, etc.)
- Time synchronization with Pico's RTC.
- Sending alerts via Telegram when CO2 levels cross a threshold.
- Logging commands and data for debugging and analysis.

Refined with modularity, error handling, logging, and full command support for the Pico.
"""

import serial
import time
import csv
import os
import logging
import RPi.GPIO as GPIO
from cryptography.fernet import Fernet
import requests
import sys
import select

# Initialize logging
LOG_FILE = "bioreactor_log.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# GPIO setup for waking up the Pico
WAKE_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(WAKE_PIN, GPIO.OUT, initial=GPIO.LOW)

# Serial setup
SERIAL_PORT = '/dev/ttyACM0'
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
            logging.info("Telegram message sent successfully!")
            print("Telegram message sent successfully!")
        else:
            logging.error(f"Failed to send message. Status code: {response.status_code}")
            print(f"Failed to send Telegram message. Status code: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Telegram message failed: {e}")
        print(f"Telegram message failed: {e}")

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
                    print(f"RTC time received: {rtc_time}")
                    return rtc_time
    except Exception as e:
        logging.error(f"Failed to request RTC time: {e}")
        print(f"Failed to request RTC time: {e}")

# Wake up the Pico from deep sleep
def wake_pico():
    """Sends a GPIO signal to wake up the Pico from deep sleep."""
    try:
        GPIO.output(WAKE_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(WAKE_PIN, GPIO.LOW)
        logging.info("Pico woken up from deep sleep")
        print("Pico woken up from deep sleep")
    except Exception as e:
        logging.error(f"Error waking up Pico: {e}")
        print(f"Error waking up Pico: {e}")

# Function to display the help menu
def show_help_menu():
    """Displays the available command options."""
    help_menu = """
    /h   : Show this help menu
    /d   : Request sensor data
    /f   : Feed - Enter the feed amount in grams
    /cal : Calibrate - Enter the CO2 value for recalibration
    /t   : Set CO2 threshold value
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

# Main control function
def control_loop():
    """Main loop to handle Pico communication and commands."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)

    except serial.SerialException as e:
        logging.error(f"Failed to open serial port: {e}")
        print(f"Failed to open serial port: {e}")
        return

    try:
        while True:
            # Handle incoming serial data from Pico
            try:
                if ser.in_waiting > 0:
                    serial_data = ser.readline().decode('utf-8').strip()
                    if serial_data == '':
                        raise TimeoutError("No data received within the timeout period.")
                    print(f"Data received: {serial_data}")
                    logging.info(f"Received data: {serial_data}")
            except (serial.SerialException, TimeoutError) as e:
                logging.error(f"Error with serial communication: {e}")
                print(f"Error: {e}")

            # Non-blocking user input check
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                command = sys.stdin.readline().strip().lower()

                try:
                    if command == '/h':
                        show_help_menu()

                    elif command == '/d':
                        request_data_command = "REQUEST_DATA\n"
                        ser.write(request_data_command.encode())
                        log_command(request_data_command)
                        logging.info("Data request command sent")

                    elif command == '/f':
                        try:
                            feed_amount = int(input("Enter feed amount (grams): "))
                            if feed_amount <= 0:
                                print("Feed amount must be a positive number.")
                                continue
                            feed_command = f"FEED,{feed_amount}\n"
                            ser.write(feed_command.encode())
                            log_command(feed_command)
                            logging.info(f"Feed command sent: {feed_amount} grams")
                        except ValueError:
                            print("Invalid input. Please enter a valid number.")
                            logging.warning("Invalid input for feed amount.")

                    elif command == '/cal':
                        try:
                            co2_value = int(input("Enter CO2 value for recalibration: "))
                            recalibration_command = f"CALIBRATE,{co2_value}\n"
                            ser.write(recalibration_command.encode())
                            log_command(recalibration_command)
                            logging.info(f"Recalibration command sent for {co2_value} ppm")
                        except ValueError:
                            print("Invalid input. Please enter a valid CO2 value.")
                            logging.warning("Invalid input for CO2 recalibration.")

                    elif command == '/alt':
                        try:
                            altitude = int(input("Enter new altitude for SCD30 sensor (meters): "))
                            if altitude < 0:
                                print("Altitude cannot be negative.")
                                continue
                            altitude_command = f"SET_ALTITUDE,{altitude}\n"
                            ser.write(altitude_command.encode())
                            log_command(altitude_command)
                            logging.info(f"Altitude set to: {altitude} meters")
                        except ValueError:
                            print("Invalid input. Please enter a valid altitude.")
                            logging.warning("Invalid input for altitude.")

                    elif command == '/p':
                        try:
                            pressure = int(input("Enter new pressure reference for BMP280 sensor (hPa): "))
                            if pressure <= 0:
                                print("Pressure must be a positive number.")
                                continue
                            pressure_command = f"SET_PRESSURE,{pressure}\n"
                            ser.write(pressure_command.encode())
                            log_command(pressure_command)
                            logging.info(f"Pressure reference set to: {pressure} hPa")
                        except ValueError:
                            print("Invalid input. Please enter a valid pressure reference.")
                            logging.warning("Invalid input for pressure reference.")

                    elif command == '/int':
                        try:
                            interval = int(input("Enter CO2 measurement interval for SCD30 sensor (seconds): "))
                            if interval < 2:
                                print("CO2 interval must be greater than 1 second.")
                                continue
                            interval_command = f"SET_CO2_INTERVAL,{interval}\n"
                            ser.write(interval_command.encode())
                            log_command(interval_command)
                            logging.info(f"CO2 measurement interval set to: {interval} seconds")
                        except ValueError:
                            print("Invalid input. Please enter a valid CO2 measurement interval.")
                            logging.warning("Invalid input for CO2 interval.")

                    elif command == '/cyc':
                        try:
                            new_cycle = int(input("Enter new sensor data query cycle duration (minutes): "))
                            if new_cycle < 1:
                                print("Cycle duration must be at least 1 minute.")
                                continue
                            cycle_command = f"SET_CYCLE_MINS,{new_cycle}\n"
                            ser.write(cycle_command.encode())
                            log_command(cycle_command)
                            logging.info(f"Sensor data query cycle set to: {new_cycle} minutes")
                        except ValueError:
                            print("Invalid input. Please enter a valid number.")
                            logging.warning("Invalid input for cycle duration.")

                    elif command == '/r':
                        reset_command = "RESET_PICO\n"
                        ser.write(reset_command.encode())
                        log_command(reset_command)
                        logging.info("Reset command sent to Pico")

                    elif command == '/e':
                        logging.info("Exiting control loop")
                        break

                    else:
                        logging.warning("Invalid command entered")
                        print("Invalid command. Type '/h' for the list of available commands.")

                except Exception as e:
                    logging.error(f"Error processing command: {e}")
                    print(f"Error processing command: {e}")

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