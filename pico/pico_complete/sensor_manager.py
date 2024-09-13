# sensor_manager.py

"""
SensorManager handles initialization and data collection from all sensors.
"""

import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
from adafruit_onewire.bus import OneWireBus  # For OneWire communication
import adafruit_ds18x20  # For DS18B20 temperature sensor
from logger import Logger

class SensorManager:
    def __init__(self):
        self.scd30 = None
        self.bmp280 = None
        self.rtc = None
        self.ds18b20 = None

    def initialize_sensors(self):
        """Initializes I2C sensors (SCD30, BMP280, DS3231) and OneWire DS18B20."""
        try:
            i2c = busio.I2C(board.GP21, board.GP20)
            self.scd30 = adafruit_scd30.SCD30(i2c)
            self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
            self.rtc = adafruit_ds3231.DS3231(i2c)
            Logger.log_info("I2C sensors initialized successfully.")
        except Exception as e:
            Logger.log_error(f"Failed to initialize I2C sensors: {e}")
            raise

        # DS18B20 initialization
        try:
            onewire_bus = OneWireBus(board.GP18)
            devices = onewire_bus.scan()
            if not devices:
                raise RuntimeError("No DS18B20 sensor found!")
            self.ds18b20 = adafruit_ds18x20.DS18X20(onewire_bus, devices[0])
            Logger.log_info("DS18B20 initialized successfully.")
        except Exception as e:
            Logger.log_error(f"Failed to initialize DS18B20: {e}")
            raise

    def get_temperature(self):
        """Reads temperature from DS18B20 sensor."""
        return self.ds18b20.temperature