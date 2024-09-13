# auto_tuning_pid.py

"""
AutoTuningPIDController handles the auto-tuning of PID parameters based on system response.
"""

import time
from logger import Logger

class AutoTuningPIDController:
    def __init__(self, heater_controller):
        """Initialize the auto-tuning controller with access to the heater."""
        self.heater_controller = heater_controller
        self.Kp = 0
        self.Ki = 0
        self.Kd = 0
        self.critical_gain = None
        self.critical_period = None
        self.oscillation_data = []
        self.tuning_complete = False

    def force_oscillation(self, step_size=100):
        """Forces the heater to a high duty cycle to induce oscillations."""
        Logger.log_info("Forcing oscillations with a step input.")
        self.heater_controller.set_duty_cycle(step_size)

    def detect_oscillations(self, temperature_reading):
        """Detects oscillations and measures their period."""
        if len(self.oscillation_data) < 2:
            self.oscillation_data.append((time.monotonic(), temperature_reading))
        else:
            prev_time, prev_temp = self.oscillation_data[-1]
            curr_time = time.monotonic()

            if prev_temp > temperature_reading:  # Peak detected
                period = curr_time - prev_time
                Logger.log_info(f"Oscillation detected with period: {period} seconds.")
                self.oscillation_data.append((curr_time, temperature_reading))
                return True, period

        return False, None

    def calculate_pid_parameters(self):
        """Calculates PID parameters using Ziegler-Nichols method."""
        Logger.log_info("Calculating PID parameters using Ziegler-Nichols tuning.")
        if self.critical_gain and self.critical_period:
            self.Kp = 0.6 * self.critical_gain
            self.Ki = 2 * self.Kp / self.critical_period
            self.Kd = self.Kp * self.critical_period / 8
            Logger.log_info(f"Auto-tuned PID parameters: Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd}")
            return self.Kp, self.Ki, self.Kd

    def auto_tune(self):
        """Performs auto-tuning to calculate the best PID values."""
        Logger.log_info("Starting PID auto-tuning process.")
        self.force_oscillation(step_size=100)

        while not self.tuning_complete:
            temperature = self.heater_controller.get_temperature()  # Example function, should be part of HeaterController
            oscillation_detected, period = self.detect_oscillations(temperature)

            if oscillation_detected:
                if self.critical_gain is None:
                    self.critical_gain = 100  # Assume initial critical gain
                self.critical_period = period
                self.tuning_complete = True

        return self.calculate_pid_parameters()