# command_handler.py

"""
CommandHandler handles all incoming commands from the Raspberry Pi and controls the heater and other system components.
"""

from logger import Logger

class CommandHandler:
    def __init__(self, heater_controller, sensor_manager):
        """Initializes the command handler with access to heater and sensor manager."""
        self.heater_controller = heater_controller
        self.sensor_manager = sensor_manager

    def handle(self, command):
        """Handles commands from the Raspberry Pi."""
        try:
            Logger.log_info(f"Received command: {command}")
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

            # Add other commands here (e.g., recalibration, data request)
            else:
                Logger.log_error("Invalid command received.")
        except Exception as e:
            Logger.log_traceback_error(e)
