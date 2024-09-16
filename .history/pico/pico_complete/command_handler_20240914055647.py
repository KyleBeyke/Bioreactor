"""
CommandHandler class for processing incoming commands from the Raspberry Pi.

The CommandHandler manages:
- Heater control (turning it on/off, setting temperature, and controlling duty cycle).
- Sensor recalibration (CO2 sensor calibration, logging sensor data).
- Setting system parameters (sensor data query interval, CO2 interval, altitude, and pressure).
- Synchronizing the real-time clock (RTC) with a provided timestamp.
- Resetting or shutting down the system, ensuring all buffers are flushed before.
- Handling all interactions needed to control the system.

Dependencies:
- HeaterController: For managing heater state and control.
- SensorManager: For managing and interacting with sensors.
- Logger: For logging system events and command handling.
- microcontroller: To reset the system programmatically.
"""

from logger import Logger
import microcontroller

class CommandHandler:
    """
    CommandHandler processes incoming commands from the Raspberry Pi and interacts with
    the HeaterController and SensorManager to perform various system actions.
    """

    def __init__(self, heater_controller, sensor_manager):
        """
        Initializes the CommandHandler with access to the heater controller and sensor manager.

        Args:
            heater_controller: Instance of HeaterController to manage the heater's state and temperature control.
            sensor_manager: Instance of SensorManager to manage and retrieve sensor data.
        """
        self.heater_controller = heater_controller
        self.sensor_manager = sensor_manager

    def handle(self, command):
        """
        Processes the received command and executes the corresponding system action.

        Args:
            command (str): The command string received from the Raspberry Pi.

        Commands:
        - Heater Control: "SET_HEATER_TEMP,45", "SET_HEATER_DUTY,30", "HEATER_ON", "HEATER_OFF"
        - Sensor Management: "FEED,500", "CALIBRATE,400", "REQUEST_DATA"
        - RTC Commands: "SYNC_TIME,2024-09-13 14:30:00", "REQUEST_RTC_TIME"
        - System Commands: "SET_CYCLE_MINS,5", "SET_CO2_INTERVAL,10", "SHUTDOWN", "RESET_PICO"
        - Environmental Settings: "SET_ALTITUDE,150", "SET_PRESSURE,1020"
        """
        try:
            # Log the received command for debugging and traceability
            Logger.log_info(f"Received command: {command}")

            # ---- Heater Control Commands ----

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

            # ---- Sensor-Related Commands ----

            elif command.startswith("FEED"):
                feed_amount = command.split(",")[1]
                Logger.log_info(f"Feed command received: {feed_amount} grams")
                self.sensor_manager.send_sensor_data(feed_amount, None)

            elif command.startswith("CALIBRATE"):
                recalibration_value = int(command.split(",")[1])
                self.sensor_manager.scd30.forced_recalibration_reference = recalibration_value
                Logger.log_info(f"SCD30 CO2 recalibrated to: {recalibration_value} ppm")
                self.sensor_manager.send_sensor_data(None, recalibration_value)

            elif command == "REQUEST_DATA":
                Logger.log_info("Data request command received.")
                self.sensor_manager.send_sensor_data()

            # ---- RTC-Related Commands ----

            elif command.startswith("SYNC_TIME"):
                Logger.log_info("Time sync command received.")
                self.sensor_manager.sync_rtc_time(command)

            elif command == "REQUEST_RTC_TIME":
                Logger.log_info("RTC time request command received.")
                timestamp = self.sensor_manager.get_rtc_time()
                print(f"RTC time: {timestamp}")

            # ---- Environmental Settings Commands ----

            elif command.startswith("SET_ALTITUDE"):
                altitude = int(command.split(",")[1])
                Logger.log_info(f"Set altitude command received: {altitude} meters")
                self.sensor_manager.set_altitude(altitude)

            elif command.startswith("SET_PRESSURE"):
                pressure = int(command.split(",")[1])
                Logger.log_info(f"Set pressure command received: {pressure} hPa")
                self.sensor_manager.set_pressure_reference(pressure)

            # ---- System Cycle and CO2 Interval Commands ----

            elif command.startswith("SET_CYCLE_MINS"):
                new_cycle = int(command.split(",")[1])
                Logger.log_info(f"Set cycle command received: {new_cycle} minute(s)")
                self.sensor_manager.set_cycle(new_cycle)

            elif command.startswith("SET_CO2_INTERVAL"):
                interval = int(command.split(",")[1])
                Logger.log_info(f"Set CO2 interval command received: {interval} second(s)")
                self.sensor_manager.set_co2_interval(interval)

            # ---- System Commands ----

            elif command == "SHUTDOWN":
                Logger.log_info("Shutdown command received. Flushing buffers and shutting down.")
                Logger.flush_all_buffers()  # Ensure all logs are written
                self.sensor_manager.shutdown_pico()

            elif command == "RESET_PICO":
                Logger.log_info("Reset command received. Flushing buffers and resetting.")
                Logger.flush_all_buffers()  # Ensure all logs are written
                microcontroller.reset()

            # ---- Invalid Command ----

            else:
                Logger.log_error(f"Invalid command received: {command}")

        except Exception as e:
            Logger.log_traceback_error(e)  # Log detailed error information if exceptions occur
