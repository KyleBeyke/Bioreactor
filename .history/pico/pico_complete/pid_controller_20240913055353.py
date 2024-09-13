# pid_controller.py

"""
PIDController handles the PID logic for heater control based on temperature feedback.
"""

import time

class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint):
        """Initializes the PID controller with provided gains and target setpoint."""
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.integral = 0
        self.prev_error = 0
        self.prev_time = time.monotonic()

    def compute(self, current_value):
        """Computes the PID output based on the current value."""
        error = self.setpoint - current_value
        current_time = time.monotonic()
        delta_time = current_time - self.prev_time

        if delta_time == 0:
            return 0  # Avoid division by zero

        # Proportional term
        P = self.Kp * error

        # Integral term
        self.integral += error * delta_time
        I = self.Ki * self.integral

        # Derivative term
        derivative = (error - self.prev_error) / delta_time
        D = self.Kd * derivative

        # Calculate PID output
        output = P + I + D

        # Update previous values for next iteration
        self.prev_error = error
        self.prev_time = current_time

        return output