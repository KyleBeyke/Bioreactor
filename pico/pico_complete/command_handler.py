# command_handler.py

"""
CommandHandler handles all incoming commands from the Raspberry Pi and controls the heater and other system components.
"""

from logger import Logger

class CommandHandler:
    def __init__(self, heater_controller, sensor_manager):
        """
        Initializes the CommandHandler with access to the heater controller and sensor manager.
        These components are required to perform various system actions such as controlling the heater,
        reading sensors, or recalibrating sensors.

        Args:
            heater_controller: Instance of HeaterController to manage the heater's state and temperature control.
            sensor_manager: Instance of SensorManager to manage and retrieve sensor data.
        """
        self.heater_controller = heater_controller
        self.sensor_manager = sensor_manager

    def handle(self, command):
        """
        Handles commands sent from the Raspberry Pi, parsing and executing actions based on the received command.

        Args:
            command (str): The command received from the Raspberry Pi in a specific format.
                           Commands may control the heater, request sensor data, recalibrate, or synchronize the RTC.
        """
        try:
            # Log that a command has been received for debugging and traceability
            Logger.log_info(f"Received command: {command}")

            # ---- Heater-related commands ----

            # Handle heater and sensor-related commands (e.g., setting temperature, controlling duty cycle)
            if command.startswith("SET_HEATER_TEMP"):
                temp = int(command.split(",")[1])
                Logger.log_info(f"Setting heater target temperature to: {temp}°C")
                self.heater_controller.pid_controller.setpoint = temp

            elif command.startswith("SET_HEATER_DUTY"):
                duty_cycle = int(command.split(",")[1])
                Logger.log_info(f"Setting max heater duty cycle to: {duty_cycle}%")
                self.heater_controller.max_duty_cycle = duty_cycle

            elif command == "HEATER_ON":
                Logger.log_info("Turning heater ON.")
                self.heater_controller.turn_on()

            elif command == "HEATER_OFF":
                Logger.log_info("Turning heater OFF.")
                self.heater_controller.turn_off()

            # ---- Sensor-related commands ----

            # Feed operation, logging feed amount along with sensor data (e.g., "FEED,500")
            elif command.startswith("FEED"):
                feed_amount = command.split(",")[1]
                Logger.log_info(f"Feed command received: {feed_amount} grams")
                self.sensor_manager.send_sensor_data(feed_amount, None)  # Log feed amount and sensor data

            # Calibrate the SCD30 CO2 sensor with a specified reference (e.g., "CALIBRATE,400")
            elif command.startswith("CALIBRATE"):
                recalibration_value = int(command.split(",")[1])
                self.sensor_manager.scd30.forced_recalibration_reference = recalibration_value
                Logger.log_info(f"Recalibration command received: {recalibration_value} ppm")
                self.sensor_manager.send_sensor_data(None, recalibration_value)  # Log the recalibration action

            # Request current sensor data to be logged ("REQUEST_DATA")
            elif command == "REQUEST_DATA":
                Logger.log_info("Data request command received.")
                self.sensor_manager.send_sensor_data()  # Trigger immediate sensor data logging

            # Shut down the system and put the Pico into deep sleep mode ("SHUTDOWN")
            elif command == "SHUTDOWN":
                Logger.log_info("Shutdown command received.")
                self.sensor_manager.shutdown_pico()  # Put the Pico into deep sleep

            # ---- RTC-related commands ----

            # Sync the RTC time with the Raspberry Pi (e.g., "SYNC_TIME,2024-09-13 14:30:00")
            elif command.startswith("SYNC_TIME"):
                Logger.log_info("Time sync command received.")
                self.sensor_manager.sync_rtc_time(command)  # Synchronize the RTC with the provided time

            # Request the current time from the RTC ("REQUEST_RTC_TIME")
            elif command == "REQUEST_RTC_TIME":
                Logger.log_info("RTC time request command received.")
                timestamp = self.sensor_manager.get_rtc_time()  # Get the current RTC time
                print(f"RTC time: {timestamp}")

            # ---- SCD30 Sensor Commands ----

            # Set altitude for the SCD30 CO2 sensor (e.g., "SET_ALTITUDE,150")
            elif command.startswith("SET_ALTITUDE"):
                altitude = int(command.split(",")[1])
                Logger.log_info(f"Set altitude command received: {altitude} meters")
                self.sensor_manager.set_altitude(altitude)  # Update the altitude for pressure compensation

            # Set the reference pressure for the BMP280 sensor (e.g., "SET_PRESSURE,1020")
            elif command.startswith("SET_PRESSURE"):
                pressure = int(command.split(",")[1])
                Logger.log_info(f"Set pressure command received: {pressure} hPa")
                self.sensor_manager.set_pressure_reference(pressure)  # Update the reference pressure

            # ---- System Cycle and CO2 Interval Commands ----

            # Set the sensor query cycle duration in minutes (e.g., "SET_CYCLE_MINS,5")
            elif command.startswith("SET_CYCLE_MINS"):
                new_cycle = int(command.split(",")[1])
                Logger.log_info(f"Set cycle command received: {new_cycle} minute(s)")
                self.sensor_manager.set_cycle(new_cycle)  # Update the sensor query interval

            # Set the CO2 measurement interval for the SCD30 sensor (e.g., "SET_CO2_INTERVAL,10")
            elif command.startswith("SET_CO2_INTERVAL"):
                interval = int(command.split(",")[1])
                Logger.log_info(f"Set CO2 interval command received: {interval} second(s)")
                self.sensor_manager.set_co2_interval(interval)  # Update the SCD30 CO2 measurement interval

            # ---- System Reset Command ----

            # Reset the Raspberry Pi Pico ("RESET_PICO")
            elif command == "RESET_PICO":
                Logger.log_info("Reset command received.")
                self.sensor_manager.reset_pico()  # Reset the Pico

            # ---- Invalid Command ----

            else:
                # Log an error if the command does not match any of the expected commands
                Logger.log_error("Invalid command received.")

        except Exception as e:
            # Log detailed error information in case of failure to process the command
            Logger.log_traceback_error(e)
