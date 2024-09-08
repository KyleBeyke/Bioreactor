import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
import sys

# I2C initialization for SCD30, BMP280, and DS3231 RTC
i2c = busio.I2C(board.GP21, board.GP20, frequency=50000)
scd30 = adafruit_scd30.SCD30(i2c)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
rtc = adafruit_ds3231.DS3231(i2c)

# Disable auto-calibration for SCD30
scd30.self_calibration_enabled = False

def get_timestamp_from_rtc():
    """ Retrieves the current timestamp from DS3231 RTC """
    now = rtc.datetime
    return f"{now.tm_year}-{now.tm_mon:02}-{now.tm_mday:02} {now.tm_hour:02}:{now.tm_min:02}:{now.tm_sec:02}"

def send_sensor_data():
    """ Sends sensor data to the Raspberry Pi and prints for troubleshooting """
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
        except Exception as e:
            sys.stdout.write(f"Error: {e}\n")
            sys.stdout.flush()

# Main loop
last_reading_time = time.monotonic()

while True:
    current_time = time.monotonic()

    # Every 15 seconds
    if current_time - last_reading_time >= 15:
        send_sensor_data()
        last_reading_time = current_time