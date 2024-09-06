import serial
import time
import csv
import os
import RPi.GPIO as GPIO
import requests

# GPIO setup for waking up the Pico
WAKE_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(WAKE_PIN, GPIO.OUT, initial=GPIO.LOW)

# Initialize serial connection to Pico
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

# CSV file for logging commands on the Pi
filename = "commands_log.csv"

# Load bot token and chat ID from environment variables
bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")

# Ensure the environment variables are set
if not bot_token or not chat_id:
    raise EnvironmentError("Bot token or chat ID environment variable not set. Ensure 'BOT_TOKEN' and 'CHAT_ID' are set.")

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
    time.sleep(1)
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

# CO2 threshold default (can be modified with commands)
co2_threshold = 480

# Function to set a new CO2 threshold
def set_co2_threshold():
    global co2_threshold
    new_threshold = input("Enter new CO2 threshold in ppm: ")
    try:
        co2_threshold = float(new_threshold)
        print(f"CO2 threshold updated to {co2_threshold} ppm")
    except ValueError:
        print("Invalid input. Please enter a numeric value.")

# Function to view the current CO2 threshold
def view_co2_threshold():
    print(f"Current CO2 threshold: {co2_threshold:.2f} ppm")

# Main loop
time_sync_generator = periodic_time_sync()

try:
    sync_time_with_pico()

    while True:
        # Check for Pico wake-up after deep sleep or sensor data
        if ser.in_waiting > 0:
            sensor_data = ser.readline().decode('utf-8').strip()

            # Handle sensor data
            if "CO2" in sensor_data:
                co2_value = float(sensor_data.split(":")[1].strip())
                print(f"CO2: {co2_value} ppm")

                # Check if CO2 has exceeded the 120% threshold
                if co2_value > co2_threshold:
                    print(f"CO2 level exceeded {co2_threshold} ppm")

                # If CO2 falls below the threshold after exceeding it
                if co2_value < co2_threshold:
                    message = f"ALERT: CO2 level has fallen below {co2_threshold} ppm! Current value: {co2_value} ppm."
                    send_telegram_message(message)
                    print(f"Notification sent: CO2 level below {co2_threshold} ppm")

        # Perform periodic time synchronization
        next(time_sync_generator)

        # Get user input for commands
        command = input("Enter 'f' for feed, 'c' for recalibration, 's' for shutdown, 'r' for restart, 't' to set CO2 threshold, or 'e' to exit: ").lower()

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
            set_co2_threshold()

        elif command == 'e':
            print("Exiting program...")
            break

        else:
            print("Invalid input. Try again.")

except KeyboardInterrupt:
    print("Program interrupted")

finally:
    GPIO.cleanup()
