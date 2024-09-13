# main.py

"""
Main control loop that manages sensors, heater control, and command processing.
"""

import time
import asyncio
from logger import Logger
from sensor_manager import SensorManager
from heater_controller import HeaterController
from pid_controller import PIDController
from command_handler import CommandHandler

def control_loop():
    """Main loop that initializes the system and handles command processing."""
    Logger.log_info("Starting system... warming up sensors for 15 seconds.")
    time.sleep(15)

    # Initialize all components
    sensor_manager = SensorManager()
    pid_controller = PIDController(Kp=2.0, Ki=0.1, Kd=0.05, setpoint=43)  # Example PID values
    heater_controller = HeaterController(board.GP14, board.GP15, pid_controller)
    command_handler = CommandHandler(heater_controller, sensor_manager)

    Logger.log_info("Starting heater control and waiting for temperature stabilization...")
    asyncio.run(heater_controller.zero_cross_task())
    asyncio.run(maintain_temperature(heater_controller, sensor_manager))

    # Main loop for handling sensor queries and commands
    while True:
        current_time = time.monotonic()
        if supervisor.runtime.serial_bytes_available:
            command = input().strip()
            command_handler.handle(command)

        # Other sensor data querying and logic can go here
        time.sleep(1)

if __name__ == "__main__":
    control_loop()
