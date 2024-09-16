"""
AutoTuningPIDController class for automatically tuning PID parameters using the Ziegler-Nichols method.

The AutoTuningPIDController performs the following tasks:
- Automatically tunes the Proportional (Kp), Integral (Ki), and Derivative (Kd) values using system response data.
- Uses forced oscillations to identify the critical gain (Ku) and critical period (Pu) for optimal PID tuning.
- Provides dynamic adjustment of the critical gain to control the system's oscillations during the tuning process.
- Once tuned, the calculated PID parameters are applied to the PID controller managing the system (e.g., heater).

Key Features:
- Force the heater into oscillations by setting a high duty cycle.
- Detect the system's natural oscillations, measuring the critical period (Pu) and adjusting critical gain dynamically.
- Calculate and update PID parameters based on the Ziegler-Nichols tuning method.
- Commands and logs are used to provide feedback and control the tuning process.

System Components:
- HeaterController: Provides heater control during the tuning process by setting duty cycles and reading temperatures.
- PIDController: The base PID controller to which the tuned parameters (Kp, Ki, Kd) are applied.

Dependencies:
- time: Used for time measurements to calculate the oscillation period and control delays.
- logger: For logging tuning progress, errors, and final results.
- pid_controller: The PID controller that manages the system after tuning.
- heater_controller: The system component controlling the heater during the tuning process.
"""

import time
from logger import Logger
from pid_controller import PIDController

class AutoTuningPIDController:
    """
    AutoTuningPIDController automatically tunes PID parameters using the Ziegler-Nichols method.
    It induces system oscillations, detects critical gain and period, and calculates optimal Kp, Ki, Kd values.
    """

    def __init__(self, heater_controller, initial_Kp=1.0, initial_Ki=0.0, initial_Kd=0.0):
        """
        Initializes the auto-tuning controller.

        Args:
            heater_controller: Instance of HeaterController to control the heater.
            initial_Kp (float): Initial guess for the proportional gain.
            initial_Ki (float): Initial guess for the integral gain.
            initial_Kd (float): Initial guess for the derivative gain.
        """
        self.heater_controller = heater_controller
        self.pid_controller = PIDController(initial_Kp, initial_Ki, initial_Kd, setpoint=0)
        self.Kp = initial_Kp
        self.Ki = initial_Ki
        self.Kd = initial_Kd
        self.critical_gain = None
        self.critical_period = None
        self.oscillation_data = []
        self.tuning_complete = False
        self.max_critical_gain = 200
        self.min_critical_gain = 50
        self.gain_increase_rate = 1.1
        self.gain_decrease_rate = 0.9
        self.oscillation_threshold = 0.05

    def force_oscillation(self, step_size=100):
        """
        Forces the heater to induce oscillations.

        Args:
            step_size (int): The duty cycle percentage to force the heater to.
        """
        Logger.log_info(f"Forcing oscillations with step input of {step_size}%.")
        self.heater_controller.set_duty_cycle(step_size)

    def detect_oscillations(self, temperature_reading):
        """
        Detects oscillations in the system's temperature response and measures the period.

        Args:
            temperature_reading (float): The current temperature reading from the system.

        Returns:
            (bool, float): A tuple indicating whether an oscillation was detected and its period.
        """
        current_time = time.monotonic()
        if len(self.oscillation_data) < 2:
            self.oscillation_data.append((current_time, temperature_reading))
            return False, None

        prev_time, prev_temp = self.oscillation_data[-1]

        if prev_temp > temperature_reading and abs(prev_temp - temperature_reading) > self.oscillation_threshold:
            period = current_time - prev_time
            Logger.log_info(f"Oscillation detected with period: {period} seconds.")
            self.oscillation_data.append((current_time, temperature_reading))
            return True, period

        return False, None

    def adjust_critical_gain(self, oscillation_detected):
        """
        Adjusts the critical gain dynamically based on oscillations.

        Args:
            oscillation_detected (bool): Whether oscillations were detected.
        """
        if oscillation_detected:
            self.critical_gain *= self.gain_decrease_rate
            Logger.log_info(f"Decreasing critical gain to {self.critical_gain:.2f}.")
        else:
            self.critical_gain *= self.gain_increase_rate
            Logger.log_info(f"Increasing critical gain to {self.critical_gain:.2f}.")

        self.critical_gain = min(max(self.critical_gain, self.min_critical_gain), self.max_critical_gain)

    def calculate_pid_parameters(self):
        """
        Calculates PID parameters using Ziegler-Nichols tuning.

        Returns:
            (float, float, float): The tuned Kp, Ki, and Kd values.
        """
        if self.critical_gain and self.critical_period:
            self.Kp = 0.6 * self.critical_gain
            self.Ki = 2 * self.Kp / self.critical_period
            self.Kd = self.Kp * self.critical_period / 8
            Logger.log_info(f"Tuned PID parameters: Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd}")
            return self.Kp, self.Ki, self.Kd
        return None, None, None

    def auto_tune(self, setpoint):
        """
        Performs the auto-tuning process.

        Args:
            setpoint (float): The desired setpoint for the system.

        Returns:
            (float, float, float): The auto-tuned Kp, Ki, and Kd values.
        """
        Logger.log_info("Starting PID auto-tuning process.")
        self.pid_controller.setpoint = setpoint
        self.force_oscillation()

        while not self.tuning_complete:
            try:
                temperature = self.heater_controller.get_temperature()
                oscillation_detected, period = self.detect_oscillations(temperature)
                self.adjust_critical_gain(oscillation_detected)

                if oscillation_detected:
                    self.critical_period = period
                    self.tuning_complete = True
            except Exception as e:
                Logger.log_traceback_error(e)
                raise RuntimeError("Critical failure during auto-tuning. Halting system.") from e

        return self.calculate_pid_parameters()
