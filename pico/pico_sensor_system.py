"""
pico_sensor_system.py

This script runs on the Raspberry Pi Pico to manage sensor readings and communication with the Raspberry Pi.
It supports:
- Reading data from the SCD30 CO2 sensor, BMP280 pressure sensor, and DS3231 RTC.
- Logging sensor data to an SD card.
- Responding to commands (feed operations, recalibration, shutdown, request data).
- Synchronizing time with the Raspberry Pi.
- Entering deep sleep and waking via GPIO.

The script includes error handling, logging, and improved modularity.
"""

import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
import digitalio
import storage
import adafruit_sdcard
import alarm
import supervisor  # Used for checking serial input
import microcontroller  # Used for safe reset

# Global default sensor data query cycle
sensor_query_cycle_mins = 5  # Time interval for querying sensor data (in minutes)
cycle = sensor_query_cycle_mins * 60  # Convert minutes to seconds

# Simple logging functions to mimic logging behavior
LOG_FILE = "/sd/pico_log.txt"

# Get current time from the RTC
def get_rtc_time():
    rtc_time = rtc.datetime
    return f"{rtc_time.tm_year}-{rtc_time.tm_mon:02}-{rtc_time.tm_mday:02} {rtc_time.tm_hour:02}:{rtc_time.tm_min:02}:{rtc_time.tm_sec:02}"

def log_info(message):
    timestamp = get_rtc_time()
    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{timestamp} INFO: {message}\n")
        print(f"{timestamp} INFO: {message}")
    except Exception as e:
        print(f"Failed to log info: {e}")

def log_error(message):
    timestamp = get_rtc_time()
    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{timestamp} ERROR: {message}\n")
        print(f"{timestamp} ERROR: {message}")
    except Exception as e:
        print(f"Failed to log error: {e}")

        # Function to reset the Pico        
def reset_pico():
    print("Resetting the Pico in 30 seconds...")
    time.sleep(30)  # Optional: allow time for operations to complete before reset
    try:
        log_info("Resetting the Pico now.")
    except Exception as e:
        print(f"Failed to log the Pico reset: {e}")
        print("Resetting the Pico now.")
    microcontroller.reset()

# Setup SPI for SD card
try:
    spi = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
    cs = digitalio.DigitalInOut(board.GP13)  # Chip select pin
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    time.sleep(2)  # Allow time for SD card to initialize
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    log_info("SD card mounted successfully.")
except Exception as e:
    print(f"Failed to mount SD card: {e}")
    reset_pico()

# I2C initialization for SCD30, BMP280, and DS3231 RTC
try:
    i2c = busio.I2C(board.GP21, board.GP20)
    scd30 = adafruit_scd30.SCD30(i2c)
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
    rtc = adafruit_ds3231.DS3231(i2c)  # Initialize DS3231 RTC
    log_info("I2C devices initialized successfully.")
except Exception as e:
    log_error(f"Failed to initialize I2C devices: {e}")
    reset_pico()

# Disable auto-calibration for SCD30
try:
    scd30.self_calibration_enabled = False
    scd30.measurement_interval = 5  # Set measurement interval to 5 seconds
    log_info("SCD30 auto-calibration disabled.")
except Exception as e:
    log_error(f"Failed to disable SCD30 auto-calibration: {e}")
    reset_pico()

def set_cycle(new_cycle):
    global cycle
    cycle = new_cycle * 60
    log_info(f"Sensor query cycle set to: {cycle} seconds")


# CSV file for logging sensor data
DATA_LOG_FILE = "/sd/sensor_data.csv"

# CSV logging function
def log_data_to_csv(timestamp, co2, temperature, humidity, pressure, altitude, feed_amount=None, recalibration=None):
    try:
        with open(DATA_LOG_FILE, mode='a') as csvfile:
            csvfile.write(f"{timestamp},{co2},{temperature},{humidity},{pressure},{altitude},{feed_amount},{recalibration}\n")
        log_info(f"Data logged: CO2: {co2} ppm, Temp: {temperature}°C, Humidity: {humidity}%, Pressure: {pressure} hPa, Altitude: {altitude} m, Feed Amount: {feed_amount}, Recalibration: {recalibration}")
    except Exception as e:
        log_error(f"Failed to log data to CSV: {e}")

# Function to update SCD30 altitude and pressure compensation
def update_scd30_compensation():
    try:
        pressure = bmp280.pressure
        altitude = bmp280.altitude
        scd30.ambient_pressure = int(pressure)  # Setting ambient pressure in pascals
        scd30.altitude = int(altitude)  # Set altitude in meters
        time.sleep(5)
        log_info(f"Compensation updated: Pressure: {pressure}, Altitude: {altitude}")
    except Exception as e:
        log_error(f"Failed to update compensation: {e}")

# Function to send sensor data and log to SD card
def send_sensor_data(feed=None, recalibration=None):
    retries = 3  # Retry mechanism if data is not available
    while not scd30.data_available and retries > 0:
        retries -= 1
        time.sleep(5)

    if retries == 0:
        log_error("Failed to get sensor data after multiple retries")
        return

    try:
        co2 = scd30.CO2
        temperature = scd30.temperature
        humidity = scd30.relative_humidity
        pressure = bmp280.pressure
        altitude = bmp280.altitude
        timestamp = get_rtc_time()
        sensor_data = f"{timestamp} | CO2: {co2:.2f} ppm, Temp: {temperature:.2f} °C, Humidity: {humidity:.2f} %, Pressure: {pressure:.2f} hPa, Altitude: {altitude:.2f} m"
        print(sensor_data)
        log_data_to_csv(timestamp, co2, temperature, humidity, pressure, altitude, feed, recalibration)
    except Exception as e:
        log_error(f"Failed to send sensor data: {e}")

# Function to shutdown Pico and enter deep sleep
def shutdown_pico():
    log_info("Shutting down Pico and entering deep sleep.")
    time.sleep(2)  # Ensure all operations complete
    wake_alarm = alarm.pin.PinAlarm(pin=board.GP15, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(wake_alarm)

# Function to sync RTC time with the Pi
def sync_rtc_time(sync_time_str):
    """Sync the RTC time using the SYNC_TIME command in format: SYNC_TIME,YYYY-MM-DD HH:MM:SS"""
    try:
        parts = sync_time_str.split(",")[1].strip().split(" ")
        date_parts = parts[0].split("-")
        time_parts = parts[1].split(":")
        year, month, day = map(int, date_parts)
        hour, minute, second = map(int, time_parts)
        rtc.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))
        log_info(f"RTC time synchronized to: {sync_time_str}")
    except Exception as e:
        log_error(f"Failed to sync RTC time: {e}")

# Function to handle incoming commands
def handle_commands(command):
    try:
        if command.startswith("FEED"):
            feed_amount = command.split(",")[1]
            log_info(f"Feed command received: {feed_amount} grams")
            send_sensor_data(feed_amount, None)
        
        elif command.startswith("CALIBRATE"):
            recalibration_value = int(command.split(",")[1])
            scd30.forced_recalibration_reference = recalibration_value
            log_info(f"Recalibration command received: {recalibration_value} ppm")
            send_sensor_data(None, recalibration_value)

        elif command == "REQUEST_DATA":
            send_sensor_data()

        elif command == "SHUTDOWN":
            shutdown_pico()

        elif command.startswith("SYNC_TIME"):
            sync_rtc_time(command)

        elif command == "REQUEST_RTC_TIME":
            timestamp = get_rtc_time()
            print(f"RTC time: {timestamp}")
            
        elif command == "SET_CYCLE_MINS":
            global cycle
            new_cycle = int(command.split(",")[1])
            set_cycle(new_cycle)

        elif command == "RESET_PICO":
            reset_pico()

        else:
            log_error("Invalid command received")

    except Exception as e:
        log_error(f"Failed to handle command: {e}")        

# Main control loop
def control_loop():
    log_info("Starting system... warming up sensors for 15 seconds.")
    time.sleep(15)  # Warm-up period for sensors

    global cycle

    # Initial sensor data send before entering the main loop
    log_info("Sending initial sensor data after warm-up period.")
    try:
        update_scd30_compensation()
        send_sensor_data()
    except Exception as e:
        log_error(f"Error during initial sensor data send: {e}")

    last_reading_time = time.monotonic()

    while True:
        current_time = time.monotonic()

        # Send sensor data every cycle duration (default 5 minutes)
        if current_time - last_reading_time >= cycle:
            try:
                update_scd30_compensation()
                send_sensor_data()
                last_reading_time = current_time
            except Exception as e:
                log_error(f"Error in sensor reading cycle: {e}")

        # Listen for commands from the Pi
        try:
            if supervisor.runtime.serial_bytes_available:
                command = input().strip()
                handle_commands(command)

        except Exception as e:
            log_error(f"Error processing command: {e}")

# Main program entry point
if __name__ == "__main__":
    control_loop()