import time
import digitalio
import board
import countio
import asyncio

class AC_Heater:
    def __init__(self, zero_cross_pin, control_pin, initial_debounce_time=0.005):
        """
        Initialize the AC heater controller with a Zero Crossing and Control pin.
        :param zero_cross_pin: The pin connected to the zero-cross detection.
        :param control_pin: The pin connected to control the heater (dimming or power control).
        :param initial_debounce_time: Initial debounce time in seconds (default 5ms).
        """
        # Setup control pin (PWM or digital out)
        self.control_pin = digitalio.DigitalInOut(control_pin)
        self.control_pin.direction = digitalio.Direction.OUTPUT
        self.control_pin.value = False

        # Zero-crossing detector using countio
        self.zero_cross = countio.Counter(zero_cross_pin, edge=countio.Edge.RISE)

        # Timing variables
        self.ac_half_cycle_time = 0.01  # Default for 50Hz (10ms half-cycle)
        self.duty_cycle = 0  # Duty cycle in percentage (0-100)
        self.state = False  # Whether heater is on or off

        # Debouncing related variables
        self.debounce_time = initial_debounce_time  # Initial debounce time
        self.last_zero_cross_time = 0  # Last time a zero-cross event was handled
        self.last_cycle_time = 0  # Duration of the last AC cycle

    async def zero_cross_task(self):
        """Task that runs to handle zero crossing events asynchronously with self-adjusting debouncing."""
        previous_count = self.zero_cross.count
        while True:
            if self.zero_cross.count > previous_count:
                # Zero-cross detected
                current_time = time.monotonic()

                # Calculate the time since the last zero-cross event
                if self.last_zero_cross_time != 0:
                    cycle_time = current_time - self.last_zero_cross_time
                    self.ac_half_cycle_time = cycle_time / 2  # Update half-cycle time

                    # Adjust debounce time based on the cycle time (10% of the half-cycle)
                    self.debounce_time = 0.1 * self.ac_half_cycle_time

                # Debounced zero-crossing event (ensure debounce time has passed)
                if current_time - self.last_zero_cross_time >= self.debounce_time:
                    previous_count = self.zero_cross.count
                    self.last_zero_cross_time = current_time  # Update last zero-cross time

                    if self.state:
                        # Dynamically adjust delay based on zero-cross timing and duty cycle
                        phase_delay = (1 - self.duty_cycle / 100) * self.ac_half_cycle_time
                        await asyncio.sleep(phase_delay)

                        # Briefly trigger the control pin to activate the heater (or TRIAC)
                        self.control_pin.value = True
                        await asyncio.sleep(0.0001)  # Brief pulse (approximate 100 µs)
                        self.control_pin.value = False

            # Allow other tasks to run
            await asyncio.sleep(0)

    def set_duty_cycle(self, duty_cycle):
        """
        Set the duty cycle (0 to 100) for the heater.
        :param duty_cycle: A value between 0 and 100.
        """
        if 0 <= duty_cycle <= 100:
            self.duty_cycle = duty_cycle
        else:
            raise ValueError("Duty cycle must be between 0 and 100")

    def turn_on(self, duty_cycle=100):
        """Turn on the heater with a specified duty cycle."""
        self.set_duty_cycle(duty_cycle)
        self.state = True

    def turn_off(self):
        """Turn off the heater."""
        self.state = False

# Example usage
async def main():
    # Define the GPIO pins
    zero_cross_pin = board.GP14  # Pin connected to zero-cross detection
    control_pin = board.GP15  # Pin connected to heater control

    # Initialize the heater control
    heater = AC_Heater(zero_cross_pin, control_pin)

    # Turn on the heater at 50% duty cycle
    heater.turn_on(duty_cycle=50)

    # Start the zero-cross detection task
    await asyncio.gather(heater.zero_cross_task())

# Run the asynchronous main loop
asyncio.run(main())
