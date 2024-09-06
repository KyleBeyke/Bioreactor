"""
This script runs on the Raspberry Pi Pico to handle the bioreactor system's sensor data collection, logging, and communication with the Raspberry Pi 4.
It interacts with the SCD30 CO2 sensor, BMP280 sensor for pressure and altitude, and the DS3231 RTC for timekeeping.
The Pico sends data to the Raspberry Pi, logs readings to an SD card, and enters deep sleep upon receiving shutdown commands.

Main Functions:
- log_data_to_csv: Logs sensor data and events (feed, recalibration) to a CSV file.
- update_scd30_compensation: Updates the SCD30 sensor with BMP280 altitude and pressure data.
- get_timestamp_from_rtc: Retrieves the current time from the DS3231 RTC.
- send_sensor_data: Sends sensor data to the Raspberry Pi.
- shutdown_pico: Shuts down the Pico and enters deep sleep.
- handle_commands: Processes commands received from the Raspberry Pi.
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
spi = busio.SPI(board.GP10, board.GP11, board.GP12)
cs = digitalio.DigitalInOut(board.GP13)
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
    scd.set_altitude_comp(int(altitude))
    scd.start_continous_measurement(int(pressure))  # Ambient pressure in mbar

    print("SCD30 compensation values updated. Waiting for sensor stabilization...")
    time.sleep(15)  # Wait for sensor stabilization

    return pressure, altitude

# Function to get the current time from DS3231 RTC
def get_timestamp_from_rtc():
    now = rtc.datetime
    return f"{now.tm_year}-{now.tm_mon:02}-{now.tm_mday:02} {now.tm_hour:02}:{now.tm_min:02}:{now.tm_sec:02}"

# Function to send sensor data to the Raspberry Pi
def send_sensor_data():
    if scd.data_available:
        co2 = scd.CO2
        temperature = scd.temperature
        humidity = scd.relative_humidity
        pressure = bmp280.pressure
        altitude = bmp280.altitude
        timestamp = get_timestamp_from_rtc()

        sensor_data = f"{timestamp} | CO2: {co2:.2f} ppm, Temp: {temperature:.2f} °C, Humidity: {humidity:.2f} %, Pressure: {pressure:.2f} hPa, Altitude: {altitude:.2f} m\n"
        print(sensor_data)

        # Log the data to the SD card
        log_data_to_csv(timestamp, co2, temperature, humidity, pressure, altitude)

# Function to handle commands from Raspberry Pi
def handle_commands(command):
    if command.startswith("SET_TIME"):
        _, year, month, day, hour, minute, second = command.split(",")
        rtc.datetime = time.struct_time((int(year), int(month), int(day), int(hour), int(minute), int(second), 0, -1, -1))
        print(f"RTC time updated to: {year}-{month}-{day} {hour}:{minute}:{second}")

    elif command.startswith("CALIBRATE"):
        recalibration_value = int(command.split(",")[1])
        scd.set_forced_recalibration(recalibration_value)
        timestamp = get_timestamp_from_rtc()
        log_data_to_csv(timestamp, scd.CO2, scd.temperature, scd.relative_humidity, recalibration=recalibration_value)
        print(f"Recalibration set to: {recalibration_value} ppm")

    elif command.startswith("FEED"):
        feed_amount = command.split(",")[1]
        timestamp = get_timestamp_from_rtc()
        log_data_to_csv(timestamp, scd.CO2, scd.temperature, scd.relative_humidity, feed_amount=feed_amount)
        print(f"Feed logged: {feed_amount} grams")

    elif command.startswith("SHUTDOWN"):
        shutdown_pico()

# Function to shut down the Pico and enter deep sleep
def shutdown_pico():
    print("Shutting down the Pico... Closing all operations.")
    time.sleep(2)
    print("Entering deep sleep...")

    # Setup deep sleep with an alarm pin that wakes it on signal
    wake_alarm = alarm.pin.PinAlarm(pin=board.GP15, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(wake_alarm)

# Wake up and inform Raspberry Pi that the Pico has restarted
def wake_up_message():
    print("Pico has restarted after deep sleep.")

if alarm.wake_alarm:
    wake_up_message()

# Main loop
last_reading_time = time.monotonic()
while True:
    current_time = time.monotonic()

    # Check if 15 minutes (900 seconds) have passed since the last reading
    if current_time - last_reading_time >= 900:
        try:
            update_scd30_compensation()
            send_sensor_data()
            last_reading_time = current_time

        except Exception as e:
            print(f"Error: {e}")

    # Continuously check for commands from Raspberry Pi
    try:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            command = input().strip()
            handle_commands(command)

    except Exception as e:
        print(f"Error processing command: {e}")
