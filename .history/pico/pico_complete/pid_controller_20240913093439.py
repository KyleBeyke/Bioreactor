# pid_controller.py

"""
PIDController class implements a PID control loop for managing heater control.

The PID (Proportional-Integral-Derivative) controller calculates the control output based on the
difference between a desired setpoint and the current value of the system. It uses three terms:
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
        self.Kp = Kp  # Proportional gain
        self.Ki = Ki  # Integral gain
        self.Kd = Kd  # Derivative gain
        self.setpoint = setpoint  # Desired target value
        self.integral = 0  # Sum of past errors (integral term)
        self.prev_error = 0  # The previous error value for derivative calculation
        self.prev_time = time.monotonic()  # Time of the last compute call (used for delta time)

    def compute(self, current_value):
        """
        Computes the PID output based on the current system value.

        This method is called in a control loop to continuously adjust the system output based on
        the difference between the current value and the desired setpoint.

        Args:
            current_value (float): The current value of the system being controlled.

        Returns:
            float: The PID output, which can be used to control the system (e.g., heater duty cycle).
        """
        # Calculate the error between the setpoint and the current system value
        error = self.setpoint - current_value

        # Get the current time and compute the time elapsed since the last computation
        current_time = time.monotonic()
        delta_time = current_time - self.prev_time

        # Ensure delta_time is positive and non-zero to avoid division by zero in derivative calculation
        if delta_time <= 0:
            return 0  # If no time has passed, no control action is needed

        # Proportional term (P): Directly proportional to the current error
        P = self.Kp * error

        # Integral term (I): Accumulates past errors over time
        # Helps eliminate long-term steady-state errors in the system
        self.integral += error * delta_time
        I = self.Ki * self.integral

        # Derivative term (D): Predicts future error based on the rate of change of the error
        derivative = (error - self.prev_error) / delta_time
        D = self.Kd * derivative

        # Calculate the PID output by summing the three components
        output = P + I + D

        # Update previous values for the next iteration
        self.prev_error = error  # Store the current error for future derivative calculation
        self.prev_time = current_time  # Update the time for the next cycle

        # Return the final computed PID output
        return output

