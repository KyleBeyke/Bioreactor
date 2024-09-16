"""
HeaterController manages the control of an AC heater using PID control and zero-cross detection.
The controller ensures that the duty cycle does not exceed a defined maximum and uses phase-delay
switching to control the heater's power.

Dependencies:
- digitalio: For controlling the heater's GPIO pin.
- countio: For counting zero-cross events in the AC signal.
- asyncio: For managing asynchronous tasks.
- Logger: For logging important events and errors.
"""

import digitalio
import countio
import asyncio
from logger import Logger

class HeaterController:
    def __init__(self, zero_cross_pin, control_pin, pid_controller, max_duty_cycle=30):
        """
        Initializes the HeaterController with the necessary components.

        Args:
            zero_cross_pin (Pin): The pin connected to the zero-cross detection circuit.
            control_pin (Pin): The GPIO pin that controls the heater (on/off signal).
            pid_controller (PIDController): An instance of PIDController to manage temperature control.
            max_duty_cycle (int): The maximum allowable duty cycle (0-100%). Defaults to 40%.
        """
        self.control_pin = digitalio.DigitalInOut(control_pin)
        self.control_pin.direction = digitalio.Direction.OUTPUT
        self.control_pin.value = False  # Ensure heater is off initially

        self.zero_cross = countio.Counter(zero_cross_pin, edge=countio.Edge.RISE)
        self.ac_half_cycle_time = 0.01  # Default half-cycle time for 50Hz AC (10ms)
        self.duty_cycle = 0
        self.max_duty_cycle = max_duty_cycle
        self.state = False  # Heater's operational state (True if ON, False if OFF)
        self.pid_controller = pid_controller
        self.last_zero_cross_time = 0

    async def zero_cross_task(self):
        """
        Asynchronous task to handle zero-cross detection and phase-delay switching.

        The task continuously monitors zero-cross events and adjusts the heater's power based on
        the duty cycle calculated by the PID controller.
        """
        previous_count = self.zero_cross.count  # Store the initial zero-cross count
        while True:
            try:
                if self.zero_cross.count > previous_count:
                    current_time = time.monotonic()
                    if self.last_zero_cross_time != 0:
                        cycle_time = current_time - self.last_zero_cross_time
                        self.ac_half_cycle_time = cycle_time / 2

                    previous_count = self.zero_cross.count
                    self.last_zero_cross_time = current_time

                    if self.state:  # Heater is ON
                        phase_delay = (1 - self.duty_cycle / 100) * self.ac_half_cycle_time
                        await asyncio.sleep(phase_delay)
                        self.control_pin.value = True
                        await asyncio.sleep(0.0001)  # 100µs pulse for phase-delay control
                        self.control_pin.value = False

                await asyncio.sleep(0)
            except Exception as e:
                Logger.log_traceback_error(e)
                raise RuntimeError("Critical failure in zero-cross task. Halting system.") from e

    def set_duty_cycle(self, duty_cycle):
        """
        Sets the duty cycle for the heater, ensuring it doesn't exceed the maximum allowed duty cycle.

        Args:
            duty_cycle (int): The desired duty cycle (0-100%).
        """
        self.duty_cycle = min(duty_cycle, self.max_duty_cycle)
        Logger.log_info(f"Duty cycle set to: {self.duty_cycle}% (capped at {self.max_duty_cycle}%)")

    def turn_on(self):
        """
        Turns the heater ON and logs the event.
        """
        self.state = True
        Logger.log_info("Heater turned ON.")

    def turn_off(self):
        """
        Turns the heater OFF and logs the event.
        """
        self.state = False
        Logger.log_info("Heater turned OFF.")
