from logger import Logger

class CommandHandler:
    """
    CommandHandler handles all incoming commands from the Raspberry Pi and controls the heater and other system components.
    """

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

            # Set target temperature for the heater (e.g., "SET_HEATER_TEMP,45")
            if command.startswith("SET_HEATER_TEMP"):
                temp = int(command.split(",")[1])
                Logger.log_info(f"Setting heater target temperature to: {temp}°C")
                # Update the PID controller's target temperature (setpoint)
                self.heater_controller.pid_controller.setpoint = temp

            # Set the maximum duty cycle for the heater (e.g., "SET_HEATER_DUTY,30")
            elif command.startswith("SET_HEATER_DUTY"):
                duty_cycle = int(command.split(",")[1])
                Logger.log_info(f"Setting max heater duty cycle to: {duty_cycle}%")
                # Cap the heater's duty cycle to the specified percentage
                self.heater_controller.max_duty_cycle = duty_cycle

            # Turn the heater ON ("HEATER_ON")
            elif command == "HEATER_ON":
                Logger.log_info("Turning heater ON.")
                self.heater_controller.turn_on()

            # Turn the heater OFF ("HEATER_OFF")
            elif command == "HEATER_OFF":
                Logger.log_info("Turning heater OFF.")
                self.heater_controller.turn_off()

            # ---- Sensor-related commands ----

            # Log feed operation, including feed amount and sensor data (e.g., "FEED,500")
            elif command.startswith("FEED"):
                feed_amount = command.split(",")[1]
                Logger.log_info(f"Feed command received: {feed_amount} grams")
                # Log the feed operation and current sensor data
                self.sensor_manager.send_sensor_data(feed_amount, None)

            # Calibrate the SCD30 CO2 sensor to a specific value (e.g., "CALIBRATE,400")
            elif command.startswith("CALIBRATE"):
                recalibration_value = int(command.split(",")[1])
                self.sensor_manager.scd30.forced_recalibration_reference = recalibration_value
                Logger.log_info(f"Recalibration command received: {recalibration_value} ppm")
                # Log the recalibration action along with sensor data
                self.sensor_manager.send_sensor_data(None, recalibration_value)

            # Request immediate sensor data logging ("REQUEST_DATA")
            elif command == "REQUEST_DATA":
                Logger.log_info("Data request command received.")
                # Log the current sensor data immediately
                self.sensor_manager.send_sensor_data()

            # Shut down the system and put the Pico into deep sleep mode ("SHUTDOWN")
            elif command == "SHUTDOWN":
                Logger.log_info("Shutdown command received.")
                # Shut down the system and put it into deep sleep
                self.sensor_manager.shutdown_pico()

            # ---- RTC-related commands ----

            # Synchronize the RTC time with the Raspberry Pi (e.g., "SYNC_TIME,2024-09-13 14:30:00")
            elif command.startswith("SYNC_TIME"):
                Logger.log_info("Time sync command received.")
                # Synchronize the RTC with the provided timestamp
                self.sensor_manager.sync_rtc_time(command)

            # Request the current time from the RTC ("REQUEST_RTC_TIME")
            elif command == "REQUEST_RTC_TIME":
                Logger.log_info("RTC time request command received.")
                # Retrieve and print the current RTC time
                timestamp = self.sensor_manager.get_rtc_time()
                print(f"RTC time: {timestamp}")

            # ---- SCD30 Sensor Commands ----

            # Set the altitude for the SCD30 CO2 sensor (e.g., "SET_ALTITUDE,150")
            elif command.startswith("SET_ALTITUDE"):
                altitude = int(command.split(",")[1])
                Logger.log_info(f"Set altitude command received: {altitude} meters")
                # Update the altitude for pressure compensation
                self.sensor_manager.set_altitude(altitude)

            # Set the reference pressure for the BMP280 sensor (e.g., "SET_PRESSURE,1020")
            elif command.startswith("SET_PRESSURE"):
                pressure = int(command.split(",")[1])
                Logger.log_info(f"Set pressure command received: {pressure} hPa")
                # Update the reference pressure for the BMP280 sensor
                self.sensor_manager.set_pressure_reference(pressure)

            # ---- System Cycle and CO2 Interval Commands ----

            # Set the sensor data query cycle duration in minutes (e.g., "SET_CYCLE_MINS,5")
            elif command.startswith("SET_CYCLE_MINS"):
                new_cycle = int(command.split(",")[1])
                Logger.log_info(f"Set cycle command received: {new_cycle} minute(s)")
                # Update the system's sensor query interval
                self.sensor_manager.set_cycle(new_cycle)

            # Set the CO2 measurement interval for the SCD30 sensor (e.g., "SET_CO2_INTERVAL,10")
            elif command.startswith("SET_CO2_INTERVAL"):
                interval = int(command.split(",")[1])
                Logger.log_info(f"Set CO2 interval command received: {interval} second(s)")
                # Update the CO2 measurement interval for the SCD30 sensor
                self.sensor_manager.set_co2_interval(interval)

            # ---- System Reset Command ----

            # Reset the Raspberry Pi Pico ("RESET_PICO")
            elif command == "RESET_PICO":
                Logger.log_info("Reset command received.")
                # Reset the Raspberry Pi Pico
                self.sensor_manager.reset_pico()

            # ---- Invalid Command ----

            else:
                # Log an error if the command is not recognized
                Logger.log_error("Invalid command received.")

        except Exception as e:
            # Log detailed error information if any exceptions occur during command handling
            Logger.log_traceback_error(e)