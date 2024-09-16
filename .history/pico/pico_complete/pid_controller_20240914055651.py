"""
PIDController class implements a PID control loop for managing heater control.

The PID controller calculates the control output based on the difference between a desired setpoint and the current value.
It uses three terms:
- Proportional: Determines the reaction to the current error.
- Integral: Accumulates past errors to correct for long-term bias.
- Derivative: Predicts future error based on the rate of change.

Dependencies:
- time: For calculating time intervals between control loop executions.
"""

import time

class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint):
        """
        Initializes the PID controller with given parameters.

        Args:
            Kp (float): Proportional gain, controls the reaction to the current error.
            Ki (float): Integral gain, controls the reaction based on cumulative past errors.
            Kd (float): Derivative gain, controls the reaction based on the rate of error change.
            setpoint (float): The desired target value that the system should aim to achieve.
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.integral = 0  # Sum of past errors (integral term)
        self.prev_error = 0
        self.prev_time = time.monotonic()

    def compute(self, current_value):
        """
        Computes the PID output based on the current system value.

        Args:
            current_value (float): The current value of the system being controlled.

        Returns:
            float: The PID output, which can be used to control the system.
        """
        # Calculate error
        error = self.setpoint - current_value

        # Calculate time elapsed since the last computation
        current_time = time.monotonic()
        delta_time = current_time - self.prev_time

        if delta_time <= 0:
            return 0

        # Proportional term
        P = self.Kp * error

        # Integral term
        self.integral += error * delta_time
        I = self.Ki * self.integral

        # Derivative term
        derivative = (error - self.prev_error) / delta_time
        D = self.Kd * derivative

        # Compute PID output
        output = P + I + D

        # Update previous values for the next iteration
        self.prev_error = error
        self.prev_time = current_time

        return output

    def reset_integral(self):
        """
        Resets the integral component of the PID controller.
        This helps in preventing integral windup in cases where the system output is saturated.
        """
        self.integral = 0
