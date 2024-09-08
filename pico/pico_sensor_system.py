"""
pico_sensor_system.py

This script runs on the Raspberry Pi Pico to manage sensor readings and communication with the Raspberry Pi.
It supports:
- Reading data from the SCD30 CO2 sensor, BMP280 pressure sensor, and DS3231 RTC.
- Logging sensor data to an SD card.
- Responding to commands (feed operations, recalibration, shutdown).
- Synchronizing time with the Raspberry Pi.
- Entering deep sleep and waking via GPIO.
"""

import time
import board # type: ignore
import busio # type: ignore
import adafruit_scd30 # type: ignore
import adafruit_bmp280 # type: ignore
import adafruit_ds3231 # type: ignore
import storage # type: ignore
import sdcardio # type: ignore
import digitalio # type: ignore
import sys
import select
import microcontroller # type: ignore  # Used for safe shutdown and reset
import alarm # type: ignore  # Used for deep sleep and wake-up
import logging

# Initialize logging
LOG_FILE = "/sd/pico_log.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# I2C initialization for SCD30, BMP280, and DS3231 RTC
i2c = busio.I2C(board.GP21, board.GP20, frequency=50000)
scd30 = adafruit_scd30.SCD30(i2c)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
rtc = adafruit_ds3231.DS3231(i2c)

# Disable auto-calibration for SCD30
scd30.self_calibration_enabled = False

# Setup SPI for SD card
spi = busio.SPI(board.GP10, board.GP11, board.GP12)
cs = digitalio.DigitalInOut(board.GP13)
sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# CSV file for logging sensor data
DATA_LOG_FILE = "/sd/sensor_data.csv"

# Function to log data manually in CSV format with a header
def log_data_to_csv(timestamp, co2, temperature, humidity, pressure=None, altitude=None, feed_amount=None, recalibration=None):
    """ Logs sensor data manually to CSV file on SD card, adds header if file is empty """
    try:
        # Check if the file exists and if it's empty
        file_exists = False
        try:
            with open(DATA_LOG_FILE, 'r') as file:
                file_exists = True
        except OSError:
            # File doesn't exist yet, so we will create it and add a header
            pass
        
        # Open the file in append mode
        with open(DATA_LOG_FILE, mode='a') as file:
            # If file does not exist or is empty, write the header
            if not file_exists:
                file.write("timestamp,CO2,temperature,humidity,pressure,altitude,feed_amount,recalibration\n")
            
            # Create a CSV row as a string
            row = f"{timestamp},{co2},{temperature},{humidity},{pressure},{altitude},{feed_amount},{recalibration}\n"
            # Write the row to the file
            file.write(row)
        logging.info(f"Data logged: CO2: {co2} ppm, Temp: {temperature}°C, Humidity: {humidity}%")
    except Exception as e:
        logging.error(f"Failed to log data to CSV: {e}")

# Function to update SCD30 altitude and pressure compensation using BMP280
def update_scd30_compensation():
    """ Updates altitude and pressure compensation for the SCD30 based on BMP280 data """
    try:
        pressure = bmp280.pressure
        altitude = bmp280.altitude
        scd30.set_altitude_comp(int(altitude))
        scd30.start_continous_measurement(int(pressure))
        logging.info(f"Compensation updated: Pressure: {pressure}, Altitude: {altitude}")
    except Exception as e:
        logging.error(f"Failed to update compensation: {e}")

# Function to get the current timestamp from the RTC
def get_timestamp_from_rtc():
    """ Retrieves the current timestamp from DS3231 RTC """
    now = rtc.datetime
    return f"{now.tm_year}-{now.tm_mon:02}-{now.tm_mday:02} {now.tm_hour:02}:{now.tm_min:02}:{now.tm_sec:02}"

# Function to send the RTC time to the Raspberry Pi on request
def send_rtc_time():
    """ Send RTC time to the Raspberry Pi when requested """
    timestamp = get_timestamp_from_rtc()
    sys.stdout.write(f"RTC_TIME,{timestamp}\n")
    sys.stdout.flush()

# Function to send sensor data to the Raspberry Pi
def send_sensor_data():
    """ Sends sensor data to the Raspberry Pi and logs it to the SD card """
    if scd30.data_available:
        try:
            co2 = scd30.CO2
            temperature = scd30.temperature
            humidity = scd30.relative_humidity
            pressure = bmp280.pressure
            altitude = bmp280.altitude
            timestamp = get_timestamp_from_rtc()
            sensor_data = f"{timestamp} | CO2: {co2:.2f} ppm, Temp: {temperature:.2f} °C, Humidity: {humidity:.2f} %, Pressure: {pressure:.2f} hPa, Altitude: {altitude:.2f} m"
            sys.stdout.write(sensor_data + "\n")
            sys.stdout.flush()
            log_data_to_csv(timestamp, co2, temperature, humidity, pressure, altitude)
        except Exception as e:
            logging.error(f"Failed to send sensor data: {e}")

# Function to handle Pico shutdown and enter deep sleep
def shutdown_pico():
    """ Shuts down the Pico safely and enters deep sleep """
    logging.info("Shutting down Pico and entering deep sleep.")
    sys.stdout.flush()
    time.sleep(2)  # Ensure all operations complete
    wake_alarm = alarm.pin.PinAlarm(pin=board.GP15, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(wake_alarm)

# Function to update RTC time from Raspberry Pi command
def update_rtc_time(year, month, day, hour, minute, second):
    """ Updates the RTC time based on values received from the Raspberry Pi """
    rtc.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))
    logging.info(f"RTC time updated to: {year}-{month}-{day} {hour}:{minute}:{second}")

# Main loop
last_reading_time = time.monotonic()

while True:
    current_time = time.monotonic()

    # Check if 15 minutes (900 seconds) have passed since the last reading
    if current_time - last_reading_time >= 900:
        try:
            update_scd30_compensation()
            time.sleep(15)  # Wait for sensor stabilization
            send_sensor_data()
            last_reading_time = current_time
        except Exception as e:
            logging.error(f"Error in sensor reading cycle: {e}")

    # Continuously check for commands from Raspberry Pi
    try:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            command = input().strip()

            if command.startswith("SET_TIME"):
                _, year, month, day, hour, minute, second = command.split(",")
                update_rtc_time(int(year), int(month), int(day), int(hour), int(minute), int(second))

            elif command == "REQUEST_RTC_TIME":
                send_rtc_time()

            elif command.startswith("CALIBRATE"):
                recalibration_value = int(command.split(",")[1])
                scd30.set_forced_recalibration(recalibration_value)
                timestamp = get_timestamp_from_rtc()
                log_data_to_csv(timestamp, scd30.CO2, scd30.temperature, scd30.relative_humidity, recalibration=recalibration_value)
                logging.info(f"Recalibration set to {recalibration_value} ppm")

            elif command.startswith("FEED"):
                feed_amount = command.split(",")[1]
                timestamp = get_timestamp_from_rtc()
                log_data_to_csv(timestamp, scd30.CO2, scd30.temperature, scd30.relative_humidity, feed_amount=feed_amount)
                logging.info(f"Feed logged: {feed_amount} grams")

            elif command.startswith("SHUTDOWN"):
                shutdown_pico()

    except Exception as e:
        logging.error(f"Error processing command: {e}")
