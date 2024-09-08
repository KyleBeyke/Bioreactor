import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
import sys

# Initialize I2C bus
i2c = busio.I2C(board.GP21, board.GP20)

# Initialize sensors
scd30 = adafruit_scd30.SCD30(i2c)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
rtc = adafruit_ds3231.DS3231(i2c)

# Disable auto-calibration for SCD30 (if desired)
scd30.self_calibration_enabled = False

# Function to get RTC time
def get_rtc_time():
    now = rtc.datetime
    return f"{now.tm_year}-{now.tm_mon:02}-{now.tm_mday:02} {now.tm_hour:02}:{now.tm_min:02}:{now.tm_sec:02}"

# Function to get and print sensor data
def get_sensor_data():
    if scd30.data_available:
        co2 = scd30.CO2
        temperature_scd30 = scd30.temperature
        humidity = scd30.relative_humidity
        
        pressure = bmp280.pressure
        altitude = bmp280.altitude
        temperature_bmp280 = bmp280.temperature
        
        rtc_time = get_rtc_time()

        # Print data to serial console for debugging
        print(f"RTC Time: {rtc_time}")
        print(f"SCD30 CO2: {co2:.2f} ppm, Temp: {temperature_scd30:.2f} °C, Humidity: {humidity:.2f} %")
        print(f"BMP280 Pressure: {pressure:.2f} hPa, Altitude: {altitude:.2f} m, Temp: {temperature_bmp280:.2f} °C")

# Main loop
while True:
    try:
        get_sensor_data()
        time.sleep(15)  # Wait for 15 seconds before reading again
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)