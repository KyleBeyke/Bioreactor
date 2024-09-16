# sensor_manager.py

"""
SensorManager handles the initialization and data collection from all sensors in the system.

This class manages the following sensors:
- SCD30: CO2, temperature, and humidity sensor (I2C).
- BMP280: Pressure sensor (I2C).
- DS3231: Real-time clock (I2C).
- DS18B20: Temperature sensor (OneWire).

The class provides methods to initialize these sensors and retrieve temperature data from DS18B20.
It also logs initialization success or failure and handles exceptions during the process.

Dependencies:
- adafruit_scd30: For interfacing with the SCD30 sensor.
- adafruit_bmp280: For interfacing with the BMP280 pressure sensor.
- adafruit_ds3231: For the DS3231 real-time clock.
- adafruit_ds18x20: For the DS18B20 temperature sensor (OneWire).
- logger: For logging information and errors.
"""

import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
from adafruit_onewire.bus import OneWireBus  # For OneWire communication
import adafruit_ds18x20  # For DS18B20 temperature sensor
from logger import Logger  # Import the Logger for logging

class SensorManager:
    """
    The SensorManager class initializes and manages all the sensors used in the system.

    It provides methods for sensor initialization and data collection.
    """

    def __init__(self):
        """
        Initializes the SensorManager class attributes. Sensor objects are initially set to None
        and are assigned during the initialization process.
        """
        self.scd30 = None  # SCD30 CO2, temperature, and humidity sensor (I2C)
        self.bmp280 = None  # BMP280 pressure sensor (I2C)
        self.rtc = None  # DS3231 real-time clock (I2C)
        self.ds18b20 = None  # DS18B20 temperature sensor (OneWire)

    def initialize_sensors(self):
        """
        Initializes all connected sensors (SCD30, BMP280, DS3231, and DS18B20).

        This method establishes I2C communication with SCD30, BMP280, and DS3231, and initializes
        the DS18B20 temperature sensor using the OneWire protocol.

        Raises:
            Exception: If any sensor fails to initialize, the exception is raised after logging the error.
        """
        # I2C sensor initialization (SCD30, BMP280, DS3231)
        try:
            # Set up I2C communication on the specified GPIO pins
            i2c = busio.I2C(board.GP21, board.GP20)

            # Initialize the SCD30 CO2 sensor
            self.scd30 = adafruit_scd30.SCD30(i2c)
            # Initialize the BMP280 pressure sensor
            self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
            # Initialize the DS3231 real-time clock
            self.rtc = adafruit_ds3231.DS3231(i2c)

            # Log successful initialization of I2C sensors
            Logger.log_info("I2C sensors (SCD30, BMP280, DS3231) initialized successfully.")
        except Exception as e:
            # Log any failure during I2C sensor initialization and raise the exception
            Logger.log_error(f"Failed to initialize I2C sensors: {e}")
            raise  # Raise the exception to indicate initialization failure

        # DS18B20 temperature sensor initialization (OneWire protocol)
        try:
            # Set up the OneWire communication bus on the specified GPIO pin
            onewire_bus = OneWireBus(board.GP18)

            # Scan for connected DS18B20 sensors
            devices = onewire_bus.scan()
            if not devices:
                raise RuntimeError("No DS18B20 temperature sensor found!")  # Raise error if no devices found

            # Initialize the DS18B20 sensor
            self.ds18b20 = adafruit_ds18x20.DS18X20(onewire_bus, devices[0])

            # Log successful initialization of the DS18B20 sensor
            Logger.log_info("DS18B20 temperature sensor initialized successfully.")
        except Exception as e:
            # Log any failure during DS18B20 initialization and raise the exception
            Logger.log_error(f"Failed to initialize DS18B20 temperature sensor: {e}")
            raise  # Raise the exception to indicate initialization failure

    def get_temperature(self):
        """
        Reads the current temperature from the DS18B20 sensor.

        Returns:
            float: The current temperature in degrees Celsius, as measured by the DS18B20 sensor.

        Raises:
            Exception: If the DS18B20 sensor is not initialized or fails to provide a reading.
        """
        try:
            # Return the current temperature reading from the DS18B20 sensor
            return self.ds18b20.temperature
        except Exception as e:
            # Log and raise any error that occurs during temperature reading
            Logger.log_error(f"Failed to read temperature from DS18B20: {e}")
            raise
