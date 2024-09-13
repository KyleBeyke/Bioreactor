# code.py

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
import supervisor

# Global constants (as placeholders for the actual values)
default_sensor_query_interval = 300  # Default to 5 minutes
heater_temp_query_interval = 5  # Heater query interval for temperature checks
default_temperature = 43

async def control_loop():
    """Main loop that initializes the system, handles sensor readings, and processes commands."""
    Logger.log_info("Starting system... warming up sensors for 15 seconds.")
    await asyncio.sleep(15)  # Use asyncio.sleep for async compatibility
    # Initialize system components
    Logger.log_info("Initializing system...")
    sensor_manager = SensorManager()
    sensor_manager.initialize_sensors()

    # Initialize PID controller (with default values, will be updated after auto-tuning)
    pid_controller = PIDController(Kp=2.0, Ki=0.1, Kd=0.05, setpoint=default_temperature)

    # Initialize heater controller
    heater_controller = HeaterController(zero_cross_pin=zero_cross_pin, control_pin=heater_control_pin, pid_controller=pid_controller)

    # Run auto-tuning before the main loop
    Logger.log_info("Running auto-tuning PID...")
    auto_tuner = AutoTuningPIDController(heater_controller)
    tuned_Kp, tuned_Ki, tuned_Kd = auto_tuner.auto_tune()

    # Set the new PID values
    pid_controller.Kp = tuned_Kp
    pid_controller.Ki = tuned_Ki
    pid_controller.Kd = tuned_Kd

    # Initialize sensor data and heater control
    sensor_query_interval = default_sensor_query_interval

    Logger.log_info("Sending initial sensor data after warm-up period.")
    try:
        # Compensate sensors and log initial readings
        sensor_manager.scd30.ambient_pressure = int(sensor_manager.bmp280.pressure)  # Compensation
        co2, temp, humidity, ds_temp, pressure = sensor_manager.read_sensors()
        Logger.log_info(f"Initial sensor data: CO2: {co2} ppm, Temp: {temp}°C, Humidity: {humidity}%, Pressure: {pressure} hPa")
    except Exception as e:
        Logger.log_traceback_error(e)

    last_reading_time = time.monotonic()

    # Start heater control tasks concurrently
    Logger.log_info("Starting heater control and waiting for temperature stabilization...")

    # Launch all asynchronous tasks concurrently
    await asyncio.gather(
        heater_controller.zero_cross_task(),  # Zero crossing task for heater control
        maintain_temperature(heater_controller, sensor_manager),  # PID-based temperature maintenance
        recalibrate_at_target_temp(sensor_manager)  # CO2 recalibration
    )

    # Main loop for sensor reading and command handling
    while True:
        current_time = time.monotonic()

        # Handle periodic sensor data logging
        if current_time - last_reading_time >= sensor_query_interval:
            try:
                sensor_manager.scd30.ambient_pressure = int(sensor_manager.bmp280.pressure)  # Update pressure compensation
                co2, temp, humidity, ds_temp, pressure = sensor_manager.read_sensors()
                Logger.log_info(f"Sensor data: CO2: {co2} ppm, Temp: {temp}°C, Humidity: {humidity}%, Pressure: {pressure} hPa")
                last_reading_time = current_time
            except Exception as e:
                Logger.log_traceback_error(e)

        # Handle commands from the Raspberry Pi
        try:
            if supervisor.runtime.serial_bytes_available:
                command = input().strip()
                command_handler.handle(command)

                # Handle configurable sensor query interval through a command
                if command.startswith("SET_CYCLE_MINS"):
                    new_cycle = int(command.split(",")[1]) * 60
                    sensor_query_interval = max(60, new_cycle)  # Minimum of 1 minute
                    Logger.log_info(f"Sensor query interval set to {sensor_query_interval} seconds.")
        except Exception as e:
            Logger.log_traceback_error(e)

        # Small async sleep to allow other tasks to run efficiently
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(control_loop())
