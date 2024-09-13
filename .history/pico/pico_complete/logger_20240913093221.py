# logger.py

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
        timestamp = Logger.get_
