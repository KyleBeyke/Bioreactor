"""
This script controls a bioreactor's Raspberry Pi using a Pico microcontroller. It communicates with the Pico via serial connection and performs various tasks such as time synchronization, sending commands to the Pico, handling sensor data, and sending notifications via Telegram.
The main functions of this script are:
- send_telegram_message: Sends a message via Telegram using a bot token and chat ID.
- log_command: Logs commands issued to the Pico in a CSV file.
- sync_time_with_pico: Sends a time synchronization command to the Pico.
- wake_pico: Wakes up the Pico from deep sleep.
- periodic_time_sync: Periodically syncs the time with the Pico.
- main: The main loop of the script that handles sensor data, time synchronization, and user input for commands.
The script also defines some constants and variables for calibration, CO2 threshold, and tracking the state of CO2 levels.
Note: This script requires the following dependencies: serial, time, csv, RPi.GPIO, cryptography.fernet, and requests.
"""

import serial
import time
import csv
import os  # To access environment variables and file paths
import RPi.GPIO as GPIO  # Import for controlling GPIO pins (used to wake the Pico)
from cryptography.fernet import Fernet
import requests
import base64  # Needed for encoding/decoding keys

# GPIO setup for waking up the Pico
WAKE_PIN = 17  # Choose an available GPIO pin on the Raspberry Pi (GPIO17 in this case)
GPIO.setmode(GPIO.BCM)
GPIO.setup(WAKE_PIN, GPIO.OUT, initial=GPIO.LOW)

# Initialize serial connection to Pico
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  # Adjust port as needed

# CSV file for logging commands on the Pi
filename = "commands_log.csv"

# Decrypt the stored bot token and chat ID from the secure file
def decrypt_data():
    secure_file_path = os.path.expanduser("~/.config/bioreactor_secure_config")
    
    # Load the encrypted data from the file
    with open(secure_file_path) as f:
        lines = f.readlines()
        encryption_key = base64.urlsafe_b64decode(lines[0].split('=')[1].strip())
        encrypted_bot_token = lines[1].split('=')[1].strip()
        encrypted_chat_id = lines[2].split('=')[1].strip()

    # Decrypt the bot token and chat ID
    cipher_suite = Fernet(encryption_key)
    bot_token = cipher_suite.decrypt(encrypted_bot_token.encode()).decode()
    chat_id = cipher_suite.decrypt(encrypted_chat_id.encode()).decode()

    return bot_token, chat_id

# Use the decrypted values in the application
bot_token, chat_id = decrypt_data()

# Function to send a message via Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")

# Function to log commands issued to the Pico
def log_command(command):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(filename, mode='a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, command])

# Function to send time sync command to Pico
def sync_time_with_pico():
    current_time = time.localtime()
    time_sync_command = f"SET_TIME,{current_time.tm_year},{current_time.tm_mon},{current_time.tm_mday},{current_time.tm_hour},{current_time.tm_min},{current_time.tm_sec}\n"
    ser.write(time_sync_command.encode())
    log_command(time_sync_command)
    print(f"Time synchronized with Pico: {time_sync_command}")

# Function to wake the Pico after deep sleep
def wake_pico():
    print("Waking Pico from deep sleep...")
    GPIO.output(WAKE_PIN, GPIO.HIGH)
    time.sleep(1)  # Hold the pin high for 1 second
    GPIO.output(WAKE_PIN, GPIO.LOW)
    print("Pico should be awake now.")

# Function to periodically sync the time
def periodic_time_sync(interval_seconds=600):
    last_sync = time.time()
    while True:
        current_time = time.time()
        if current_time - last_sync >= interval_seconds:
            sync_time_with_pico()
            last_sync = current_time
        yield

# Calibration and CO2 threshold
calibration_value = 400  # Replace this with your calibration value logic
co2_threshold = calibration_value * 1.2  # 120% of the calibration value

# Flags to track the state of CO2 levels
threshold_crossed = False  # Has CO2 exceeded the threshold?
alert_sent = False  # Ensure one alert is sent until the CO2 crosses the threshold again

# Main loop
time_sync_generator = periodic_time_sync()

try:
    sync_time_with_pico()  # Initial time sync with the Pico at startup

    while True:
        # Check for Pico wake-up after deep sleep or sensor data
        if ser.in_waiting > 0:
            sensor_data = ser.readline().decode('utf-8').strip()
            
            # Handle sensor data
            if "CO2" in sensor_data:
                # Parse the CO2 value from the sensor data
                co2 = float(sensor_data.split(":")[1].strip())
                print(f"CO2: {co2} ppm")

                # Check if CO2 has exceeded the 120% threshold
                if co2 > co2_threshold:
                    threshold_crossed = True
                    alert_sent = False  # Reset alert flag
                    print(f"CO2 level exceeded {co2_threshold} ppm")

                # If CO2 falls below the threshold after exceeding it
                if threshold_crossed and not alert_sent and co2 < co2_threshold:
                    message = f"ALERT: CO2 level has fallen below {co2_threshold} ppm! Current value: {co2} ppm."
                    send_telegram_message(message)
                    alert_sent = True
                    print(f"Notification sent: CO2 level below {co2_threshold} ppm")

            elif "Pico has restarted" in sensor_data:
                print(sensor_data)
            else:
                print(sensor_data)  # Display any other sensor data

        # Perform periodic time synchronization
        next(time_sync_generator)

        # Get user input for commands to send to the Pico
        command = input("Enter 'f' for feed, 'c' for recalibration, 's' for shutdown, 'r' for restart, or 'e' to exit: ").lower()

        if command == 'f':
            feed_amount = input("Enter feed amount (in grams): ")
            feed_command = f"FEED,{feed_amount}\n"
            ser.write(feed_command.encode())  # Send feed command to Pico
            log_command(feed_command)  # Log feed command on the Pi
            print(f"Feed command sent: {feed_amount} grams")

        elif command == 'c':
            co2_value = input("Enter CO2 value for recalibration: ")
            recalibration_command = f"CALIBRATE,{co2_value}\n"
            ser.write(recalibration_command.encode())  # Send recalibration command to Pico
            log_command(recalibration_command)  # Log recalibration command on the Pi
            print(f"Recalibration command sent for {co2_value} ppm")

        elif command == 's':
            shutdown_command = "SHUTDOWN\n"
            ser.write(shutdown_command.encode())  # Send shutdown command to Pico
            log_command(shutdown_command)  # Log shutdown command on the Pi
            print("Shutdown command sent to Pico")

        elif command == 'r':
            # Wake the Pico by toggling the GPIO pin
            wake_pico()
            print("Pico has been restarted")

        elif command == 'e':
            print("Exiting program...")
            break

        else:
            print("Invalid input. Try again.")

except KeyboardInterrupt:
    print("Program interrupted")

except Exception as e:
    print(f"Error: {e}")

finally:
    GPIO.cleanup()  # Clean up GPIO resources on exit
