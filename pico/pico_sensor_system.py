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
import board
import busio
import adafruit_scd30
import adafruit_bmp280 # type: ignore
import digitalio
import sdcardio
import storage
import sys
import select
import microcontroller
import alarm

# Simple logging functions to mimic logging behavior
LOG_FILE = "/sd/pico_log.txt"

def log_info(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{timestamp} INFO: {message}\n")
        print(f"{timestamp} INFO: {message}")
    except Exception as e:
        print(f"Failed to log info: {e}")

def log_error(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(f"{timestamp} ERROR: {message}\n")
        print(f"{timestamp} ERROR: {message}")
    except Exception as e:
        print(f"Failed to log error: {e}")

# I2C initialization for SCD30 and BMP280
i2c = busio.I2C(board.GP21, board.GP20, frequency=50000)
scd30 = adafruit_scd30.SCD30(i2c)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)

# Disable auto-calibration for SCD30
scd30.self_calibration_enabled = False

# Setup SPI for SD card
spi = busio.SPI(board.GP10, board.GP11, board.GP12)
cs = board.GP13  # Corrected to be of type Pin, as required by sdcardio
sdcard = sdcardio.SDCard(spi, cs)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

# CSV file for logging sensor data
DATA_LOG_FILE = "/sd/sensor_data.csv"

# Function to log data to the CSV file
def log_data_to_csv(timestamp, co2, temperature, humidity, pressure=None, altitude=None, feed_amount=None, recalibration=None):
    try:
        with open(DATA_LOG_FILE, mode='a', newline='') as csvfile:
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
        log_info(f"Data logged: CO2: {co2} ppm, Temp: {temperature}°C, Humidity: {humidity}%, Pressure: {pressure} hPa, Altitude: {altitude} m")
    except Exception as e:
        log_error(f"Failed to log data to CSV: {e}")

# Function to update SCD30 altitude and pressure compensation using BMP280
def update_scd30_compensation():
    try:
        pressure = bmp280.pressure
        altitude = bmp280.altitude
        scd30.set_altitude_comp(int(altitude))
        scd30.start_continous_measurement(int(pressure))
        log_info(f"Compensation updated: Pressure: {pressure}, Altitude: {altitude}")
    except Exception as e:
        log_error(f"Failed to update compensation: {e}")

# Function to send sensor data to the Raspberry Pi
def send_sensor_data():
    if scd30.data_available:
        try:
            co2 = scd30.CO2
            temperature = scd30.temperature
            humidity = scd30.relative_humidity
            pressure = bmp280.pressure
            altitude = bmp280.altitude
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            sensor_data = f"{timestamp} | CO2: {co2:.2f} ppm, Temp: {temperature:.2f} °C, Humidity: {humidity:.2f} %, Pressure: {pressure:.2f} hPa, Altitude: {altitude:.2f} m"
            sys.stdout.write(sensor_data + "\n")
            sys.stdout.flush()
            log_data_to_csv(timestamp, co2, temperature, humidity, pressure, altitude)
        except Exception as e:
            log_error(f"Failed to send sensor data: {e}")

# Function to handle Pico shutdown and enter deep sleep
def shutdown_pico():
    log_info("Shutting down Pico and entering deep sleep.")
    sys.stdout.flush()
    time.sleep(2)  # Ensure all operations complete
    wake_alarm = alarm.pin.PinAlarm(pin=board.GP15, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(wake_alarm)

# Function to update RTC time from Raspberry Pi command (Placeholder, as RTC not added back yet)
def update_rtc_time(year, month, day, hour, minute, second):
    log_info(f"RTC time updated to: {year}-{month}-{day} {hour}:{minute}:{second}")

# Main control loop
def control_loop():
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
                log_error(f"Error in sensor reading cycle: {e}")

        # Continuously check for commands from Raspberry Pi
        try:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                command = input().strip()

                if command.startswith("SET_TIME"):
                    _, year, month, day, hour, minute, second = command.split(",")
                    update_rtc_time(int(year), int(month), int(day), int(hour), int(minute), int(second))

                elif command == "REQUEST_RTC_TIME":
                    # Placeholder - send time to Pi (implement when RTC is added back)
                    log_info("RTC Time requested")

                elif command.startswith("CALIBRATE"):
                    recalibration_value = int(command.split(",")[1])
                    scd30.set_forced_recalibration(recalibration_value)
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    log_data_to_csv(timestamp, scd30.CO2, scd30.temperature, scd30.relative_humidity, recalibration=recalibration_value)
                    log_info(f"Recalibration set to {recalibration_value} ppm")

                elif command.startswith("FEED"):
                    feed_amount = command.split(",")[1]
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    log_data_to_csv(timestamp, scd30.CO2, scd30.temperature, scd30.relative_humidity, feed_amount=feed_amount)
                    log_info(f"Feed logged: {feed_amount} grams")

                elif command.startswith("SHUTDOWN"):
                    shutdown_pico()

        except Exception as e:
            log_error(f"Error processing command: {e}")

# Main program entry point
if __name__ == "__main__":
    control_loop()
