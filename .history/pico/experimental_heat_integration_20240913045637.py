import time
import board
import busio
import adafruit_scd30
import adafruit_bmp280
import adafruit_ds3231
import digitalio
import storage
import adafruit_sdcard
import alarm
import supervisor
import microcontroller
import traceback
from adafruit_onewire.bus import OneWireBus  # For OneWire communication
import adafruit_ds18x20  # For DS18B20 temperature sensor
import asyncio
import countio

# Global default sensor data query cycle
sensor_query_cycle_mins = 3  # Time interval for querying sensor data (in minutes)
cycle = sensor_query_cycle_mins * 60  # Convert minutes to seconds

# Heater-related defaults
default_temperature = 43  # Default target temperature in °C
default_duty_cycle = 30  # Default heater duty cycle in %
heater_control_pin = board.GP15  # Pin connected to the heater's control signal

# Heater class for controlling the heating element
class AC_Heater:
    def __init__(self, zero_cross_pin, control_pin, initial_debounce_time=0.005):
        self.control_pin = digitalio.DigitalInOut(control_pin)
        self.control_pin.direction = digitalio.Direction.OUTPUT
        self.control_pin.value = False

        # Zero-crossing detector
        self.zero_cross = countio.Counter(zero_cross_pin, edge=countio.Edge.RISE)
        self.ac_half_cycle_time = 0.01  # Default for 50Hz (10ms half-cycle)
        self.duty_cycle = default_duty_cycle  # Duty cycle in percentage (0-100)
        self.state = False  # Heater on/off state
        self.debounce_time = initial_debounce_time  # Debounce time
        self.last_zero_cross_time = 0

    async def zero_cross_task(self):
        """Task for handling zero crossing and heater control asynchronously."""
        previous_count = self.zero_cross.count
        while True:
            if self.zero_cross.count > previous_count:
                current_time = time.monotonic()

                if self.last_zero_cross_time != 0:
                    cycle_time = current_time - self.last_zero_cross_time
                    self.ac_half_cycle_time = cycle_time / 2
                    self.debounce_time = 0.1 * self.ac_half_cycle_time

                if current_time - self.last_zero_cross_time >= self.debounce_time:
                    previous_count = self.zero_cross.count
                    self.last_zero_cross_time = current_time

                    if self.state:
                        phase_delay = (1 - self.duty_cycle / 100) * self.ac_half_cycle_time
                        await asyncio.sleep(phase_delay)
                        self.control_pin.value = True
                        await asyncio.sleep(0.0001)  # Brief pulse (100 µs)
                        self.control_pin.value = False
            await asyncio.sleep(0)

    def set_duty_cycle(self, duty_cycle):
        if 0 <= duty_cycle <= 100:
            self.duty_cycle = duty_cycle

    def turn_on(self, duty_cycle=default_duty_cycle):
        self.set_duty_cycle(duty_cycle)
        self.state = True

    def turn_off(self):
        self.state = False

# Function to reset the Pico
def reset_pico():
    """Resets the Pico after a 30-second wait to allow safe shutdown of tasks."""
    print("Resetting the Pico in 30 seconds...")
    time.sleep(30)
    microcontroller.reset()

# I2C initialization with retries
for attempt in range(3):
    try:
        i2c = busio.I2C(board.GP21, board.GP20)
        scd30 = adafruit_scd30.SCD30(i2c)
        bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
        rtc = adafruit_ds3231.DS3231(i2c)
        print("I2C devices initialized successfully.")
        break
    except Exception as e:
        print(f"Failed to initialize I2C devices on attempt {attempt + 1}: {e}")
        if attempt == 2:
            reset_pico()

# DS18B20 temperature sensor initialization
for attempt in range(3):
    try:
        onewire_bus = OneWireBus(board.GP18)
        devices = onewire_bus.scan()
        if not devices:
            raise RuntimeError("No DS18B20 sensor found!")
        ds18b20 = adafruit_ds18x20.DS18X20(onewire_bus, devices[0])
        print(f"DS18B20 initialized successfully.")
        break
    except Exception as e:
        print(f"Failed to initialize DS18B20 on attempt {attempt + 1}: {e}")
        if attempt == 2:
            reset_pico()

# Heater Initialization
zero_cross_pin = board.GP14  # Zero-crossing detection pin
heater = AC_Heater(zero_cross_pin, heater_control_pin)

# Temperature control function (Async)
async def maintain_temperature():
    """Asynchronously controls the heater based on the target temperature."""
    target_temp = default_temperature
    heater.turn_on(default_duty_cycle)

    while True:
        current_temp = ds18b20.temperature
        if current_temp < target_temp:
            if not heater.state:
                heater.turn_on()
        elif current_temp >= target_temp:
            heater.turn_off()
        await asyncio.sleep(5)  # Sleep to avoid excessive polling

# CO2 recalibration after reaching target temperature
async def recalibrate_at_target_temp():
    """Recalibrates CO2 sensor after reaching target temperature."""
    while ds18b20.temperature < default_temperature:
        await asyncio.sleep(5)
    scd30.forced_recalibration_reference = 400  # Example recalibration value
    log_info("CO2 sensor recalibrated after reaching target temperature.")

# Handling commands for heater control
def handle_heater_commands(command):
    """Handles commands to control the heater."""
    global heater
    if command.startswith("SET_HEATER_TEMP"):
        temp = int(command.split(",")[1])
        log_info(f"Setting heater target temperature to: {temp}°C")
        maintain_temperature.target_temp = temp

    elif command.startswith("SET_HEATER_DUTY"):
        duty_cycle = int(command.split(",")[1])
        log_info(f"Setting heater duty cycle to: {duty_cycle}%")
        heater.set_duty_cycle(duty_cycle)

    elif command == "HEATER_ON":
        log_info("Turning heater ON.")
        heater.turn_on()

    elif command == "HEATER_OFF":
        log_info("Turning heater OFF.")
        heater.turn_off()

# Function to handle incoming commands (integrated heater control)
def handle_commands(command):
    """Handles commands from the Raspberry Pi."""
    try:
        log_info(f"Received command: {command}")

        if command.startswith("FEED"):
            feed_amount = command.split(",")[1]
            log_info(f"Feed command received: {feed_amount} grams")
            send_sensor_data(feed_amount, None)

        elif command.startswith("CALIBRATE"):
            recalibration_value = int(command.split(",")[1])
            scd30.forced_recalibration_reference = recalibration_value
            log_info(f"Recalibration command received: {recalibration_value} ppm")
            send_sensor_data(None, recalibration_value)

        elif command == "REQUEST_DATA":
            log_info("Data request command received.")
            send_sensor_data()

        elif command == "SHUTDOWN":
            log_info("Shutdown command received.")
            shutdown_pico()

        elif command.startswith("SYNC_TIME"):
            log_info("Time sync command received.")
            sync_rtc_time(command)

        elif command == "REQUEST_RTC_TIME":
            log_info("RTC time request command received.")
            timestamp = get_rtc_time()
            print(f"RTC time: {timestamp}")

        elif command.startswith("SET_ALTITUDE"):
            altitude = command.split(",")[1]
            log_info(f"Set altitude command received: {altitude} meters")
            set_altitude(altitude)

        elif command.startswith("SET_PRESSURE"):
            pressure = int(command.split(",")[1])
            log_info(f"Set pressure command received: {pressure} hPa")
            set_pressure_reference(pressure)

        elif command.startswith("SET_CYCLE_MINS"):
            new_cycle = int(command.split(",")[1])
            log_info(f"Set cycle command received: {new_cycle} minute(s)")
            set_cycle(new_cycle)

        elif command.startswith("SET_CO2_INTERVAL"):
            interval = command.split(",")[1]
            log_info(f"Set CO2 interval command received: {interval} second(s)")
            set_co2_interval(interval)

        elif command == "RESET_PICO":
            log_info("Reset command received.")
            reset_pico()

        elif command.startswith("SET_HEATER_TEMP") or command.startswith("SET_HEATER_DUTY") or command == "HEATER_ON" or command == "HEATER_OFF":
            handle_heater_commands(command)

        else:
            log_error("Invalid command received")

    except Exception as e:
        log_traceback_error(e)

# Function to sync RTC time with the Pi
def sync_rtc_time(sync_time_str):
    """Syncs the RTC time using the SYNC_TIME command."""
    try:
        parts = sync_time_str.split(",")[1].strip().split(" ")
        date_parts = parts[0].split("-")
        time_parts = parts[1].split(":")
        year, month, day = map(int, date_parts)
        hour, minute, second = map(int, time_parts)
        rtc.datetime = time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))
        log_info(f"RTC time synchronized to: {sync_time_str}")
    except Exception as e:
        log_traceback_error(e)

# Function to update SCD30 altitude and pressure compensation
def update_scd30_compensation():
    """Updates the SCD30 sensor compensation values based on BMP280 readings."""
    try:
        pressure = bmp280.pressure
        scd30.ambient_pressure = int(pressure)
        time.sleep(5)
        log_info(f"Compensation updated: Pressure: {pressure} hPa")
    except Exception as e:
        log_traceback_error(e)
        log_error("Failed to update SCD30 compensation values.")

# Function to shutdown Pico and enter deep sleep
def shutdown_pico():
    """Shuts down the Pico and enters deep sleep."""
    log_info("Shutting down Pico and entering deep sleep.")
    time.sleep(2)
    wake_alarm = alarm.pin.PinAlarm(pin=board.GP15, value=False, pull=True)
    alarm.exit_and_deep_sleep_until_alarms(wake_alarm)

# Send sensor data and log to SD card with retries
def send_sensor_data(feed=None, recalibration=None):
    """Sends sensor data to SD card and logs it, with retries on failure."""
    retries = 3
    while not scd30.data_available and retries > 0:
        retries -= 1
        time.sleep(5)

    if retries == 0:
        log_error("Failed to get sensor data after multiple retries")
        return

    try:
        co2 = scd30.CO2
        temperature = scd30.temperature
        humidity = scd30.relative_humidity
        ds18b20_temperature = ds18b20.temperature
        pressure = bmp280.pressure
        timestamp = get_rtc_time()
        # Log with conditionally formatting feed and recalibration values
        sensor_data = f"SENSOR DATA:{timestamp},{co2:.2f},{ds18b20_temperature:.2f},{temperature:.2f},{humidity:.2f},{pressure:.2f},{feed if feed is not None else 'N/A'},{recalibration if recalibration is not None else 'N/A'}"
        print(sensor_data)
        log_data_to_csv(timestamp, co2, ds18b20_temperature, temperature, humidity, pressure, feed, recalibration)
    except Exception as e:
        log_traceback_error(e)
        log_error("Error while sending sensor data.")

# Function to update SCD30 altitude and pressure compensation
def update_scd30_compensation():
    """Updates the SCD30 sensor compensation values based on BMP280 readings."""
    try:
        pressure = bmp280.pressure
        scd30.ambient_pressure = int(pressure)
        time.sleep(5)
        log_info(f"Compensation updated: Pressure: {pressure} hPa")
    except Exception as e:
        log_traceback_error(e)
        log_error("Failed to update SCD30 compensation values.")

# Main control loop
def control_loop():
    """Main loop that handles periodic sensor readings and command processing."""
    log_info("Starting system... warming up sensors for 15 seconds.")
    time.sleep(15)

    global cycle

    log_info("Sending initial sensor data after warm-up period.")
    try:
        update_scd30_compensation()
        send_sensor_data()
    except Exception as e:
        log_traceback_error(e)

    last_reading_time = time.monotonic()

    # Start heater control after everything else
    log_info("Starting heater control and waiting for temperature stabilization...")
    asyncio.run(heater.zero_cross_task())
    asyncio.run(maintain_temperature())
    asyncio.run(recalibrate_at_target_temp())

    while True:
        current_time = time.monotonic()

        # Send sensor data every cycle duration (default 5 minutes)
        if current_time - last_reading_time >= cycle:
            try:
                update_scd30_compensation()
                send_sensor_data()
                last_reading_time = current_time
            except Exception as e:
                log_traceback_error(e)

        # Listen for commands from the Pi
        try:
            if supervisor.runtime.serial_bytes_available:
                command = input().strip()
                handle_commands(command)

        except Exception as e:
            log_traceback_error(e)

# Main program entry point
if __name__ == "__main__":
    control_loop()
