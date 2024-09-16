"""
Logger module for logging system messages, errors, and tracebacks to the SD card.

The Logger dynamically initializes the SD card if not already mounted and writes log messages
to both the SD card and the console. It handles informational messages, error messages, and
traceback logging for debugging.

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
        # CircuitPython does not always have access to an RTC by default, so we use the
        # system monotonic time for the log. In more advanced systems, this can be replaced
        # with real RTC logic.
        current_time = time.localtime()  # Get local time from system
        return f"{current_time.tm_year}-{current_time.tm_mon:02}-{current_time.tm_mday:02} " \
               f"{current_time.tm_hour:02}:{current_time.tm_min:02}:{current_time.tm_sec:02}"

    @staticmethod
    def log_info(message):
        """
        Logs informational messages to the SD card and prints to the console.

        Args:
            message (str): The message to be logged.
        """
        # Ensure the SD card is initialized
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()

        # Get the current timestamp for the log entry
        timestamp = Logger.get_rtc_time()

        try:
            # Append the log message to the log file on the SD card
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(f"{timestamp} INFO: {message}\n")
            print(f"{timestamp} INFO: {message}")  # Also print to the console
        except Exception as e:
            # Handle any errors during logging
            print(f"Failed to log info: {e}")

    @staticmethod
    def log_error(message):
        """
        Logs error messages to the SD card and prints to the console.

        Args:
            message (str): The error message to be logged.
        """
        # Ensure the SD card is initialized
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()

        # Get the current timestamp for the log entry
        timestamp = Logger.get_rtc_time()

        try:
            # Append the error message to the log file on the SD card
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(f"{timestamp} ERROR: {message}\n")
            print(f"{timestamp} ERROR: {message}")  # Also print to the console
        except Exception as e:
            # Handle any errors during logging
            print(f"Failed to log error: {e}")

    @staticmethod
    def log_traceback_error(e):
        """
        Logs detailed error messages with traceback information to help debug exceptions.

        Args:
            e (Exception): The exception object to log.
        """
        # Ensure the SD card is initialized
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()

        # Get the current timestamp for the log entry
        timestamp = Logger.get_rtc_time()

        try:
            # Capture the full traceback as a string
            tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))

            # Append the traceback to the log file on the SD card
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(f"{timestamp} TRACEBACK ERROR: {tb_str}\n")
            print(f"{timestamp} TRACEBACK ERROR: {tb_str}")  # Also print to the console
        except Exception as log_exception:
            # Handle any errors during traceback logging
            print(f"Failed to log traceback error: {log_exception}")
            
    @staticmethod
    def log_sensor_data(temperature, setpoint, duty_cycle):
        """
        Logs sensor data (temperature, setpoint, and duty cycle) to a CSV file on the SD card.

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

        try:
            # Append the sensor data to the CSV file on the SD card
            with open(Logger.DATA_LOG_FILE, 'a') as data_file:
                data_file.write(f"{timestamp},{temperature},{setpoint},{duty_cycle}\n")
            print(f"{timestamp} Sensor Data: Temp={temperature}C, Setpoint={setpoint}C, Duty={duty_cycle}%")
        except Exception as e:
            # Handle any errors during data logging
            print(f"Failed to log sensor data: {e}")

