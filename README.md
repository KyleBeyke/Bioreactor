# Bioreactor System with Raspberry Pi Pico and Raspberry Pi 4

This project integrates the Raspberry Pi Pico and Raspberry Pi 4 to control and monitor bioreactor conditions, such as CO2 levels, temperature, humidity, and pressure. The system uses a variety of sensors, logs data to an SD card, and sends notifications via Telegram. It includes remote control functionality and deep sleep capabilities for power conservation.

## Features

- Logs **CO2**, **temperature**, **humidity**, **pressure**, and **altitude** data every 15 minutes.
- Allows the Raspberry Pi 4 to send remote commands to the Pico:
  - **CO2 calibration**
  - **Feed logging**
  - **Shutdown** and **restart** (deep sleep)
  - **Time synchronization** (every 10 minutes)
- Sends **Telegram notifications** when CO2 exceeds a set threshold or falls back below it.
- Logs all events (sensor readings, commands) to a CSV file on the Pico's SD card.
- Modularized scripts for **environment setup**, **sensor control**, and **testing**.

## Components Required

### Hardware

1. **Raspberry Pi Pico** (with CircuitPython installed)
2. **Raspberry Pi 4**
3. **SCD30 CO2 Sensor**
4. **BMP280 Pressure and Altitude Sensor**
5. **DS3231 RTC Module**
6. **MicroSD Card + Adapter** (for data logging)
7. **Jumper wires** (for wiring connections)
8. **GPIO connections** between Raspberry Pi and Pico for deep sleep wake-up

### Software

- **Python 3** on Raspberry Pi 4
- **CircuitPython** on Raspberry Pi Pico

## Wiring Setup

### Raspberry Pi Pico Pin Assignments

- **I2C SDA (SCD30, BMP280, RTC)**: `GP20`
- **I2C SCL (SCD30, BMP280, RTC)**: `GP21`
- **SPI MOSI (SD Card)**: `GP10`
- **SPI MISO (SD Card)**: `GP11`
- **SPI SCLK (SD Card)**: `GP12`
- **SPI CS (SD Card)**: `GP13`
- **GPIO Wake-Up Pin**: `GP15` (connected to GPIO17 on Raspberry Pi)

### GPIO Pin on Raspberry Pi 4

- **GPIO17**: Connected to Pico’s `GP15` for wake-up control.

## Installation

### 1. Set Up CircuitPython on Raspberry Pi Pico

1. Download and install CircuitPython from [Adafruit](https://circuitpython.org/board/raspberry_pi_pico/).
2. Copy the required libraries (`adafruit_scd30`, `adafruit_bmp280`, `adafruit_ds3231`, `sdcardio`) to the `lib` folder on the Pico.

### 2. Set Up the Raspberry Pi 4 Environment

1. Ensure Python 3 is installed on the Raspberry Pi 4:
   
   `sudo apt-get install python3`

2. Clone the repository:
   
   `git clone https://github.com/KyleBeyke/Bioreactor.git`

3. Install the required Python dependencies:
   
   `pip install -r requirements.txt`

4. Run the environment setup script to configure environment variables:
   
   `python3 setup_bioreactor_env.py`

### 3. Test the Telegram Connection

Run the test script to ensure the Telegram connection is functioning properly:

`python3 test_telegram_connection.py`

## Usage

### 1. Starting the Raspberry Pi Control System

Run the following command on your Raspberry Pi 4 to start the control system:

`python3 pi_control_system.py`

### 2. Available Commands (via Console)

- **`f` (feed)**: Logs a feed operation.
  - Example: Enter `f` and provide the feed amount in grams.
  
- **`c` (calibrate)**: Calibrates the CO2 sensor.
  - Example: Enter `c` and provide the CO2 calibration value.

- **`s` (shutdown)**: Puts the Pico into deep sleep.
  
- **`r` (restart)**: Wakes the Pico from deep sleep by toggling the GPIO pin.

- **`t` (threshold)**: Set a new CO2 threshold value for notifications.
  - Example: Enter `t` and provide the new CO2 threshold in ppm.

- **`e` (exit)**: Exits the control system.

## Data Logging

### Raspberry Pi Command Log

- Commands issued to the Pico are logged in a CSV file called `commands_log.csv` on the Raspberry Pi.

### Pico Data Logging

- Sensor data and events (feed, recalibration) are logged to a CSV file on the Pico’s SD card. The CSV includes the following fields:
  - `timestamp`, `CO2`, `temperature`, `humidity`, `pressure`, `altitude`, `feed_amount`, and `recalibration`.

## Troubleshooting

1. **Telegram messages not sending**:
   - Verify that the bot token and chat ID are correct.
   - Ensure the Raspberry Pi has internet access.

2. **No sensor data**:
   - Check the wiring of the sensors.
   - Ensure that the required CircuitPython libraries are installed on the Pico.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.