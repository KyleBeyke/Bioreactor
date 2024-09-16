"""
SensorManager handles the initialization and data collection from all sensors in the system.

This class manages the following sensors:
- SCD30: CO2, temperature, and humidity sensor (I2C).
- BMP280: Pressure sensor (I2C).
- DS3231: Real-time clock (I2C).
- DS18B20: Temperature sensor (OneWire).

The class provides methods to initialize these sensors, retrieve sensor data, synchronize the RTC,
and log critical sensor data. It also handles system power management, including deep sleep and reset functionality.

Key Features:
- Periodic sensor data collection and buffering to reduce SD card wear.
- Deep sleep and system reset management using CircuitPython's `alarm` and `microcontroller` modules.
- Error handling with system halt in case of sensor initialization failures.

Dependencies:
- adafruit_scd30: For interfacing with the SCD30 sensor.
- adafruit_bmp280: For interfacing with the BMP280 pressure sensor.
- adafruit_ds3231: For the DS3231 real-time clock.
- adafruit_ds18x20: For the DS18B20 temperature sensor (OneWire).
- logger: For logging information and errors.
- time: For handling real-time data and sleep intervals.
- busio: For I2C communication with the sensors.
- OneWireBus: For managing the DS18B20 OneWire communication.
- alarm: For deep sleep and wake-up management.
- microcontroller: For system reset functionality.
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
    SensorManager handles the initialization and data collection from all sensors in the system.
    It provides sensor initialization, data reading, and power management (shutdown and reset).
    """

    def __init__(self):
        """
        Initializes the SensorManager class attributes. Sensor objects are initially set to None
        and are assigned during the initialization process.
        """
        self.scd30 = None
        self.bmp280 = None
        self.rtc = None
        self.ds18b20 = None
        self.sensor_data_buffer = []  # Buffer for storing sensor data before writing to SD card

    def initialize_sensors(self):
        """
        Initializes all connected sensors (SCD30, BMP280, DS3231, and DS18B20).
        Raises exception if any sensor fails to initialize.
        """
        try:
            i2c = busio.I2C(board.GP21, board.GP20)

            # Initialize the SCD30 CO2 sensor
            self.scd30 = adafruit_scd30.SCD30(i2c)
            # Initialize the BMP280 pressure sensor
            self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
            # Initialize the DS3231 RTC
            self.rtc = adafruit_ds3231.DS3231(i2c)

            Logger.log_info("I2C sensors (SCD30, BMP280, DS3231) initialized successfully.")
        except Exception as e:
            Logger.log_error(f"Failed to initialize I2C sensors: {e}")
            raise RuntimeError("Critical failure: I2C sensor initialization failed. Halting system.") from e

        # Initialize the DS18B20 temperature sensor (OneWire protocol)
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
            raise RuntimeError("Critical failure: DS18B20 sensor initialization failed. Halting system.") from e

    def get_temperature(self):
        """
        Reads the current temperature from the DS18B20 sensor.

        Returns:
            float: The current temperature in degrees Celsius.

        Raises:
            Exception: If the DS18B20 sensor is not initialized or fails to provide a reading.
        """
        try:
            return self.ds18b20.temperature
        except Exception as e:
            Logger.log_error(f"Failed to read temperature from DS18B20: {e}")
            raise RuntimeError("Critical failure: Unable to read temperature. Halting system.") from e

    def read_sensors(self):
        """
        Reads the current data from all connected sensors and stores it in the buffer.

        Returns:
            tuple: CO2 (ppm), temperature (°C), humidity (%), DS18B20 temperature (°C), and pressure (hPa).

        Raises:
            Exception: If any sensor fails to provide data.
        """
        try:
            co2 = self.scd30.CO2
            temperature = self.scd30.temperature
            humidity = self.scd30.relative_humidity
            ds_temp = self.get_temperature()
            pressure = self.bmp280.pressure

            # Add data to the buffer
            self.sensor_data_buffer.append((co2, temperature, humidity, ds_temp, pressure))

            return co2, temperature, humidity, ds_temp, pressure
        except Exception as e:
            Logger.log_error(f"Failed to read sensor data: {e}")
            raise RuntimeError("Critical failure: Unable to read sensor data. Halting system.") from e

    def write_sensor_data_to_sd(self):
        """
        Writes the buffered sensor data to the SD card. This method flushes the buffer.
        """
        try:
            if self.sensor_data_buffer:
                for data in self.sensor_data_buffer:
                    co2, temperature, humidity, ds_temp, pressure = data
                    Logger.log_sensor_data(ds_temp, self.scd30.temperature, self.scd30.CO2)
                    Logger.log_info(f"Buffered Sensor Data: CO2: {co2} ppm, Temp: {temperature}°C, Humidity: {humidity}%, Pressure: {pressure} hPa")
                
                # Clear the buffer after writing to SD card
                self.sensor_data_buffer.clear()
        except Exception as e:
            Logger.log_error(f"Failed to write buffered sensor data: {e}")
            raise RuntimeError("Critical failure: Unable to write buffered data. Halting system.") from e

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

            if len(self.sensor_data_buffer) >= 10:  # Adjust the buffer size threshold as needed
                self.write_sensor_data_to_sd()

            if feed_amount:
                Logger.log_info(f"Feed operation logged: {feed_amount} grams")

            if recalibration_value:
                Logger.log_info(f"SCD30 CO2 recalibrated to: {recalibration_value} ppm")
        except Exception as e:
            Logger.log_error(f"Failed to send sensor data: {e}")
            raise RuntimeError("Critical failure: Unable to send sensor data. Halting system.") from e

    def shutdown_pico(self):
        """
        Shuts down the Raspberry Pi Pico by putting it into deep sleep mode.
        """
        Logger.log_info("System shutting down and entering deep sleep.")
        # Trigger an alarm to wake up the system if needed (optional)
        alarm.exit_and_deep_sleep_until_alarms()

    def reset_pico(self):
        """
        Resets the Raspberry Pi Pico.
        """
        Logger.log_info("System resetting.")
        microcontroller.reset()

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
            raise RuntimeError("Critical failure: RTC sync failed. Halting system.") from e

    def get_rtc_time(self):
        """
        Retrieves the current time from the RTC.

        Returns:
            str: The current time in "YYYY-MM-DD HH:MM:SS" format.
        """
        try:
            rtc_time = self.rtc.datetime
            return f"{rtc_time.tm_year}-{rtc_time.tm_mon:02}-{rtc_time.tm_mday:02} " \
                   f"{rtc_time.tm_hour:02}:{rtc_time.tm_min:02}:{rtc_time.tm_sec:02}"
        except Exception as e:
            Logger.log_error(f"Failed to retrieve RTC time: {e}")
            raise RuntimeError("Critical failure: Unable to retrieve RTC time. Halting system.") from e

    def set_altitude(self, altitude):
        """
        Sets the altitude for the SCD30 sensor for accurate CO2 readings.

        Args:
            altitude (int): Altitude in meters.
        """
        try:
            self.scd30.altitude = altitude
            Logger.log_info(f"SCD30 altitude set to: {altitude} meters")
        except Exception as e:
            Logger.log_error(f"Failed to set altitude: {e}")
            raise RuntimeError("Critical failure: Unable to set altitude. Halting system.") from e

    def set_pressure_reference(self, pressure):
        """
        Sets the reference pressure for the BMP280 sensor for accurate pressure readings.

        Args:
            pressure (int): Pressure in hPa.
        """
        try:
            self.bmp280.sea_level_pressure = pressure
            Logger.log_info(f"BMP280 reference pressure set to: {pressure} hPa")
        except Exception as e:
            Logger.log_error(f"Failed to set reference pressure: {e}")
            raise RuntimeError("Critical failure: Unable to set reference pressure. Halting system.") from e

    def set_cycle(self, new_cycle):
        """
        Sets the cycle interval for sensor data queries.

        Args:
            new_cycle (int): New cycle interval in seconds.
        """
        try:
            self.query_interval = max(60, new_cycle)  # Ensure a minimum interval of 1 minute
            Logger.log_info(f"Sensor query interval set to: {self.query_interval} seconds")
        except Exception as e:
            Logger.log_error(f"Failed to set sensor query interval: {e}")
            raise RuntimeError("Critical failure: Unable to set query cycle. Halting system.") from e

    def set_co2_interval(self, interval):
        """
        Sets the CO2 measurement interval for the SCD30 sensor.

        Args:
            interval (int): CO2 measurement interval in seconds.
        """
        try:
            self.scd30.measurement_interval = interval
            Logger.log_info(f"SCD30 CO2 interval set to: {interval} seconds")
        except Exception as e:
            Logger.log_error(f"Failed to set CO2 interval: {e}")
            raise RuntimeError("Critical failure: Unable to set CO2 interval. Halting system.") from e

    def reset_pico(self):
        """
        Resets the Raspberry Pi Pico.
        """
        Logger.log_info("System resetting.")
        microcontroller.reset()

    def shutdown_pico(self):
        """
        Shuts down the Raspberry Pi Pico by putting it into deep sleep mode.
        """
        Logger.log_info("System shutting down and entering deep sleep.")
        # Trigger deep sleep using alarm
        alarm.exit_and_deep_sleep_until_alarms()