# logger.py

"""
Logger module for logging system messages, errors, and tracebacks to the SD card.
"""

import traceback
import board
import busio
import storage
import digitalio
import adafruit_sdcard

class Logger:
    LOG_FILE = "/sd/pico_log.txt"
    DATA_LOG_FILE = "/sd/sensor_data.csv"

    sd_initialized = False

    @staticmethod
    def initialize_sd_card():
        """Initializes the SD card for logging, if not already initialized."""
        if not Logger.sd_initialized:
            try:
                spi = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
                cs = digitalio.DigitalInOut(board.GP13)
                sdcard = adafruit_sdcard.SDCard(spi, cs)
                vfs = storage.VfsFat(sdcard)
                storage.mount(vfs, "/sd")
                Logger.sd_initialized = True
                Logger.log_info("SD card initialized and mounted successfully.")
            except Exception as e:
                print(f"Failed to initialize SD card: {e}")
                Logger.sd_initialized = False

    @staticmethod
    def log_info(message):
        """Logs informational messages to the SD card and prints to the console."""
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()
        timestamp = Logger.get_rtc_time()
        try:
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(f"{timestamp} INFO: {message}\n")
            print(f"{timestamp} INFO: {message}")
        except Exception as e:
            print(f"Failed to log info: {e}")

    @staticmethod
    def log_error(message):
        """Logs error messages to the SD card and prints to the console."""
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()
        timestamp = Logger.get_rtc_time()
        try:
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(f"{timestamp} ERROR: {message}\n")
            print(f"{timestamp} ERROR: {message}")
        except Exception as e:
            print(f"Failed to log error: {e}")

    @staticmethod
    def log_traceback_error(e):
        """Logs detailed error messages with traceback information."""
        if not Logger.sd_initialized:
            Logger.initialize_sd_card()
        timestamp = Logger.get_rtc_time()
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        try:
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(f"{timestamp} TRACEBACK ERROR: {error_message}\n")
            print(f"{timestamp} TRACEBACK ERROR: {error_message}")
        except Exception as log_e:
            print(f"Failed to log traceback error: {log_e}")

    @staticmethod
    def get_rtc_time():
        """Fetches the current time from the RTC."""
        try:
            rtc_time = rtc.datetime
            return f"{rtc_time.tm_year}-{rtc_time.tm_mon:02}-{rtc_time.tm_mday:02} {rtc_time.tm_hour:02}:{rtc_time.tm_min:02}:{rtc_time.tm_sec:02}"
        except Exception:
            return "N/A"
