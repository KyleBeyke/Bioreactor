# heater_controller.py

"""
HeaterController handles the control of the heater using PID control, including managing the duty cycle and zero-cross detection.
"""

import digitalio
import countio
import asyncio
from logger import Logger

class HeaterController:
    def __init__(self, zero_cross_pin, control_pin, pid_controller, max_duty_cycle=40):
        """Initializes the heater controller with zero-cross detection and PID control."""
        self.control_pin = digitalio.DigitalInOut(control_pin)
        self.control_pin.direction = digitalio.Direction.OUTPUT
        self.control_pin.value = False

        self.zero_cross = countio.Counter(zero_cross_pin, edge=countio.Edge.RISE)
        self.ac_half_cycle_time = 0.01  # Default for 50Hz (10ms half-cycle)
        self.duty_cycle = 0  # Set by PID
        self.max_duty_cycle = max_duty_cycle
        self.state = False  # On/off state
        self.pid_controller = pid_controller
        self.last_zero_cross_time = 0

    async def zero_cross_task(self):
        """Asynchronous task for handling zero crossing and heater control."""
        previous_count = self.zero_cross.count
        while True:
            try:
                if self.zero_cross.count > previous_count:
                    current_time = time.monotonic()

                    if self.last_zero_cross_time != 0:
                        cycle_time = current_time - self.last_zero_cross_time
                        self.ac_half_cycle_time = cycle_time / 2

                    previous_count = self.zero_cross.count
                    self.last_zero_cross_time = current_time

                    if self.state:
                        # Calculate phase delay based on the duty cycle set by PID
                        phase_delay = (1 - self.duty_cycle / 100) * self.ac_half_cycle_time
                        await asyncio.sleep(phase_delay)
                        self.control_pin.value = True
                        await asyncio.sleep(0.0001)  # Brief pulse (100 µs)
                        self.control_pin.value = False
                await asyncio.sleep(0)
            except Exception as e:
                Logger.log_traceback_error(e)

    def set_duty_cycle(self, duty_cycle):
        """Caps the duty cycle to the max_duty_cycle value."""
        self.duty_cycle = min(duty_cycle, self.max_duty_cycle)

    def turn_on(self):
        """Turns the heater ON."""
        self.state = True
        Logger.log_info("Heater turned ON.")

    def turn_off(self):
        """Turns the heater OFF."""
        self.state = False
        Logger.log_info("Heater turned OFF.")
