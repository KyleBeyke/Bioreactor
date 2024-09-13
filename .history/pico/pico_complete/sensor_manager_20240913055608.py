# sensor_manager.py

"""
SensorManager handles the initialization and data retrieval from all connected sensors (SCD30, BMP280, DS18B20).
"""

import busio
import board
import time
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
from adafruit_onewire.bus import OneWireBus
import adafruit_ds18x20
from logger import Logger

class SensorManager:
    def __init__(self):
        """Initializes I2C sensors and DS18B20 temperature sensor."""
        self.i2c, self.scd30, self.bmp280, self.rtc = self.initialize_sensors()
        self.ds18b20 = self.initialize_ds18b20()

    def initialize_sensors(self):
        """Initializes I2C sensors (SCD30, BMP280, DS3231)."""
        for attempt in range(3):
            try:
                i2c = busio.I2C(board.GP21, board.GP20)
                scd30 = adafruit_scd30.SCD30(i2c)
                bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
                rtc = adafruit_ds3231.DS3231(i2c)
                Logger.log_info("I2C devices initialized successfully.")
                return i2c, scd30, bmp280, rtc
            except Exception as e:
                Logger.log_error(f"Failed to initialize I2C devices on attempt {attempt + 1}: {e}")
                if attempt == 2:
                    microcontroller.reset()

    def initialize_ds18b20(self):
        """Initializes the DS18B20 temperature sensor."""
        for attempt in range(3):
            try:
                onewire_bus = OneWireBus(board.GP18)
                devices = onewire_bus.scan()
                if not devices:
                    raise RuntimeError("No DS18B20 sensor found!")
                ds18b20 = adafruit_ds18x20.DS18X20(onewire_bus, devices[0])
                Logger.log_info("DS18B20 initialized successfully.")
                return ds18b20
            except Exception as e:
                Logger.log_error(f"Failed to initialize DS18B20 on attempt {attempt + 1}: {e}")
                if attempt == 2:
                    microcontroller.reset()

    def read_sensors(self):
        """Fetch data from all sensors."""
        try:
            co2 = self.scd30.CO2
            temp = self.scd30.temperature
            humidity = self.scd30.relative_humidity
            ds18b20_temp = self.ds18b20.temperature
            pressure = self.bmp280.pressure
            return co2, temp, humidity, ds18b20_temp, pressure
        except Exception as e:
            Logger.log_traceback_error(e)
            return None
