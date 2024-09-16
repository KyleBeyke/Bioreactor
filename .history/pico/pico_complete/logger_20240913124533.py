"""
Logger module for logging system messages, errors, and tracebacks to the SD card.

This version implements buffered logging to reduce SD card write frequency. Logs are written
after every 50 entries or when flushed manually or periodically (every 1 minute).

Dependencies:
- busio: For SPI communication.
- digitalio: For controlling the SD card chip select (CS) pin.
- storage: For mounting the SD card.
- adafruit_sdcard: For interfacing with the SD card.
- traceback: For detailed error reporting.
"""

import traceback
import time
import board
import busio
import storage
import digitalio
import adafruit_sdcard

class Logger:
    # Log file paths for general log messages and sensor data
    LOG_FILE = "/sd/pico_log.txt"
    DATA_LOG_FILE = "/sd/sensor_data.csv"

    # Track if the SD card has been initialized and mounted
    sd_initialized = False

    # Buffers for storing logs before writing to the SD card
    log_buffer = []
    sensor_data_buffer = []

    # Set buffer size limit before writing to the SD card
    BUFFER_LIMIT = 50

    # Last flush timestamp for periodic flushing (every 1 minute)
    last_flush_time = time.monotonic()

    @staticmethod
    def initialize_sd_card():
        """
        Initializes the SD card for logging if it is not already initialized.
        This method sets up SPI communication and mounts the SD card to the filesystem.
        """
        if not Logger.sd_initialized:
            try:
                # SPI communication setup for the SD card
                spi = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
                cs = digitalio.DigitalInOut(board.GP13)  # Chip select pin for the SD card
                sdcard = adafruit_sdcard.SDCard(spi, cs)

                # Mount the SD card to the filesystem
                vfs = storage.VfsFat(sdcard)
                storage.mount(vfs, "/sd")

                # Mark SD card as initialized
                Logger.sd_initialized = True
                Logger.log_info("SD card initialized and mounted successfully.")
            except Exception as e:
                # Handle any errors during SD card initialization
                print(f"Failed to initialize SD card: {e}")
                Logger.sd_initialized = False

    @staticmethod
    def get_rtc_time():
        """
        Gets the current timestamp from the system's RTC.
        This method is useful for adding timestamps to logs.

        Returns:
            str: The current timestamp in the format "YYYY-MM-DD HH:MM:SS".
        """
        current_time = time.localtime()  # Get local time from system
        return f"{current_time.tm_year}-{current_time.tm_mon:02}-{current_time.tm_mday:02} " \
               f"{current_time.tm_hour:02}:{current_time.tm_min:02}:{current_time.tm_sec:02}"

    @staticmethod
    def log_info(message):
        """
        Logs informational messages to the buffer. Once the buffer reaches the limit, it flushes
        the logs to the SD card.

        Args:
            message (str): The message to be logged.
        """
        # Ensure the SD card is initialized
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()

        # Get the current timestamp for the log entry
        timestamp = Logger.get_rtc_time()
        log_entry = f"{timestamp} INFO: {message}\n"
        
        # Add to log buffer
        Logger.log_buffer.append(log_entry)
        
        # Flush buffer to SD card if the buffer limit is reached
        if len(Logger.log_buffer) >= Logger.BUFFER_LIMIT or Logger._time_to_flush():
            Logger.flush_log_buffer()

        print(log_entry)  # Also print to the console

    @staticmethod
    def log_error(message):
        """
        Logs error messages to the buffer. Flushes the buffer to the SD card when limit is reached.

        Args:
            message (str): The error message to be logged.
        """
        # Ensure the SD card is initialized
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()

        # Get the current timestamp for the log entry
        timestamp = Logger.get_rtc_time()
        log_entry = f"{timestamp} ERROR: {message}\n"

        # Add to log buffer
        Logger.log_buffer.append(log_entry)

        # Flush buffer to SD card if the buffer limit is reached or it is time to flush
        if len(Logger.log_buffer) >= Logger.BUFFER_LIMIT or Logger._time_to_flush():
            Logger.flush_log_buffer()

        print(log_entry)  # Also print to the console

    @staticmethod
    def log_traceback_error(e):
        """
        Logs detailed error messages with traceback information to help debug exceptions.
        Adds traceback logs to the buffer and flushes when the buffer limit is reached.

        Args:
            e (Exception): The exception object to log.
        """
        # Ensure the SD card is initialized
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()

        # Get the current timestamp for the log entry
        timestamp = Logger.get_rtc_time()

        # Capture the full traceback as a string
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        log_entry = f"{timestamp} TRACEBACK ERROR: {tb_str}\n"

        # Add to log buffer
        Logger.log_buffer.append(log_entry)

        # Flush buffer to SD card if the buffer limit is reached or it is time to flush
        if len(Logger.log_buffer) >= Logger.BUFFER_LIMIT or Logger._time_to_flush():
            Logger.flush_log_buffer()

        print(log_entry)  # Also print to the console

    @staticmethod
    def log_sensor_data(temperature, setpoint, duty_cycle):
        """
        Logs sensor data (temperature, setpoint, and duty cycle) to the buffer for periodic flushing to the SD card.

        Args:
            temperature (float): The current temperature reading.
            setpoint (float): The desired setpoint temperature.
            duty_cycle (float): The current heater duty cycle.
        """
        # Ensure the SD card is initialized
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()

        # Get the current timestamp for the log entry
        timestamp = Logger.get_rtc_time()
        sensor_entry = f"{timestamp},{temperature},{setpoint},{duty_cycle}\n"

        # Add to sensor data buffer
        Logger.sensor_data_buffer.append(sensor_entry)

        # Flush sensor buffer to SD card if the buffer limit is reached or it is time to flush
        if len(Logger.sensor_data_buffer) >= Logger.BUFFER_LIMIT or Logger._time_to_flush():
            Logger.flush_sensor_data_buffer()

        print(f"{timestamp} Sensor Data: Temp={temperature}C, Setpoint={setpoint}C, Duty={duty_cycle}%")

    @staticmethod
    def flush_log_buffer():
        """
        Flushes the log buffer by writing all buffered log messages to the SD card.
        """
        try:
            with open(Logger.LOG_FILE, 'a') as log_file:
                for entry in Logger.log_buffer:
                    log_file.write(entry)
            Logger.log_buffer.clear()  # Clear the buffer after flushing
        except Exception as e:
            print(f"Failed to flush log buffer: {e}")

    @staticmethod
    def flush_sensor_data_buffer():
        """
        Flushes the sensor data buffer by writing all buffered sensor data to the SD card.
        """
        try:
            with open(Logger.DATA_LOG_FILE, 'a') as data_file:
                for entry in Logger.sensor_data_buffer:
                    data_file.write(entry)
            Logger.sensor_data_buffer.clear()  # Clear the buffer after flushing
        except Exception as e:
            print(f"Failed to flush sensor data buffer: {e}")

    @staticmethod
    def flush_all_buffers():
        """
        Flushes both log and sensor data buffers to the SD card.
        """
        Logger.flush_log_buffer()
        Logger.flush_sensor_data_buffer()

    @staticmethod
    def _time_to_flush():
        """
        Determines if it is time to flush based on a periodic interval (e.g., 1 minute).
        Returns:
            bool: True if it has been more than 1 minute since the last flush, False otherwise.
        """
        current_time = time.monotonic()
        if current_time - Logger.last_flush_time >= 60:  # 1 minute
            Logger.last_flush_time = current_time
            return True
        return