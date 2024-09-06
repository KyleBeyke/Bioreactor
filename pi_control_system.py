"""
This script controls the bioreactor's Raspberry Pi, which communicates with a Pico microcontroller. It handles tasks such as time synchronization, sending commands to the Pico, handling sensor data, and sending notifications via Telegram.

Main Functions:
- send_telegram_message: Sends a message via Telegram using a bot token and chat ID.
- log_command: Logs commands issued to the Pico in a CSV file.
- sync_time_with_pico: Sends a time synchronization command to the Pico.
- wake_pico: Wakes up the Pico from deep sleep.
- periodic_time_sync: Periodically syncs the time with the Pico.
- set_co2_threshold: Updates CO2 threshold values from the console.
- main: The main loop handles sensor data, time synchronization, and user input for commands.

Dependencies:
- serial, time, csv, RPi.GPIO, cryptography.fernet, requests, os (for environment variable handling).
"""

import serial
import time
import csv
import os
import RPi.GPIO as GPIO
from cryptography.fernet import Fernet
import requests
import base64

# GPIO setup for waking up the Pico
WAKE_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(WAKE_PIN, GPIO.OUT, initial=GPIO.LOW)

# Serial connection to Pico
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# CSV file for logging commands
filename = "commands_log.csv"

# Decrypt the stored bot token and chat ID from the secure file
def decrypt_data():
    secure_file_path = os.path.expanduser("~/.config/bioreactor_secure_config")

    # Load the encrypted data from the file
    with open(os.path.join(secure_file_path, "encrypted_data.txt"), "rb") as f:
        lines = f.readlines()
        encrypted_bot_token = lines[0].strip()
        encrypted_chat_id = lines[1].strip()

    # Load the encryption key
    with open(os.path.join(secure_file_path, "secret_key.key"), "rb") as key_file:
        encryption_key = key_file.read()

    # Decrypt the bot token and chat ID
    cipher_suite = Fernet(encryption_key)
    bot_token = cipher_suite.decrypt(encrypted_bot_token).decode()
    chat_id = cipher_suite.decrypt(encrypted_chat_id).decode()

    return bot_token, chat_id

# Get decrypted bot token and chat ID
bot_token, chat_id = decrypt_data()

# Function to send a message via Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")

# Log issued commands
def log_command(command):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(filename, mode='a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, command])

# Sync time with the Pico
def sync_time_with_pico():
    current_time = time.localtime()
    time_sync_command = f"SET_TIME,{current_time.tm_year},{current_time.tm_mon},{current_time.tm_mday},{current_time.tm_hour},{current_time.tm_min},{current_time.tm_sec}\n"
    ser.write(time_sync_command.encode())
    log_command(time_sync_command)
    print(f"Time synchronized with Pico: {time_sync_command}")

# Wake up the Pico from deep sleep
def wake_pico():
    print("Waking Pico from deep sleep...")
    GPIO.output(WAKE_PIN, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(WAKE_PIN, GPIO.LOW)
    print("Pico should be awake now.")

# Periodic time synchronization
def periodic_time_sync(interval_seconds=600):
    last_sync = time.time()
    while True:
        current_time = time.time()
        if current_time - last_sync >= interval_seconds:
            sync_time_with_pico()
            last_sync = current_time
        yield

# Update CO2 threshold from the console
def set_co2_threshold():
    global co2_threshold
    new_threshold = input("Enter new CO2 threshold (ppm): ")
    try:
        co2_threshold = float(new_threshold)
        print(f"New CO2 threshold set to: {co2_threshold} ppm")
        log_command(f"CO2 threshold set to {co2_threshold} ppm")
    except ValueError:
        print("Invalid input. Please enter a numeric value.")

# Calibration and CO2 threshold
calibration_value = 400
co2_threshold = calibration_value * 1.2

# Main loop
time_sync_generator = periodic_time_sync()

try:
    sync_time_with_pico()

    while True:
        # Check for Pico wake-up or sensor data
        if ser.in_waiting > 0:
            sensor_data = ser.readline().decode('utf-8').strip()

            if "CO2" in sensor_data:
                # Parse the CO2 value from the sensor data
                co2 = float(sensor_data.split(":")[1].strip())
                print(f"CO2: {co2} ppm")

                # Send alert if CO2 exceeds threshold
                if co2 > co2_threshold:
                    print(f"ALERT: CO2 level exceeded {co2_threshold} ppm")
                    send_telegram_message(f"ALERT: CO2 level exceeded {co2_threshold} ppm! Current value: {co2} ppm")
                    log_command(f"CO2 exceeded {co2_threshold} ppm")

            elif "Pico has restarted" in sensor_data:
                print(sensor_data)
            else:
                print(sensor_data)

        # Perform periodic time synchronization
        next(time_sync_generator)

        # Get user input for commands to send to the Pico
        command = input("Enter 'f' for feed, 'c' for recalibration, 's' for shutdown, 'r' for restart, 't' for testing Telegram, or 'e' to exit: ").lower()

        if command == 'f':
            feed_amount = input("Enter feed amount (in grams): ")
            feed_command = f"FEED,{feed_amount}\n"
            ser.write(feed_command.encode())
            log_command(feed_command)
            print(f"Feed command sent: {feed_amount} grams")

        elif command == 'c':
            co2_value = input("Enter CO2 value for recalibration: ")
            recalibration_command = f"CALIBRATE,{co2_value}\n"
            ser.write(recalibration_command.encode())
            log_command(recalibration_command)
            print(f"Recalibration command sent for {co2_value} ppm")

        elif command == 's':
            shutdown_command = "SHUTDOWN\n"
            ser.write(shutdown_command.encode())
            log_command(shutdown_command)
            print("Shutdown command sent to Pico")

        elif command == 'r':
            wake_pico()
            print("Pico has been restarted")

        elif command == 't':
            send_telegram_message("Test message from bioreactor system.")
            print("Test message sent to Telegram")

        elif command == 'e':
            print("Exiting program...")
            break

        elif command == 'set-threshold':
            set_co2_threshold()

        else:
            print("Invalid input. Try again.")

except KeyboardInterrupt:
    print("Program interrupted")

except Exception as e:
    print(f"Error: {e}")

finally:
    GPIO.cleanup()