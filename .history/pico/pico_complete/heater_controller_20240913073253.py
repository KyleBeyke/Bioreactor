# heater_controller.py

"""
HeaterController handles the control of the AC heater using PID control, zero-cross detection,
and phase-delay switching. It ensures that the duty cycle does not exceed a defined maximum,
which can be adjusted via commands.
"""

import digitalio
import countio
import asyncio
from logger import Logger

class HeaterController:
    def __init__(self, zero_cross_pin, control_pin, pid_controller, max_duty_cycle=40):
        """
        Initializes the heater controller with zero-cross detection and PID control.

        Args:
            zero_cross_pin: The pin connected to the zero-crossing detector.
            control_pin: The pin used to control the heater.
            pid_controller: An instance of the PIDController to manage the temperature.
            max_duty_cycle: The maximum allowed duty cycle for the heater (default is 40%).
        """
        # Setup for controlling the heater's output signal
        self.control_pin = digitalio.DigitalInOut(control_pin)
        self.control_pin.direction = digitalio.Direction.OUTPUT
        self.control_pin.value = False  # Initial state: heater off

        # Zero-crossing detection setup (used for phase control)
        self.zero_cross = countio.Counter(zero_cross_pin, edge=countio.Edge.RISE)
        self.ac_half_cycle_time = 0.01  # Default for 50Hz AC (10ms half-cycle)

        # Heater control variables
        self.duty_cycle = 0  # Initial duty cycle (0-100% range)
        self.max_duty_cycle = max_duty_cycle  # Maximum allowed duty cycle (capped by default to 40%)
        self.state = False  # Tracks whether the heater is ON or OFF

        # PID controller instance (used to calculate the appropriate duty cycle)
        self.pid_controller = pid_controller

        # Last recorded time of a zero-crossing event (for timing phase delays)
        self.last_zero_cross_time = 0

    async def zero_cross_task(self):
        """
        Asynchronous task to monitor the zero-cross events of the AC signal. The heater is controlled
        based on phase delays derived from the desired duty cycle, calculated by the PID controller.

        This task continuously runs, detecting the zero-cross events and turning the heater on for the
        correct portion of each AC cycle to achieve the target duty cycle.
        """
        previous_count = self.zero_cross.count  # Tracks the last zero-cross event count

        # Continuously check for zero-crossing events to control the heater asynchronously
        while True:
            try:
                # Check if a new zero-cross event has been detected
                if self.zero_cross.count > previous_count:
                    current_time = time.monotonic()  # Get the current time (in seconds)

                    # Calculate the time between two zero-cross events to determine the AC cycle time
                    if self.last_zero_cross_time != 0:
                        cycle_time = current_time - self.last_zero_cross_time
                        self.ac_half_cycle_time = cycle_time / 2  # Half-cycle time for phase control

                    previous_count = self.zero_cross.count  # Update the count to the current value
                    self.last_zero_cross_time = current_time  # Update the last zero-cross timestamp

                    # If the heater is on, adjust the phase based on the calculated duty cycle
                    if self.state:
                        # Calculate the phase delay (off-time) based on the duty cycle
                        phase_delay = (1 - self.duty_cycle / 100) * self.ac_half_cycle_time
                        await asyncio.sleep(phase_delay)  # Wait for the correct phase delay before turning on the heater

                        # Turn the heater on briefly, then turn it off again after a short pulse (phase control)
                        self.control_pin.value = True
                        await asyncio.sleep(0.0001)  # Brief pulse of 100 µs to control the heater
                        self.control_pin.value = False

                await asyncio.sleep(0)  # Small delay to yield control back to the event loop

            except Exception as e:
                # Log any errors that occur during zero-cross detection or heater control
                Logger.log_traceback_error(e)

    def set_duty_cycle(self, duty_cycle):
        """
        Sets the duty cycle for the heater but ensures it doesn't exceed the maximum duty cycle.

        Args:
            duty_cycle (float): The desired duty cycle percentage (0-100%).
        """
        # Cap the duty cycle to the maximum allowed duty cycle value (e.g., 40%)
        self.duty_cycle = min(duty_cycle, self.max_duty_cycle)
        # Log the adjusted duty cycle for debugging purposes
        Logger.log_info(f"Duty cycle set to: {self.duty_cycle}% (capped at {self.max_duty_cycle}%)")

    def turn_on(self):
        """
        Turns the heater ON by enabling the state and allowing the phase control logic
        to manage the AC switching during zero-cross events.
        """
        self.state = True  # Mark the heater as ON
        Logger.log_info("Heater turned ON.")  # Log the heater state change

    def turn_off(self):
        """
        Turns the heater OFF by disabling the state and stopping phase control, ensuring
        that the heater stays off until re-enabled.
        """
        self.state = False  # Mark the heater as OFF
        Logger.log_info("Heater turned OFF.")  # Log the heater state change
