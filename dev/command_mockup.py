"""
command_mockup.py

This script simulates the command-line interface of the `pi_control_system.py` for testing purposes.
It injects fake data to mock communication between the Raspberry Pi and Pico, mimicking the sensor readings and command interactions.
The script supports commands like:
- /f: Feed the bioreactor.
- /c: Calibrate CO2 levels.
- /s: Shutdown the Pico.
- /r: Restart the Pico.
- /t: Set a new CO2 threshold.
- /help: Displays available commands.

This mockup ensures no physical hardware is required for testing the command interface.
"""

import random
import time
import logging

# Initialize logging
LOG_FILE = "mockup_log.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Mockup for receiving sensor data from Pico
def receive_fake_sensor_data():
    """Simulates the reception of sensor data from the Pico."""
    co2 = random.uniform(300, 1000)  # Simulating CO2 levels in ppm
    temperature = random.uniform(15, 30)  # Simulating temperature in °C
    humidity = random.uniform(20, 80)  # Simulating humidity in %
    return f"CO2: {co2:.2f} ppm, Temp: {temperature:.2f} °C, Humidity: {humidity:.2f} %"

# Mockup for RTC time request
def request_rtc_time():
    """Simulates receiving the RTC time from the Pico."""
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logging.info(f"RTC time received: {current_time}")
    return current_time

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

# Main mockup loop
def control_mockup_loop():
    """Main mockup loop to simulate Pico communication and commands."""
    print("Starting command mockup interface...")
    rtc_time = request_rtc_time()  # Simulate getting RTC time on startup
    print(f"RTC time received: {rtc_time}")

    try:
        while True:
            # Simulate receiving fake sensor data every 10 seconds
            sensor_data = receive_fake_sensor_data()
            logging.info(f"Fake sensor data received: {sensor_data}")
            print(sensor_data)

            # Get user input for commands
            command = input("Enter command (use '/help' for a list of commands): ").lower()

            if command == '/help':
                show_help_menu()

            elif command == '/f':
                feed_amount = input("Enter feed amount (grams): ")
                logging.info(f"Feed command executed: {feed_amount} grams")
                print(f"Feed command executed: {feed_amount} grams")

            elif command == '/c':
                co2_value = input("Enter CO2 value for recalibration: ")
                logging.info(f"Calibration command executed: {co2_value} ppm")
                print(f"Calibration command executed: {co2_value} ppm")

            elif command == '/s':
                logging.info("Shutdown command executed")
                print("Shutdown command executed.")

            elif command == '/r':
                logging.info("Restart command executed")
                print("Restart command executed.")

            elif command == '/t':
                new_threshold = input("Enter new CO2 threshold: ")
                logging.info(f"New CO2 threshold set: {new_threshold}")
                print(f"New CO2 threshold set: {new_threshold}")

            elif command == '/e':
                logging.info("Exiting mockup control loop")
                print("Exiting mockup...")
                break

            else:
                logging.warning("Invalid command entered")
                print("Invalid command. Use '/help' for available commands.")

            # Simulate a short delay between commands
            time.sleep(2)

    except KeyboardInterrupt:
        logging.warning("Program interrupted by user")

    except Exception as e:
        logging.error(f"Unexpected error in mockup loop: {e}")

if __name__ == "__main__":
    control_mockup_loop()
