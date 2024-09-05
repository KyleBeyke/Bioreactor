"""
This script is responsible for controlling a bioreactor system using a Raspberry Pi Pico microcontroller. It reads data from various sensors including an SCD30 CO2 sensor, a BMP280 temperature and pressure sensor, and a DS3231 RTC (Real-Time Clock). The script logs the sensor data to a CSV file on an SD card and communicates with a Raspberry Pi 4 for commands and synchronization.

Functions:
- log_data_to_csv(timestamp, co2, temperature, humidity, pressure=None, altitude=None, feed_amount=None, recalibration=None): Logs the sensor data to a CSV file.
- update_scd30_compensation(): Updates the SCD30 altitude and pressure compensation using BMP280 values.
- get_timestamp_from_rtc(): Retrieves the current time from the DS3231 RTC.
- update_rtc_time(year, month, day, hour, minute, second): Updates the DS3231 RTC time.
- send_sensor_data(): Sends the sensor data to the Raspberry Pi 4.
- shutdown_pico(): Shuts down the Pico safely and enters deep sleep.
- wake_up_message(): Sends a wake-up message to the Raspberry Pi 4 after waking up from deep sleep.
"""

import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
import storage
import sdcardio
import digitalio
import csv
import sys
import select
import microcontroller  # Used for safe shutdown and reset
import alarm  # Used for deep sleep and wake-up

# Initialize I2C for SCD30, BMP280, and DS3231 RTC
i2c = busio.I2C(board.GP21, board.GP20, frequency=50000)
scd = adafruit_scd30.SCD30(i2c)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
rtc = adafruit_ds3231.DS3231(i2c)

# Disable auto-calibration for SCD30
scd.self_calibration_enabled = False

# Set BMP280 reference sea level pressure (in hPa)
bmp280.sea_level_pressure = 1013.25

# Setup SPI for SD card
spi = busio.SPI(board.GP10, board.GP11, board.GP12)  # SPI pins for SD card module
cs = digitalio.DigitalInOut(board.GP13)  # Chip select pin for SD card module
sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# CSV file for logging data
filename = "/sd/co2_data.csv"

# Function to log data to the CSV file
def log_data_to_csv(timestamp, co2, temperature, humidity, pressure=None, altitude=None, feed_amount=None, recalibration=None):
    with open(filename, mode='a', newline='') as csvfile:
        fieldnames = ['timestamp', 'CO2', 'temperature', 'humidity', 'pressure', 'altitude', 'feed_amount', 'recalibration']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({
            'timestamp': timestamp,
            'CO2': co2,
            'temperature': temperature,
            'humidity': humidity,
            'pressure': pressure,
            'altitude': altitude,
            'feed_amount': feed_amount,
            'recalibration': recalibration
        })

# Function to update SCD30 altitude and pressure compensation using BMP280 values
def update_scd30_compensation():
    pressure = bmp280.pressure  # Pressure in hPa
    altitude = bmp280.altitude  # Altitude in meters

    # Update SCD30 compensation values
    scd.set_altitude_comp(int(altitude))  # Set altitude compensation (integer)
    scd.start_continous_measurement(int(pressure))  # Set ambient pressure compensation (in mbar)

    print(f"SCD30 compensation values updated. Waiting for sensor stabilization...")
    sys.stdout.flush()

    # Wait for sensor stabilization (e.g., 15 seconds)
    time.sleep(15)

    return pressure, altitude

# Function to get the current time from DS3231 RTC
def get_timestamp_from_rtc():
    now = rtc.datetime
    return f"{now.tm_year}-{now.tm_mon:02}-{now.tm_mday:02} {now.tm_hour:02}:{now.tm_min:02}:{now.tm_sec:02}"

# Function to update DS3231 RTC time
def update_rtc_time(year, month, day, hour, minute, second):
    rtc.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))

# Function to send sensor data to the Raspberry Pi 4
def send_sensor_data():
    if scd.data_available:
        co2 = scd.CO2
        temperature = scd.temperature
        humidity = scd.relative_humidity
        pressure = bmp280.pressure
        altitude = bmp280.altitude
        timestamp = get_timestamp_from_rtc()

        # Format the sensor data and send it to the Raspberry Pi
        sensor_data = f"{timestamp} | CO2: {co2:.2f} ppm, Temp: {temperature:.2f} °C, Humidity: {humidity:.2f} %, Pressure: {pressure:.2f} hPa, Altitude: {altitude:.2f} m\n"
        sys.stdout.write(sensor_data)
        sys.stdout.flush()

        # Log the data to the SD card
        log_data_to_csv(timestamp, co2, temperature, humidity, pressure, altitude)

# Function to shut down the Pico safely and enter deep sleep
def shutdown_pico():
    print("Shutting down the Pico... Closing all operations.")
    sys.stdout.flush()  # Flush any remaining output
    time.sleep(2)  # Allow time for any final operations

    # Enter deep sleep mode
    print("Entering deep sleep...")
    sys.stdout.flush()

    # Setup deep sleep with an alarm pin that wakes it on signal
    wake_alarm = alarm.pin.PinAlarm(pin=board.GP15, value=False, pull=True)  # Set a wake-up pin (adjust pin as needed)
    alarm.exit_and_deep_sleep_until_alarms(wake_alarm)

# Wake up and inform Raspberry Pi that the Pico has restarted
def wake_up_message():
    print("Pico has restarted after deep sleep.")
    sys.stdout.flush()

# If Pico just woke up from deep sleep, send restart message
if alarm.wake_alarm:
    wake_up_message()

# Main loop
last_reading_time = time.monotonic()
while True:
    current_time = time.monotonic()

    # Check if 15 minutes (900 seconds) have passed since the last reading
    if current_time - last_reading_time >= 900:  # 900 seconds = 15 minutes
        try:
            # Update pressure and altitude compensation, then wait for stabilization
            update_scd30_compensation()

            # After the sensor has stabilized, send sensor data to the Pi and log it
            send_sensor_data()

            last_reading_time = current_time  # Update last reading time

        except Exception as e:
            print(f"Error: {e}")

    # Continuously check for commands from Raspberry Pi 4 (via serial)
    try:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            command = input().strip()

            if command.startswith("SET_TIME"):  # Handle time sync command
                _, year, month, day, hour, minute, second = command.split(",")
                update_rtc_time(int(year), int(month), int(day), int(hour), int(minute), int(second))
                print(f"RTC time updated to: {year}-{month}-{day} {hour}:{minute}:{second}")
                sys.stdout.flush()

            elif command.startswith("CALIBRATE"):  # Handle recalibration command
                recalibration_value = int(command.split(",")[1])
                scd.set_forced_recalibration(recalibration_value)
                timestamp = get_timestamp_from_rtc()
                log_data_to_csv(timestamp, scd.CO2, scd.temperature, scd.relative_humidity, recalibration=recalibration_value)
                print(f"Recalibration set to: {recalibration_value} ppm")
                sys.stdout.flush()

            elif command.startswith("FEED"):  # Handle feed command
                feed_amount = command.split(",")[1]
                timestamp = get_timestamp_from_rtc()
                log_data_to_csv(timestamp, scd.CO2, scd.temperature, scd.relative_humidity, feed_amount=feed_amount)
                print(f"Feed logged: {feed_amount} grams")
                sys.stdout.flush()

            elif command.startswith("SHUTDOWN"):  # Handle shutdown command
                shutdown_pico()

    except Exception as e:
        print(f"Error processing command: {e}")