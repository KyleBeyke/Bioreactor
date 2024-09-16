# code.py

"""
Main control loop that manages sensors, heater control, and command processing.

This script is responsible for:
- Initializing the system components (sensors, heater, and PID controller).
- Running PID auto-tuning to optimize control parameters.
- Handling asynchronous tasks for sensor reading, heater control, and command handling.
- Periodically logging sensor data and processing commands from the Raspberry Pi.

Dependencies:
- asyncio: For managing asynchronous tasks.
- supervisor: To check for serial commands.
- logger: For logging system information and errors.
- sensor_manager: For initializing and reading from the system sensors.
- heater_controller: For controlling the heater using PID control.
- pid_controller: For the PID control logic.
- command_handler: For processing commands from the Raspberry Pi.
"""

import time
import asyncio
from logger import Logger
from sensor_manager import SensorManager
from heater_controller import HeaterController
from pid_controller import PIDController
from command_handler import CommandHandler
import supervisor

# Global constants (placeholders for the actual values)
default_sensor_query_interval = 300  # Default to 5 minutes for sensor data queries
heater_temp_query_interval = 5  # Heater query interval for more frequent temperature checks
default_temperature = 43  # Default target temperature in °C

async def control_loop():
    """
    Main control loop that initializes the system, handles sensor readings, and processes commands.

    This loop initializes the sensors, heater, and PID controller. It also performs auto-tuning for the PID
    control loop. After initialization, it periodically reads sensor data, logs information, and handles
    commands from the Raspberry Pi.
    """

    # Log the system start and warm-up period
    Logger.log_info("Starting system... warming up sensors for 15 seconds.")
    await asyncio.sleep(15)  # Delay for sensor warm-up (use asyncio.sleep for async compatibility)

    # Step 1: Initialize system components
    Logger.log_info("Initializing system components...")
    sensor_manager = SensorManager()
    sensor_manager.initialize_sensors()  # Initialize sensors

    # Step 2: Initialize PID controller with default tuning values (will be auto-tuned)
    pid_controller = PIDController(Kp=2.0, Ki=0.1, Kd=0.05, setpoint=default_temperature)

    # Step 3: Initialize the heater controller
    # NOTE: Ensure that zero_cross_pin and heater_control_pin are defined elsewhere in your code.
    heater_controller = HeaterController(zero_cross_pin=zero_cross_pin, control_pin=heater_control_pin, pid_controller=pid_controller)

    # Step 4: Run PID auto-tuning before entering the main control loop
    Logger.log_info("Running auto-tuning for PID parameters...")
    auto_tuner = AutoTuningPIDController(heater_controller)
    tuned_Kp, tuned_Ki, tuned_Kd = auto_tuner.auto_tune()  # Perform auto-tuning for PID parameters

    # Step 5: Update the PID controller with the tuned values
    pid_controller.Kp = tuned_Kp
    pid_controller.Ki = tuned_Ki
    pid_controller.Kd = tuned_Kd
    Logger.log_info(f"Tuned PID parameters: Kp={tuned_Kp}, Ki={tuned_Ki}, Kd={tuned_Kd}")

    # Step 6: Initialize sensor query interval and heater control
    sensor_query_interval = default_sensor_query_interval

    # Step 7: Log initial sensor data after warm-up
    Logger.log_info("Sending initial sensor data after warm-up period.")
    try:
        # Compensate sensors and log the initial sensor readings
        sensor_manager.scd30.ambient_pressure = int(sensor_manager.bmp280.pressure)  # Pressure compensation for SCD30
        co2, temp, humidity, ds_temp, pressure = sensor_manager.read_sensors()  # Read sensor data
        Logger.log_info(f"Initial sensor data: CO2: {co2} ppm, Temp: {temp}°C, Humidity: {humidity}%, Pressure: {pressure} hPa")
    except Exception as e:
        Logger.log_traceback_error(e)  # Log any errors during sensor reading

    # Track the time of the last sensor reading
    last_reading_time = time.monotonic()

    # Step 8: Start the heater control tasks concurrently with other tasks
    Logger.log_info("Starting heater control and waiting for temperature stabilization...")

    # Launch all asynchronous tasks concurrently (zero crossing, temperature maintenance, and recalibration)
    await asyncio.gather(
        heater_controller.zero_cross_task(),  # Zero crossing task for AC heater control
        maintain_temperature(heater_controller, sensor_manager),  # PID-based temperature maintenance
        recalibrate_at_target_temp(sensor_manager)  # CO2 recalibration once the temperature stabilizes
    )

    # Main loop for sensor reading and command handling
    while True:
        current_time = time.monotonic()  # Get the current time

        # Step 9: Handle periodic sensor data logging
        if current_time - last_reading_time >= sensor_query_interval:
            try:
                # Update pressure compensation and log the sensor data
                sensor_manager.scd30.ambient_pressure = int(sensor_manager.bmp280.pressure)
                co2, temp, humidity, ds_temp, pressure = sensor_manager.read_sensors()
                Logger.log_info(f"Sensor data: CO2: {co2} ppm, Temp: {temp}°C, Humidity: {humidity}%, Pressure: {pressure} hPa")
                last_reading_time = current_time  # Update the last reading time
            except Exception as e:
                Logger.log_traceback_error(e)  # Log any errors during sensor reading

        # Step 10: Handle commands from the Raspberry Pi
        try:
            if supervisor.runtime.serial_bytes_available:
                command = input().strip()  # Read the incoming command
                command_handler.handle(command)  # Handle the command

                # Handle configurable sensor query interval through a command (e.g., "SET_CYCLE_MINS,5")
                if command.startswith("SET_CYCLE_MINS"):
                    new_cycle = int(command.split(",")[1]) * 60  # Convert minutes to seconds
                    sensor_query_interval = max(60, new_cycle)  # Ensure a minimum interval of 1 minute
                    Logger.log_info(f"Sensor query interval set to {sensor_query_interval} seconds.")
        except Exception as e:
            Logger.log_traceback_error(e)  # Log any errors during command handling

        # Small async sleep to allow other tasks to run efficiently
        await asyncio.sleep(1)

# Main entry point for the program
if __name__ == "__main__":
    # Run the control loop with asyncio
    asyncio.run(control_loop())
