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
    LOG_FILE = "/sd/pico_log.txt"  # Log file path for general messages
    DATA_LOG_FILE = "/sd/sensor_data.csv"  # CSV file for sensor data logging

    sd_initialized = False  # Track if SD card has been initialized

    @staticmethod
    def initialize_sd_card():
        """
        Initializes the SD card for logging if it is not already initialized.
        This method sets up SPI communication and mounts the SD card to the filesystem.
        The system halts if SD card initialization fails.
        """
        if not Logger.sd_initialized:
            try:
                spi = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
                cs = digitalio.DigitalInOut(board.GP13)
                sdcard = adafruit_sdcard.SDCard(spi, cs)
                vfs = storage.VfsFat(sdcard)
                storage.mount(vfs, "/sd")
                Logger.sd_initialized = True
                Logger.log_info("SD card initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize SD card: {e}")
                Logger.sd_initialized = False
                raise RuntimeError("Critical failure: SD card initialization failed. Halting system.") from e

    @staticmethod
    def get_rtc_time():
        """
        Gets the current timestamp from the system's RTC. Returns a formatted string.
        If no RTC is available, it uses system time.
        """
        current_time = time.localtime()
        return f"{current_time.tm_year}-{current_time.tm_mon:02}-{current_time.tm_mday:02} " \
               f"{current_time.tm_hour:02}:{current_time.tm_min:02}:{current_time.tm_sec:02}"

    @staticmethod
    def log_info(message):
        """
        Logs informational messages to the SD card and console.
        """
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()
        
        timestamp = Logger.get_rtc_time()
        log_entry = f"{timestamp} INFO: {message}"
        
        try:
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(log_entry + "\n")
            print(log_entry)  # Output to console
        except Exception as e:
            print(f"Failed to log info: {e}")
            raise RuntimeError("Critical failure: Unable to log info to SD card. Halting system.") from e

    @staticmethod
    def log_error(message):
        """
        Logs error messages to the SD card and console.
        """
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()
        
        timestamp = Logger.get_rtc_time()
        log_entry = f"{timestamp} ERROR: {message}"
        
        try:
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(log_entry + "\n")
            print(log_entry)  # Output to console
        except Exception as e:
            print(f"Failed to log error: {e}")
            raise RuntimeError("Critical failure: Unable to log error to SD card. Halting system.") from e

    @staticmethod
    def log_traceback_error(e):
        """
        Logs detailed error tracebacks to help debug exceptions.
        """
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()
        
        timestamp = Logger.get_rtc_time()
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        log_entry = f"{timestamp} TRACEBACK ERROR: {tb_str}"
        
        try:
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(log_entry + "\n")
            print(log_entry)  # Output to console
        except Exception as log_exception:
            print(f"Failed to log traceback error: {log_exception}")
            raise RuntimeError("Critical failure: Unable to log traceback to SD card. Halting system.") from e

    @staticmethod
    def log_sensor_data(temperature, setpoint, duty_cycle):
        """
        Logs sensor data (temperature, setpoint, and duty cycle) to a CSV file on the SD card.
        """
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()
        
        timestamp = Logger.get_rtc_time()
        log_entry = f"{timestamp},{temperature},{setpoint},{duty_cycle}"
        
        try:
            with open(Logger.DATA_LOG_FILE, 'a') as data_file:
                data_file.write(log_entry + "\n")
            print(f"{timestamp} Sensor Data: Temp={temperature}C, Setpoint={setpoint}C, Duty={duty_cycle}%")
        except Exception as e:
            print(f"Failed to log sensor data: {e}")
            raise RuntimeError("Critical failure: Unable to log sensor data to SD card. Halting system.") from e
