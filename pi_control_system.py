import serial
import time
import csv
import RPi.GPIO as GPIO  # Import for controlling GPIO pins (used to wake the Pico)

# GPIO setup for waking up the Pico
WAKE_PIN = 17  # Choose an available GPIO pin on the Raspberry Pi (GPIO17 in this case)
GPIO.setmode(GPIO.BCM)
GPIO.setup(WAKE_PIN, GPIO.OUT, initial=GPIO.LOW)

# Initialize serial connection to Pico
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)  # Adjust port as needed

# CSV file for logging commands on the Pi
filename = "commands_log.csv"

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

# Main loop
time_sync_generator = periodic_time_sync()

try:
    sync_time_with_pico()  # Initial time sync with the Pico at startup

    while True:
        # Check for Pico wake-up after deep sleep
        if ser.in_waiting > 0:
            sensor_data = ser.readline().decode('utf-8').strip()
            if "Pico has restarted" in sensor_data:
                print(sensor_data)
            else:
                print(sensor_data)  # Display sensor data in the terminal

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
