# logger.py

import traceback

class Logger:
    LOG_FILE = "/sd/pico_log.txt"
    DATA_LOG_FILE = "/sd/sensor_data.csv"

    @staticmethod
    def log_info(message):
        """Logs informational messages to the SD card and prints to console."""
        timestamp = Logger.get_rtc_time()
        try:
            with open(Logger.LOG_FILE, 'a') as log_file:
                log_file.write(f"{timestamp} INFO: {message}\n")
            print(f"{timestamp} INFO: {message}")
        except Exception as e:
            print(f"Failed to log info: {e}")

    @staticmethod
    def log_error(message):
        """Logs error messages to the SD card and prints to console."""
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
        """Fetches the current time from the RTC (external RTC or system time)."""
        rtc_time = rtc.datetime
        return f"{rtc_time.tm_year}-{rtc_time.tm_mon:02}-{rtc_time.tm_mday:02} {rtc_time.tm_hour:02}:{rtc_time.tm_min:02}:{rtc_time.tm_sec:02}"
