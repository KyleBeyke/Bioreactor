"""
sensor_manager.py

SensorManager handles the initialization and data collection from all sensors in the system.
It also provides power management functionalities like shutdown and reset.

The following sensors are managed:
- SCD30: CO2, temperature, and humidity sensor (I2C).
- BMP280: Pressure sensor (I2C).
- DS3231: Real-time clock (I2C).
- DS18B20: Temperature sensor (OneWire).

The class provides methods to:
- Initialize sensors
- Retrieve data from sensors
- Set sensor parameters (e.g., altitude, pressure)
- Manage power (shutdown, reset)

Dependencies:
- adafruit_scd30: For interfacing with the SCD30 sensor.
- adafruit_bmp280: For interfacing with the BMP280 sensor.
- adafruit_ds3231: For the DS3231 real-time clock.
- adafruit_ds18x20: For the DS18B20 temperature sensor (OneWire).
- logger: For logging sensor data and system information.
- alarm and microcontroller: For shutdown and reset functionality.
"""

import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
from adafruit_onewire.bus import OneWireBus
import adafruit_ds18x20
from logger import Logger
import alarm
import microcontroller


class SensorManager:
    """
    SensorManager class manages the initialization, reading, and management of all connected sensors.
    It also provides system power management functions such as shutdown and reset.
    """

    def __init__(self):
        """
        Initializes the SensorManager class attributes. Sensors are initially set to None and assigned
        during the initialization process.
        """
        self.scd30 = None  # SCD30 CO2, temperature, and humidity sensor
        self.bmp280 = None  # BMP280 pressure sensor
        self.rtc = None  # DS3231 real-time clock
        self.ds18b20 = None  # DS18B20 temperature sensor
        self.sensor_data_buffer = []  # Buffer to store sensor data for periodic writing
        self.buffer_max_size = 50  # Maximum buffer size before flushing to SD

    def initialize_sensors(self):
        """
        Initializes all connected sensors (SCD30, BMP280, DS3231, DS18B20).
        Raises an exception if any sensor fails to initialize.
        """
        try:
            # I2C sensor initialization (SCD30, BMP280, DS3231)
            i2c = busio.I2C(board.GP21, board.GP20)

            # Initialize SCD30 CO2 sensor
            self.scd30 = adafruit_scd30.SCD30(i2c)
            # Initialize BMP280 pressure sensor
            self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
            # Initialize DS3231 real-time clock
            self.rtc = adafruit_ds3231.DS3231(i2c)

            Logger.log_info("I2C sensors (SCD30, BMP280, DS3231) initialized successfully.")
        except Exception as e:
            Logger.log_error(f"Failed to initialize I2C sensors: {e}")
            raise RuntimeError("Critical failure: I2C sensor initialization failed.") from e

        # DS18B20 temperature sensor initialization (OneWire protocol)
        try:
            onewire_bus = OneWireBus(board.GP18)
            devices = onewire_bus.scan()
            if not devices:
                raise RuntimeError("No DS18B20 temperature sensor found.")

            # Initialize the first detected DS18B20 sensor
            self.ds18b20 = adafruit_ds18x20.DS18X20(onewire_bus, devices[0])
            Logger.log_info("DS18B20 temperature sensor initialized successfully.")
        except Exception as e:
            Logger.log_error(f"Failed to initialize DS18B20 sensor: {e}")
            raise RuntimeError("Critical failure: DS18B20 sensor initialization failed.") from e

    def get_temperature(self):
        """
        Reads the current temperature from the DS18B20 sensor.

        Returns:
            float: The current temperature in degrees Celsius.

        Raises:
            RuntimeError: If the DS18B20 sensor is not initialized or fails to provide a reading.
        """
        try:
            return self.ds18b20.temperature
        except Exception as e:
            Logger.log_error(f"Failed to read temperature from DS18B20: {e}")
            raise RuntimeError("Critical failure: Unable to read temperature.") from e

    def read_sensors(self):
        """
        Reads the current data from all connected sensors.

        Returns:
            tuple: CO2 (ppm), temperature (°C), humidity (%), DS18B20 temperature (°C), and pressure (hPa).

        Raises:
            RuntimeError: If any sensor fails to provide data.
        """
        try:
            co2 = self.scd30.CO2
            temperature = self.scd30.temperature
            humidity = self.scd30.relative_humidity
            ds_temp = self.get_temperature()
            pressure = self.bmp280.pressure

            # Add sensor data to buffer
            self.sensor_data_buffer.append((co2, temperature, humidity, ds_temp, pressure))
            if len(self.sensor_data_buffer) >= self.buffer_max_size:
                self.flush_sensor_data_to_sd()

            return co2, temperature, humidity, ds_temp, pressure
        except Exception as e:
            Logger.log_error(f"Failed to read sensor data: {e}")
            raise RuntimeError("Critical failure: Unable to read sensor data.") from e

    def flush_sensor_data_to_sd(self):
        """
        Flushes the buffered sensor data to the SD card. Clears the buffer after writing.
        """
        try:
            for data in self.sensor_data_buffer:
                co2, temp, humidity, ds_temp, pressure = data
                Logger.log_sensor_data(ds_temp, temp, co2)
                Logger.log_info(f"Buffered Sensor Data: CO2: {co2} ppm, Temp: {temp}°C, "
                                f"Humidity: {humidity}%, Pressure: {pressure} hPa")

            # Clear buffer after writing to SD
            self.sensor_data_buffer.clear()
        except Exception as e:
            Logger.log_error(f"Failed to write buffered sensor data: {e}")
            raise RuntimeError("Critical failure: Unable to write buffered data.") from e

    def send_sensor_data(self, feed_amount=None, recalibration_value=None):
        """
        Logs current sensor data. Optionally logs feed operation and sensor recalibration.
        Writes buffered data to the SD card periodically.

        Args:
            feed_amount (str): Amount of feed to log (optional).
            recalibration_value (int): Recalibration value for SCD30 CO2 sensor (optional).
        """
        try:
            co2, temp, humidity, ds_temp, pressure = self.read_sensors()

            if len(self.sensor_data_buffer) >= self.buffer_max_size:
                self.flush_sensor_data_to_sd()

            if feed_amount:
                Logger.log_info(f"Feed operation logged: {feed_amount} grams")

            if recalibration_value:
                Logger.log_info(f"SCD30 CO2 recalibrated to: {recalibration_value} ppm")
        except Exception as e:
            Logger.log_error(f"Failed to send sensor data: {e}")
            raise RuntimeError("Critical failure: Unable to send sensor data.") from e

    def shutdown_pico(self):
        """
        Shuts down the Pico by putting it into deep sleep mode.
        """
        Logger.log_info("System entering deep sleep mode.")
        self.flush_sensor_data_to_sd()  # Ensure buffered data is flushed before shutdown
        alarm.exit_and_deep_sleep_until_alarms()

    def reset_pico(self):
        """
        Resets the Pico using the microcontroller module.
        """
        Logger.log_info("Resetting the Pico.")
        self.flush_sensor_data_to_sd()  # Ensure buffered data is flushed before reset
        microcontroller.reset()

    def get_rtc_time(self):
        """
        Retrieves the current time from the RTC.

        Returns:
            str: The current time in "YYYY-MM-DD HH:MM:SS" format.

        Raises:
            RuntimeError: If the RTC fails to provide the current time.
        """
        try:
            rtc_time = self.rtc.datetime
            return f"{rtc_time.tm_year}-{rtc_time.tm_mon:02}-{rtc_time.tm_mday:02} " \
                   f"{rtc_time.tm_hour:02}:{rtc_time.tm_min:02}:{rtc_time.tm_sec:02}"
        except Exception as e:
            Logger.log_error(f"Failed to retrieve RTC time: {e}")
            raise RuntimeError("Critical failure: Unable to retrieve RTC time.") from e

    def sync_rtc_time(self, command):
        """
        Synchronizes the RTC time with a timestamp received from the Raspberry Pi.

        Args:
            command (str): The command string containing the timestamp (e.g., "SYNC_TIME,2024-09-13 14:30:00").
        """
        try:
            timestamp_str = command.split(",")[1]
            timestamp = time.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            self.rtc.datetime = timestamp
            Logger.log_info(f"RTC time synchronized to: {timestamp_str}")
        except Exception as e:
            Logger.log_error(f"Failed to sync RTC time: {e}")
            raise RuntimeError("Critical failure: RTC sync failed.") from e

    def set_altitude(self, altitude):
        """
        Sets the altitude for the SCD30 sensor for accurate CO2 readings.

        Args:
            altitude (int): Altitude in meters.

        Raises:
            RuntimeError: If the altitude cannot be set.
        """
        try:
            self.scd30.altitude = altitude
            Logger.log_info(f"SCD30 altitude set to: {altitude} meters")
        except Exception as e:
            Logger.log_error(f"Failed to set altitude: {e}")
            raise RuntimeError("Critical failure: Unable to set altitude.") from e

    def set_pressure_reference(self, pressure):
        """
        Sets the reference pressure for the BMP280 sensor.

        Args:
            pressure (int): Pressure in hPa.

        Raises:
            RuntimeError: If the pressure reference cannot be set.
        """
        try:
            self.bmp280.sea_level_pressure = pressure
            Logger.log_info(f"BMP280 pressure reference set to: {pressure} hPa")
        except Exception as e:
            Logger.log_error(f"Failed to set pressure reference: {e}")
            raise RuntimeError("Critical failure: Unable to set pressure reference.") from e

    def set_cycle(self, new_cycle_minutes):
        """
        Sets the system's sensor data query cycle duration in minutes.

        Args:
            new_cycle_minutes (int): The new sensor data query cycle duration in minutes.
        """
        try:
            Logger.log_info(f"Sensor data query cycle set to {new_cycle_minutes} minute(s).")
            # This would normally be passed up to the control loop managing sensor data queries
        except Exception as e:
            Logger.log_error(f"Failed to set sensor query cycle: {e}")
            raise RuntimeError("Critical failure: Unable to set sensor query cycle.") from e

    def set_co2_interval(self, interval_seconds):
        """
        Sets the CO2 measurement interval for the SCD30 sensor.

        Args:
            interval_seconds (int): Interval between CO2 measurements in seconds.

        Raises:
            RuntimeError: If the CO2 measurement interval cannot be set.
        """
        try:
            self.scd30.measurement_interval = interval_seconds
            Logger.log_info(f"SCD30 CO2 measurement interval set to: {interval_seconds} second(s)")
        except Exception as e:
            Logger.log_error(f"Failed to set CO2 interval: {e}")
            raise RuntimeError("Critical failure: Unable to set CO2 measurement interval.") from e
