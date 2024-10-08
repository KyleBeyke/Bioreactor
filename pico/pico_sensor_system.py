"""
pico_sensor_system.py

This script runs on the Raspberry Pi Pico to manage sensor readings and communication with the Raspberry Pi.
It supports:
- Reading data from the SCD30 CO2 sensor, BMP280 pressure sensor, DS3231 RTC, and DS18B20 temperature sensor.
- Logging sensor data to an SD card.
- Responding to commands (feed operations, recalibration, shutdown, request data).
- Synchronizing time with the Raspberry Pi.
- Entering deep sleep and waking via GPIO.
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
import supervisor
import microcontroller
import traceback
from adafruit_onewire.bus import OneWireBus  # For OneWire communication
import adafruit_ds18x20  # For DS18B20 temperature sensor

# Global default sensor data query cycle
sensor_query_cycle_mins = 3  # Time interval for querying sensor data (in minutes)
cycle = sensor_query_cycle_mins * 60  # Convert minutes to seconds

# Function to reset the Pico
def reset_pico():
    """Resets the Pico after a 30-second wait to allow safe shutdown of tasks."""
    print("Resetting the Pico in 30 seconds...")
    time.sleep(30)
    microcontroller.reset()

# I2C initialization with retries
for attempt in range(3):
    try:
        i2c = busio.I2C(board.GP21, board.GP20)
        scd30 = adafruit_scd30.SCD30(i2c)
        bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
        rtc = adafruit_ds3231.DS3231(i2c)
        print("I2C devices initialized successfully.")
        break
    except Exception as e:
        print(f"Failed to initialize I2C devices on attempt {attempt + 1}: {e}")
        if attempt == 2:
            reset_pico()

# DS18B20 temperature sensor initialization
for attempt in range(3):
    try:
        onewire_bus = OneWireBus(board.GP18)
        devices = onewire_bus.scan()
        if not devices:
            raise RuntimeError("No DS18B20 sensor found!")

        ds18b20 = adafruit_ds18x20.DS18X20(onewire_bus, devices[0])
        print(f"DS18B20 initialized successfully.")
        break
    except Exception as e:
        print(f"Failed to initialize DS18B20 on attempt {attempt + 1}: {e}")
        if attempt == 2:
            reset_pico()

# Get current time from the RTC
def get_rtc_time():
    rtc_time = rtc.datetime
    return f"{rtc_time.tm_year}-{rtc_time.tm_mon:02}-{rtc_time.tm_mday:02} {rtc_time.tm_hour:02}:{rtc_time.tm_min:02}:{rtc_time.tm_sec:02}"

# Logging file path on SD card
LOG_FILE = "/sd/pico_log.txt"

def log_info(message):
    """Logs informational messages to the SD card and prints to console."""
    timestamp = get_rtc_time()
    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{timestamp} INFO: {message}\n")
        print(f"{timestamp} INFO: {message}")
    except Exception as e:
        print(f"Failed to log info: {e}")

def log_error(message):
    """Logs error messages to the SD card and prints to console."""
    timestamp = get_rtc_time()
    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{timestamp} ERROR: {message}\n")
        print(f"{timestamp} ERROR: {message}")
    except Exception as e:
        print(f"Failed to log error: {e}")

def log_traceback_error(e):
    """Logs detailed error messages with traceback information."""
    timestamp = get_rtc_time()
    error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{timestamp} TRACEBACK ERROR: {error_message}\n")
        print(f"{timestamp} TRACEBACK ERROR: {error_message}")
    except Exception as log_e:
        print(f"Failed to log traceback error: {log_e}")

# Setup SPI for SD card with retries
for attempt in range(3):
    try:
        spi = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
        cs = digitalio.DigitalInOut(board.GP13)
        sdcard = adafruit_sdcard.SDCard(spi, cs)
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd")
        log_info("SD card mounted successfully.")
        break
    except Exception as e:
        print(f"Failed to mount SD card on attempt {attempt + 1}: {e}")
        if attempt == 2:
            reset_pico()

# Setup SCD30 values
try:
    scd30.self_calibration_enabled = False  # Disable auto-calibration
    scd30.measurement_interval = 5  # Set measurement interval to 5 seconds
    scd30.altitude = 139  # Set altitude for pressure compensation
    log_info("SCD30 auto-calibration disabled.")
except Exception as e:
    log_traceback_error(e)
    log_error("Failed to disable SCD30 auto-calibration.")
    reset_pico()

def set_altitude(new_altitude):
    """Sets the altitude for the SCD30 sensor."""
    global scd30
    try:
        new_altitude = int(new_altitude)
        scd30.altitude = new_altitude
        log_info(f"SCD30 altitude set to: {new_altitude} meters")
    except Exception as e:
        log_traceback_error(e)
        log_error("Failed to set SCD30 altitude.")

def set_co2_interval(interval):
    """Sets the CO2 measurement interval for the SCD30 sensor."""
    try:
        if int(interval) < 2:
            log_error("Interval value must be greater than 1 second.")
            return
        scd30.measurement_interval = int(interval)
        log_info(f"SCD30 CO2 measurement interval set to: {interval} second(s)")
    except Exception as e:
        log_traceback_error(e)
        log_error("Failed to set SCD30 CO2 measurement interval.")

# Set BMP280 location reference sea level pressure
try:
    bmp280.sea_level_pressure = 1023
    log_info(f"BMP280 reference sea level pressure set: {bmp280.sea_level_pressure} hPa")
except Exception as e:
    log_traceback_error(e)
    log_error("Failed to set BMP280 reference sea level pressure.")
    reset_pico()

def set_pressure_reference(pressure):
    """Sets the BMP280 reference sea level pressure."""
    try:
        bmp280.sea_level_pressure = pressure
        log_info(f"BMP280 reference sea level pressure set: {pressure} hPa")
    except Exception as e:
        log_traceback_error(e)
        log_error("Failed to set BMP280 reference sea level pressure.")

def set_cycle(new_cycle):
    """Sets the new sensor query cycle duration."""
    global cycle
    try:
        if new_cycle < 1:
            log_error("Cycle duration must be at least 1 minute.")
            return
        cycle = new_cycle * 60
        log_info(f"Sensor query cycle set to: {cycle} second(s)")
    except Exception as e:
        log_traceback_error(e)
        log_error("Failed to set sensor query cycle.")

# CSV logging function
DATA_LOG_FILE = "/sd/sensor_data.csv"

def log_data_to_csv(timestamp, co2, probe_temp, sensor_temp, humidity, pressure, feed_amount=None, recalibration=None):
    """Logs sensor data to the CSV file on the SD card."""
    try:
        with open(DATA_LOG_FILE, mode='a') as csvfile:
            csvfile.write(f"{timestamp},{co2},{probe_temp},{sensor_temp},{humidity},{pressure},{feed_amount if feed_amount is not None else 'N/A'},{recalibration if recalibration is not None else 'N/A'}\n")
        log_info(f"Data logged: CO2: {co2} ppm, Media Temp: {probe_temp}, Sensor Temp: {sensor_temp}°C, Humidity: {humidity}%, Pressure: {pressure} hPa, Feed Amount: {feed_amount}, Recalibration: {recalibration}")
    except Exception as e:
        log_traceback_error(e)
        log_error("Failed to log sensor data to CSV.")

# Function to update SCD30 altitude and pressure compensation
def update_scd30_compensation():
    """Updates the SCD30 sensor compensation values based on BMP280 readings."""
    try:
        pressure = bmp280.pressure
        scd30.ambient_pressure = int(pressure)
        time.sleep(5)
        log_info(f"Compensation updated: Pressure: {pressure} hPa")
    except Exception as e:
        log_traceback_error(e)
        log_error("Failed to update SCD30 compensation values.")

# Send sensor data and log to SD card with retries
def send_sensor_data(feed=None, recalibration=None):
    """Sends sensor data to SD card and logs it, with retries on failure."""
    retries = 3
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
        ds18b20_temperature = ds18b20.temperature
        pressure = bmp280.pressure
        timestamp = get_rtc_time()
        # Log with conditionally formatting feed and recalibration values
        sensor_data = f"SENSOR DATA:{timestamp},{co2:.2f},{ds18b20_temperature:.2f},{temperature:.2f},{humidity:.2f},{pressure:.2f},{feed if feed is not None else 'N/A'},{recalibration if recalibration is not None else 'N/A'}"
        print(sensor_data)
        log_data_to_csv(timestamp, co2, ds18b20_temperature, temperature, humidity, pressure, feed, recalibration)
    except Exception as e:
        log_traceback_error(e)
        log_error("Error while sending sensor data.")

# Function to shutdown Pico and enter deep sleep
def shutdown_pico():
    """Shuts down the Pico and enters deep sleep."""
    log_info("Shutting down Pico and entering deep sleep.")
    time.sleep(2)
    wake_alarm = alarm.pin.PinAlarm(pin=board.GP15, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(wake_alarm)

# Function to sync RTC time with the Pi
def sync_rtc_time(sync_time_str):
    """Syncs the RTC time using the SYNC_TIME command."""
    try:
        parts = sync_time_str.split(",")[1].strip().split(" ")
        date_parts = parts[0].split("-")
        time_parts = parts[1].split(":")
        year, month, day = map(int, date_parts)
        hour, minute, second = map(int, time_parts)
        rtc.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))
        log_info(f"RTC time synchronized to: {sync_time_str}")
    except Exception as e:
        log_traceback_error(e)

# Function to handle incoming commands
def handle_commands(command):
    """Handles commands from the Raspberry Pi."""
    try:
        log_info(f"Received command: {command}")
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
            log_info("Data request command received.")
            send_sensor_data()

        elif command == "SHUTDOWN":
            log_info("Shutdown command received.")
            shutdown_pico()

        elif command.startswith("SYNC_TIME"):
            log_info("Time sync command received.")
            sync_rtc_time(command)

        elif command == "REQUEST_RTC_TIME":
            log_info("RTC time request command received.")
            timestamp = get_rtc_time()
            print(f"RTC time: {timestamp}")

        elif command.startswith("SET_ALTITUDE"):
            altitude = command.split(",")[1]
            log_info(f"Set altitude command received: {altitude} meters")
            set_altitude(altitude)

        elif command.startswith("SET_PRESSURE"):
            pressure = int(command.split(",")[1])
            log_info(f"Set pressure command received: {pressure} hPa")
            set_pressure_reference(pressure)

        elif command.startswith("SET_CYCLE_MINS"):
            new_cycle = int(command.split(",")[1])
            log_info(f"Set cycle command received: {new_cycle} minute(s)")
            set_cycle(new_cycle)

        elif command.startswith("SET_CO2_INTERVAL"):
            interval = command.split(",")[1]
            log_info(f"Set CO2 interval command received: {interval} second(s)")
            set_co2_interval(interval)

        elif command == "RESET_PICO":
            log_info("Reset command received.")
            reset_pico()

        else:
            log_error("Invalid command received")

    except Exception as e:
        log_traceback_error(e)

# Main control loop
def control_loop():
    """Main loop that handles periodic sensor readings and command processing."""
    log_info("Starting system... warming up sensors for 15 seconds.")
    time.sleep(15)

    global cycle

    log_info("Sending initial sensor data after warm-up period.")
    try:
        update_scd30_compensation()
        send_sensor_data()
    except Exception as e:
        log_traceback_error(e)

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
                log_traceback_error(e)

        # Listen for commands from the Pi
        try:
            if supervisor.runtime.serial_bytes_available:
                command = input().strip()
                handle_commands(command)

        except Exception as e:
            log_traceback_error(e)

# Main program entry point
if __name__ == "__main__":
    control_loop()
