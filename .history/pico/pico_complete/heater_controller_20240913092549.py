# heater_controller.py

"""
HeaterController manages the control of an AC heater using PID control and zero-cross detection.
The controller ensures that the duty cycle does not exceed a defined maximum (adjustable via commands)
and uses phase-delay switching to control the heater's power.

Dependencies:
- digitalio: For controlling the heater's GPIO pin.
- countio: For counting zero-cross events in the AC signal.
- asyncio: For managing asynchronous tasks (such as zero-cross handling).
- Logger: For logging important events and errors.
"""

import digitalio
import countio
import asyncio
from logger import Logger

class HeaterController:
    def __init__(self, zero_cross_pin, control_pin, pid_controller, max_duty_cycle=40):
        """
        Initializes the HeaterController with the necessary components.

        Args:
            zero_cross_pin (Pin): The pin connected to the zero-cross detection circuit.
            control_pin (Pin): The GPIO pin that controls the heater (on/off signal).
            pid_controller (PIDController): An instance of PIDController to manage temperature control.
            max_duty_cycle (int): The maximum allowable duty cycle (0-100%). Defaults to 40%.
        """
        # Initialize the heater control pin (set to OUTPUT mode)
        self.control_pin = digitalio.DigitalInOut(control_pin)
        self.control_pin.direction = digitalio.Direction.OUTPUT
        self.control_pin.value = False  # Ensure heater is off initially

        # Initialize the zero-cross detection counter (for AC signal phase control)
        self.zero_cross = countio.Counter(zero_cross_pin, edge=countio.Edge.RISE)

        # Default half-cycle time for 50Hz AC (10ms), can be recalculated dynamically
        self.ac_half_cycle_time = 0.01

        # Initialize the duty cycle (0 to 100%)
        self.duty_cycle = 0

        # Maximum duty cycle to limit heater power
        self.max_duty_cycle = max_duty_cycle

        # Heater's operational state (True if ON, False if OFF)
        self.state = False

        # PID controller to manage heater power based on temperature feedback
        self.pid_controller = pid_controller

        # Track the time of the last zero-cross event to calculate phase delay
        self.last_zero_cross_time = 0

    async def zero_cross_task(self):
        """
        Asynchronous task to handle zero-cross detection and phase-delay switching.

        The task continuously monitors zero-cross events and adjusts the heater's power based on
        the duty cycle calculated by the PID controller. It uses phase-delay control to modulate
        power within each AC half-cycle.

        Runs indefinitely as long as the controller is active.
        """
        previous_count = self.zero_cross.count  # Store the initial zero-cross count
        while True:
            try:
                # Check if a new zero-cross event has occurred
                if self.zero_cross.count > previous_count:
                    # Calculate the current time and the time difference from the last zero-cross event
                    current_time = time.monotonic()
                    if self.last_zero_cross_time != 0:
                        # Calculate the time for one full AC cycle (between zero crosses)
                        cycle_time = current_time - self.last_zero_cross_time
                        self.ac_half_cycle_time = cycle_time / 2  # Half-cycle time for phase-delay control

                    # Update the count and last zero-cross time
                    previous_count = self.zero_cross.count
                    self.last_zero_cross_time = current_time

                    if self.state:  # Heater is ON
                        # Calculate the phase delay based on the duty cycle
                        phase_delay = (1 - self.duty_cycle / 100) * self.ac_half_cycle_time
                        await asyncio.sleep(phase_delay)  # Wait for the phase delay to apply

                        # Turn the heater ON for a brief period to inject power into the AC cycle
                        self.control_pin.value = True
                        await asyncio.sleep(0.0001)  # Keep heater ON briefly (100µs)
                        self.control_pin.value = False  # Turn the heater OFF again

                await asyncio.sleep(0)  # Yield control to allow other tasks to run
            except Exception as e:
                # Log any unexpected errors during zero-cross detection or phase-delay control
                Logger.log_traceback_error(e)

    def set_duty_cycle(self, duty_cycle):
        """
        Sets the duty cycle for the heater, ensuring it doesn't exceed the maximum allowed duty cycle.

        Args:
            duty_cycle (int): The desired duty cycle (0-100%).

        If the requested duty cycle exceeds the maximum allowed duty cycle, it is capped to the
        predefined limit (max_duty_cycle). This protects the heater from operating at excessive power levels.
        """
        # Ensure the duty cycle does not exceed the configured maximum
        self.duty_cycle = min(duty_cycle, self.max_duty_cycle)
        # Log the updated duty cycle for debugging and tracking
        Logger.log_info(f"Duty cycle set to: {self.duty_cycle}% (capped at {self.max_duty_cycle}%)")

    def turn_on(self):
        """
        Turns the heater ON and logs the event. The heater will be controlled by the zero-cross task.
        """
        self.state = True  # Update the state to ON
        Logger.log_info("Heater turned ON.")  # Log the heater state change

    def turn_off(self):
        """
        Turns the heater OFF and logs the event. This stops power delivery to the heater.
        """
        self.state = False  # Update the state to OFF
        Logger.log_info("Heater turned OFF.")  # Log the heater state change
