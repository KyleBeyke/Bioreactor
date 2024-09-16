import time
from logger import Logger
from pid_controller import PIDController

class AutoTuningPIDController:
    """
    AutoTuningPIDController is responsible for automatically tuning PID parameters
    using the Ziegler-Nichols method. It induces system oscillations, detects critical
    gain and period, and calculates the optimal Kp, Ki, and Kd values based on the system response.

    This class works in conjunction with the HeaterController and manages heater power during
    the tuning process to detect critical oscillation points.
    """
    
    def __init__(self, heater_controller, initial_Kp=1.0, initial_Ki=0.0, initial_Kd=0.0):
        """
        Initializes the AutoTuningPIDController with a reference to the HeaterController.

        Args:
            heater_controller (HeaterController): Instance of HeaterController to control the heater.
            initial_Kp (float): Initial guess for the proportional gain.
            initial_Ki (float): Initial guess for the integral gain.
            initial_Kd (float): Initial guess for the derivative gain.
        """
        self.heater_controller = heater_controller
        
        # Initialize the PID controller with starting values
        self.pid_controller = PIDController(initial_Kp, initial_Ki, initial_Kd, setpoint=0)
        
        # Initial guesses for PID parameters
        self.Kp = initial_Kp
        self.Ki = initial_Ki
        self.Kd = initial_Kd

        # Critical gain (Ku) and critical period (Pu) used in Ziegler-Nichols tuning
        self.critical_gain = None  # Ku: The gain at which the system oscillates
        self.critical_period = None  # Pu: The period of oscillation
        
        # Oscillation data
        self.oscillation_data = []  # Stores (time, temperature) to detect oscillations
        self.tuning_complete = False  # Flag to indicate the tuning is complete

        # Parameters for self-adjusting the critical gain
        self.max_critical_gain = 200  # Maximum allowable critical gain
        self.min_critical_gain = 50   # Minimum allowable critical gain
        self.gain_increase_rate = 1.1  # Rate to increase critical gain (when oscillations are too slow)
        self.gain_decrease_rate = 0.9  # Rate to decrease critical gain (when oscillations are too fast)
        self.oscillation_threshold = 0.05  # Minimum temperature change to detect meaningful oscillations

    def force_oscillation(self, step_size=100):
        """
        Forces the heater to a high duty cycle to induce oscillations in the system.

        Args:
            step_size (int): The duty cycle percentage to force the heater to, inducing system oscillations.
        """
        Logger.log_info(f"Forcing oscillations with step input of {step_size}%.")
        self.heater_controller.set_duty_cycle(step_size)

    def detect_oscillations(self, temperature_reading):
        """
        Detects oscillations in the system's temperature response and measures the period between them.

        Args:
            temperature_reading (float): The current temperature reading from the system.

        Returns:
            (bool, float): A tuple indicating whether an oscillation was detected and the period of oscillation.
        """
        try:
            # Store the first two temperature data points to detect oscillations
            current_time = time.monotonic()
            if len(self.oscillation_data) < 2:
                self.oscillation_data.append((current_time, temperature_reading))
                return False, None  # Not enough data to detect oscillations yet

            # Retrieve the last recorded time and temperature
            prev_time, prev_temp = self.oscillation_data[-1]

            # Detect a temperature peak (oscillation) by checking if the temperature is decreasing
            if prev_temp > temperature_reading and abs(prev_temp - temperature_reading) > self.oscillation_threshold:
                period = current_time - prev_time  # Calculate the time period between oscillations
                Logger.log_info(f"Oscillation detected with period: {period} seconds.")
                self.oscillation_data.append((current_time, temperature_reading))  # Log the new oscillation
                return True, period

        except Exception as e:
            Logger.log_traceback_error(e)  # Log any errors during oscillation detection

        return False, None  # No oscillation detected or an error occurred

    def adjust_critical_gain(self, oscillation_detected):
        """
        Adjusts the critical gain dynamically based on the presence or absence of oscillations.
        
        Args:
            oscillation_detected (bool): Whether oscillations were detected.
        """
        if oscillation_detected:
            # Oscillations detected: Decrease the critical gain
            self.critical_gain *= self.gain_decrease_rate
            Logger.log_info(f"Decreasing critical gain to {self.critical_gain:.2f}.")
        else:
            # No oscillations detected: Increase the critical gain to make the system more responsive
            self.critical_gain *= self.gain_increase_rate
            Logger.log_info(f"Increasing critical gain to {self.critical_gain:.2f}.")

        # Ensure the critical gain stays within defined limits
        self.critical_gain = min(max(self.critical_gain, self.min_critical_gain), self.max_critical_gain)

    def calculate_pid_parameters(self):
        """
        Calculates the PID parameters (Kp, Ki, Kd) using the Ziegler-Nichols method.
        
        Returns:
            (float, float, float): The calculated values for Kp, Ki, and Kd.
        """
        try:
            Logger.log_info("Calculating PID parameters using Ziegler-Nichols tuning.")
            if self.critical_gain and self.critical_period:
                self.Kp = 0.6 * self.critical_gain  # Ziegler-Nichols proportional gain
                self.Ki = 2 * self.Kp / self.critical_period  # Integral gain based on critical period
                self.Kd = self.Kp * self.critical_period / 8  # Derivative gain based on critical period
                Logger.log_info(f"Auto-tuned PID parameters: Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd}")
                return self.Kp, self.Ki, self.Kd
        except Exception as e:
            Logger.log_traceback_error(e)

        return None, None, None  # Return None if PID parameters couldn't be calculated

    def auto_tune(self, setpoint):
        """
        Performs the auto-tuning process to calculate the optimal PID values.

        The system is driven into oscillations, and the critical gain and period are used to
        calculate optimal PID values. The process continues until tuning is complete.

        Args:
            setpoint (float): The desired setpoint for the system.
        
        Returns:
            (float, float, float): The auto-tuned Kp, Ki, and Kd values for the PID controller.
        """
        Logger.log_info("Starting PID auto-tuning process.")
        self.pid_controller.setpoint = setpoint  # Set the desired temperature setpoint
        self.force_oscillation(step_size=100)  # Force oscillations to detect critical points

        # Continuously monitor system response until tuning is complete
        while not self.tuning_complete:
            try:
                # Get the current temperature from the heater controller
                temperature = self.heater_controller.get_temperature()

                # Detect oscillations and measure the critical period
                oscillation_detected, period = self.detect_oscillations(temperature)

                # Adjust the critical gain based on the presence of oscillations
                self.adjust_critical_gain(oscillation_detected)

                # If oscillations are detected, calculate the critical period and complete tuning
                if oscillation_detected:
                    self.critical_period = period
                    self.tuning_complete = True  # Mark tuning as complete

            except Exception as e:
                Logger.log_traceback_error(e)

        # Calculate and return the final PID parameters
        return self.calculate_pid_parameters()