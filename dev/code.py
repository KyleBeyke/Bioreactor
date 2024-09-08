import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
import sys

# Initialize I2C for all sensors
i2c = busio.I2C(board.GP21, board.GP20)

# Initialize sensors
try:
    scd30 = adafruit_scd30.SCD30(i2c)
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
    rtc = adafruit_ds3231.DS3231(i2c)
    print("Sensors initialized successfully.")
except Exception as e:
    print(f"Failed to initialize sensors: {e}")
    sys.exit(1)

# Disable auto-calibration for SCD30
scd30.self_calibration_enabled = False

# Function to get data from the sensors
def get_sensor_data():
    try:
        # SCD30: CO2, temperature, and humidity
        if scd30.data_available:
            co2 = scd30.CO2
            temperature = scd30.temperature
            humidity = scd30.relative_humidity
        else:
            co2, temperature, humidity = None, None, None

        # BMP280: Pressure and altitude
        pressure = bmp280.pressure
        altitude = bmp280.altitude

        # DS3231: Current time
        now = rtc.datetime
        timestamp = f"{now.tm_year}-{now.tm_mon:02}-{now.tm_mday:02} {now.tm_hour:02}:{now.tm_min:02}:{now.tm_sec:02}"

        return timestamp, co2, temperature, humidity, pressure, altitude

    except Exception as e:
        print(f"Error getting sensor data: {e}")
        return None

# Main loop to send data every 15 seconds
while True:
    sensor_data = get_sensor_data()
    if sensor_data:
        timestamp, co2, temperature, humidity, pressure, altitude = sensor_data
        print(f"Time: {timestamp}")
        if co2 is not None:
            print(f"CO2: {co2:.2f} ppm, Temp: {temperature:.2f} C, Humidity: {humidity:.2f} %")
        print(f"Pressure: {pressure:.2f} hPa, Altitude: {altitude:.2f} m")

    time.sleep(15)  # Wait for 15 seconds before the next reading