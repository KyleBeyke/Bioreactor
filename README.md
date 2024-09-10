# Bioreactor Project
# Raspberry Pi Bioreactor Control System

This project controls a **bioreactor** using a **Raspberry Pi** and a **Raspberry Pi Pico**. The Pi and the Pico communicate via serial, allowing the Pi to send commands and receive sensor data from the Pico, which manages the connected environmental sensors and real-time clock (RTC). The system allows for sensor calibration, feeding control, and time synchronization, among other features.

## Features

- **CO2 Monitoring**: CO2 levels are monitored using the SCD30 sensor.
- **Pressure Monitoring**: Atmospheric pressure is measured using the BMP280 sensor.
- **Time Synchronization**: The Pico's RTC (DS3231) can be synchronized with the Pi's system time.
- **Command Execution**: The Pi sends commands such as feeding, calibration, altitude adjustments, and querying sensor data to the Pico.
- **Deep Sleep and Wake Control**: The Pico can enter deep sleep mode to conserve energy and be woken up by the Pi.
- **Telegram Alerts**: The system can send alerts via Telegram when specific conditions are met (e.g., high CO2 levels).
- **Non-Blocking Command Prompt**: The Pi script features a non-blocking command prompt, allowing continuous monitoring of serial data while accepting user commands.

## Hardware Components

- **Raspberry Pi** (tested on Raspberry Pi 400)
- **Raspberry Pi Pico** running CircuitPython
- **SCD30 CO2 Sensor** (connected to the Pico via I2C)
- **BMP280 Pressure Sensor** (connected to the Pico via I2C)
- **DS3231 RTC Module** (connected to the Pico via I2C)
- **SD Card Module** (for logging data on the Pico)
- **GPIO connections** for waking the Pico from deep sleep

## Software Components

- **CircuitPython** on the Pico
  - Used for managing sensors, RTC, and command execution.
- **Python** on the Raspberry Pi (Raspbian OS)
  - Handles communication with the Pico, command input, logging, and Telegram alerts.

## Communication Flow

- The Pi sends commands to the Pico via a serial connection (`/dev/ttyACM0`).
- The Pico processes the commands, interacts with its connected sensors, and responds back with data or status updates.
- Commands include actions like feeding control, CO2 calibration, altitude setting, and data requests.
- Time synchronization is done by sending the Pi's system time to the Pico using the `SYNC_TIME` command.

## Installation

### Raspberry Pi Setup

1. **Install Python Libraries**:
   - Install the necessary Python libraries on your Pi:
     ```bash
     sudo apt update
     sudo apt install python3 python3-pip
     pip3 install pyserial requests cryptography RPi.GPIO
     ```

2. **Configure Serial Communication**:
   - Enable serial communication on the Pi by running:
     ```bash
     sudo raspi-config
     ```
   - Navigate to **Interface Options** > **Serial**. Disable the shell over serial, but enable serial communication.

3. **Configure Telegram Alerts** (Optional):
   - Store your Telegram bot token and chat ID as encrypted credentials under `~/.config/bioreactor_secure_config/`.

### Raspberry Pi Pico Setup

1. **Install CircuitPython**:
   - Flash your Raspberry Pi Pico with the latest version of CircuitPython.

2. **Install CircuitPython Libraries**:
   - Copy the necessary libraries to the Pico's `lib` folder:
     - `adafruit_scd30`
     - `adafruit_bmp280`
     - `adafruit_ds3231`
     - `adafruit_sdcard`
     - `digitalio`, `busio`, `storage`, `supervisor`, and `alarm`

3. **Upload the `pico_sensor_system.py`** script to the Pico.
   - This script handles sensor readings, logging to the SD card, and executing commands sent from the Raspberry Pi.

## Usage

### Running the System

1. **Start the Pi Control Script**:
   - On the Raspberry Pi, run the `pi_control_system.py` script:
     ```bash
     python3 pi_control_system.py
     ```

2. **Interacting with the System**:
   - The script will start a non-blocking command prompt where you can enter commands.
   - Available commands:
     - `/d` - Request sensor data from the Pico.
     - `/f` - Feed command. Enter the feed amount in grams (e.g., `/f` followed by the amount in grams).
     - `/cal` - Calibrate CO2. Enter the CO2 calibration value in ppm.
     - `/alt` - Set altitude for SCD30.
     - `/p` - Set sea level pressure reference for BMP280.
     - `/int` - Set CO2 measurement interval for the SCD30 sensor.
     - `/cyc` - Set sensor data query cycle duration in minutes.
     - `/s` - Shutdown the Pico into deep sleep.
     - `/w` - Wake the Pico from deep sleep.
     - `/r` - Reset the Pico.
     - `/time` - Sync the Pi’s system time with the Pico’s RTC.

3. **Telegram Alerts** (Optional):
   - If set up, you will receive alerts via Telegram when certain conditions (e.g., high CO2) are met.

### Example Command Workflow

- **Request Data**: Type `/d` in the prompt to request the latest sensor data from the Pico.
- **Sync Time**: Type `/time` to sync the Pi’s system time to the Pico’s RTC.
- **Calibrate CO2 Sensor**: Type `/cal` and enter the CO2 calibration value (in ppm) to recalibrate the SCD30 sensor.

### Logs and Data

- Commands sent to the Pico are logged in `commands_log.csv` and `bioreactor_log.log` on the Raspberry Pi.
- Sensor data is logged on the SD card connected to the Pico in a CSV format.

## System Architecture

- **Raspberry Pi**: Manages the bioreactor control logic, provides user interaction via a non-blocking command prompt, and logs all data and commands.
- **Raspberry Pi Pico**: Handles real-time sensor data collection, RTC synchronization, and power management (deep sleep/wake functions).
- **Serial Communication**: The Pi and Pico communicate via serial using `/dev/ttyACM0`, sending and receiving commands and sensor data.

## License

This project is open-source and available under the MIT License.