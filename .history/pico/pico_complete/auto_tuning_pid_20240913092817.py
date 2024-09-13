# auto_tuning_pid.py

"""
AutoTuningPIDController is responsible for automatically tuning PID parameters using
the Ziegler-Nichols method. It induces system oscillations, detects critical gain and period,
and calculates the optimal Kp, Ki, and Kd values based on the observed behavior.

Dependencies:
- heater_controller: The controller that manages the heater's duty cycle and provides temperature feedback.
- logger: Used for logging important events and errors.
"""

import time
from logger import Logger

class AutoTuningPIDController:
    def __init__(self, heater_controller):
        """
        Initializes the auto-tuning controller with access to the heater.

        Args:
            heater_controller: Instance of HeaterController to control the heater and get temperature readings.
        """
        self.heater_controller = heater_controller  # Access to heater control and temperature feedback
        self.Kp = 0  # Proportional gain (to be tuned)
        self.Ki = 0  # Integral gain (to be tuned)
        self.Kd = 0  # Derivative gain (to be tuned)
        self.critical_gain = None  # Critical gain for oscillations
        self.critical_period = None  # Critical period between oscillations
        self.oscillation_data = []  # Stores time and temperature data points for oscillation detection
        self.tuning_complete = False  # Flag to indicate when tuning is complete

    def force_oscillation(self, step_size=100):
        """
        Forces the heater to a high duty cycle to induce oscillations in the system.

        Args:
            step_size (int): The duty cycle percentage to force the heater to, inducing system oscillations.

        The goal is to push the system into oscillations by setting the heater to a high duty cycle,
        allowing us to measure the system's natural response.
        """
        Logger.log_info("Forcing oscillations with a step input.")
        # Set the heater to the desired high duty cycle to induce oscillations
        self.heater_controller.set_duty_cycle(step_size)

    def detect_oscillations(self, temperature_reading):
        """
        Detects oscillations in the system's temperature response and measures the period between them.

        Args:
            temperature_reading (float): The current temperature reading from the system.

        Returns:
            (bool, float): A tuple indicating whether an oscillation was detected, and the period of oscillation.
        """
        try:
            # Store the first two temperature data points to detect oscillations
            if len(self.oscillation_data) < 2:
                self.oscillation_data.append((time.monotonic(), temperature_reading))
                return False, None  # Not enough data to detect oscillations yet

            # Retrieve the last recorded time and temperature
            prev_time, prev_temp = self.oscillation_data[-1]
            curr_time = time.monotonic()

            # Detect a temperature peak (oscillation) by checking if temperature is decreasing
            if prev_temp > temperature_reading:
                period = curr_time - prev_time  # Calculate the time period between oscillations
                Logger.log_info(f"Oscillation detected with period: {period} seconds.")
                self.oscillation_data.append((curr_time, temperature_reading))  # Log the new oscillation
                return True, period

        except Exception as e:
            Logger.log_traceback_error(e)  # Log any errors during oscillation detection

        return False, None  # No oscillation detected or an error occurred

    def calculate_pid_parameters(self):
        """
        Calculates the PID parameters (Kp, Ki, Kd) using the Ziegler-Nichols method.

        The method uses the system's critical gain and period to calculate optimal PID values.

        Returns:
            (float, float, float): The calculated values for Kp, Ki, and Kd.
        """
        try:
            Logger.log_info("Calculating PID parameters using Ziegler-Nichols tuning.")
            # Ensure that we have both critical gain and period before calculating
            if self.critical_gain and self.critical_period:
                self.Kp = 0.6 * self.critical_gain  # Ziegler-Nichols proportional gain
                self.Ki = 2 * self.Kp / self.critical_period  # Integral gain based on critical period
                self.Kd = self.Kp * self.critical_period / 8  # Derivative gain based on critical period
                Logger.log_info(f"Auto-tuned PID parameters: Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd}")
                return self.Kp, self.Ki, self.Kd  # Return the calculated values
        except Exception as e:
            Logger.log_traceback_error(e)  # Log any errors during PID calculation

        return None, None, None  # Return None if PID parameters couldn't be calculated

    def auto_tune(self):
        """
        Performs the auto-tuning process to calculate the best PID values.

        The system is driven into oscillations, and the critical gain and period are used to
        calculate optimal PID values. The process continues until the tuning is complete.

        Returns:
            (float, float, float): The auto-tuned Kp, Ki, and Kd values for the PID controller.
        """
        Logger.log_info("Starting PID auto-tuning process.")
        self.force_oscillation(step_size=100)  # Induce oscillations by setting a high duty cycle

        while not self.tuning_complete:
            try:
                # Get the current temperature from the heater controller (should be implemented in HeaterController)
                temperature = self.heater_controller.get_temperature()

                # Detect oscillations and measure the critical period
                oscillation_detected, period = self.detect_oscillations(temperature)

                # If oscillations are detected, calculate the critical gain and period
                if oscillation_detected:
                    if self.critical_gain is None:
                        self.critical_gain = 100  # Initial guess for the critical gain (adjust as needed)
                    self.critical_period = period
                    self.tuning_complete = True  # Mark tuning as complete after detection
            except Exception as e:
                Logger.log_traceback_error(e)  # Log any errors during the auto-tuning process

        return self.calculate_pid_parameters()  # Calculate and return the final PID parameters
