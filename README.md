# Bioreactor Control System

This project is designed to manage a bioreactor system using a **Raspberry Pi Pico** (running CircuitPython) and a **Raspberry Pi 400** (running Raspbian OS). The Raspberry Pi Pico handles sensor data collection from various environmental sensors, while the Raspberry Pi 400 communicates with the Pico, sending commands, logging data, and monitoring the system.

## Features

- **CO2 Monitoring**: Tracks CO2 levels using the SCD30 CO2 sensor.
- **Temperature Monitoring**: Tracks temperature using the DS18B20 sensor and the SCD30 temperature sensor.
- **Pressure Monitoring**: Measures atmospheric pressure using the BMP280 sensor.
- **Time Management**: The DS3231 RTC module provides real-time clock functionality and synchronizes time with the Raspberry Pi 400.
- **Data Logging**: Sensor data is logged to an SD card on the Raspberry Pi Pico.
- **Command Handling**: The Raspberry Pi 400 sends commands to the Pico for operations like feeding, recalibration, setting altitude, adjusting CO2 measurement intervals, etc.
- **Deep Sleep & Wake**: The Raspberry Pi Pico can enter deep sleep mode for power saving and be woken up by the Raspberry Pi 400 using GPIO.
- **CO2 Alerts**: Sends Telegram alerts when CO2 levels drop below a set threshold for 3 consecutive readings.

## Hardware Requirements

- **Raspberry Pi Pico** running **CircuitPython**
- **Raspberry Pi 400** running **Raspbian OS**
- **SCD30 CO2 Sensor**
- **BMP280 Pressure Sensor**
- **DS3231 RTC Module**
- **DS18B20 Temperature Sensor** (with OneWire adapter)
- **SD Card Module** (for logging data on the Pico)
- **GPIO connections** for waking the Pico from deep sleep

## Software Requirements

### Raspberry Pi Pico (CircuitPython)

- **CircuitPython Libraries**:
  - `adafruit_scd30`
  - `adafruit_bmp280`
  - `adafruit_ds3231`
  - `adafruit_sdcard`
  - `adafruit_onewire`
  - `adafruit_ds18x20`

### Raspberry Pi 400 (Raspbian OS)

- **Python Libraries** (install via `pip3`): pyserial, requests, cryptography, RPi.GPIO

## System Architecture

- The **Raspberry Pi Pico** handles the sensor data collection and logs the data to an SD card. It communicates with the Raspberry Pi 400 over a serial connection.
- The **Raspberry Pi 400** sends commands to the Pico, such as requesting data, adjusting sensor settings, or syncing the RTC. It also monitors CO2 levels and sends a Telegram alert when thresholds are breached.

## Setup Instructions

### 1. Install CircuitPython on Raspberry Pi Pico

1. Download the latest version of **CircuitPython** for the Raspberry Pi Pico from circuitpython.org.
2. Flash CircuitPython to the Pico by copying the `.uf2` file to the Pico's USB drive.

### 2. Install CircuitPython Libraries on Pico

Download the CircuitPython library bundle from circuitpython.org/libraries and copy the following `.mpy` files to the `lib` folder on the Pico:
- `adafruit_scd30.mpy`
- `adafruit_bmp280.mpy`
- `adafruit_ds3231.mpy`
- `adafruit_sdcard.mpy`
- `adafruit_onewire.mpy`
- `adafruit_ds18x20.mpy`

### 3. Hardware Connections

- **Raspberry Pi Pico**:
  - **SCD30 CO2 Sensor**: Connect to I2C pins on the Pico.
  - **BMP280 Pressure Sensor**: Connect to I2C pins on the Pico.
  - **DS18B20 Temperature Sensor**: Connect the OneWire data pin to a GPIO pin (e.g., GP18) and power it with the 3.3V pin on the Pico.
  - **DS3231 RTC Module**: Connect to I2C pins on the Pico.
  - **SD Card Module**: Connect via SPI (e.g., GP10, GP11, GP12, GP13).
  - **GPIO for Waking**: Use a GPIO pin (e.g., GP15) to wake the Pico from deep sleep.

- **Raspberry Pi 400**:
  - **Serial Communication**: Connect the Raspberry Pi Pico to the Raspberry Pi 400 via USB for serial communication.
  - **GPIO Connection**: Connect the Raspberry Pi 400's GPIO pin (e.g., GPIO 17) to the Pico's wake pin (e.g., GP15).

### 4. Setting Up the Raspberry Pi 400

#### Install Required Python Libraries

On your Raspberry Pi 400, you need to install the following libraries using `pip3`: pyserial, requests, cryptography, RPi.GPIO

#### Create Secure Credentials for Telegram Alerts

1. **Telegram Bot Setup**:
   - Set up a Telegram bot and get the bot's token.
   - Get your chat ID by messaging the bot and retrieving the chat ID from Telegram's API.

2. **Encrypt Credentials**:
   - Store the bot token and chat ID securely. Use the cryptography library's `Fernet` encryption to encrypt and store these credentials.
   - Save the encrypted credentials and key in the following paths:
     - `~/.config/bioreactor_secure_config/encrypted_data.txt` (for the encrypted token and chat ID)
     - `~/.config/bioreactor_secure_config/secret_key.key` (for the encryption key)

### 5. Running the System

1. **Start the Raspberry Pi Pico**:
   - The Pico will begin collecting sensor data and log it to the SD card. It will also listen for commands sent via serial from the Raspberry Pi 400.

2. **Run the `pi_control_system.py` script on the Raspberry Pi 400**:
   - On your Raspberry Pi 400, execute the `pi_control_system.py` script by typing: python3 pi_control_system.py
   - This will start the communication with the Pico and allow you to send commands, request sensor data, and monitor CO2 levels.

3. **Interacting with the Command Prompt**:
   - The system features a non-blocking command prompt where you can enter the following commands:
     - `/d` - Request sensor data from the Pico.
     - `/t` - Request RTC time from the Pico.
     - `/st` - Sync the Raspberry Pi 400's system time with the Pico's RTC.
     - `/f` - Feed command. Enter the feed amount in grams.
     - `/cal` - Calibrate CO2 sensor. Enter the CO2 calibration value.
     - `/th` - Set CO2 warning threshold level
     - `/alt` - Set altitude for the SCD30 sensor.
     - `/p` - Set sea level pressure reference for the BMP280 sensor.
     - `/int` - Set CO2 measurement interval for the SCD30 sensor.
     - `/cyc` - Set sensor data query cycle duration (in minutes).
     - `/s` - Shutdown the Pico into deep sleep.
     - `/w` - Wake the Pico from deep sleep.
     - `/r` - Reset the Pico.
     - `/e` - Exit the control loop.

### 6. Telegram Alerts

The Raspberry Pi 400 monitors the CO2 levels from the Pico. If the CO2 level drops below the configured threshold for 3 consecutive readings, it will send a **Telegram alert** to notify the user.

### 7. Example Workflow

1. **Start the Raspberry Pi Pico**:
   - The Pico begins collecting data from the SCD30, DS18B20, and BMP280 sensors, logging it to the SD card and waiting for commands from the Raspberry Pi 400.

2. **Run the Control System on the Raspberry Pi 400**:
   - Start the `pi_control_system.py` script on the Raspberry Pi 400. Use the interactive command prompt to manage the system:
     - Request sensor data with `/d`.
     - Sync the RTC time using `/st`.
     - Calibrate the CO2 sensor using `/cal <value>`.
     - Adjust sensor settings such as altitude, pressure, and CO2 intervals.

3. **Receive Alerts**:
   - If CO2 levels drop below the threshold for 3 consecutive readings, the Raspberry Pi 400 will send a Telegram alert.

## Troubleshooting

- **Pico not responding to commands**:
  - Ensure the correct serial port (`/dev/ttyACM0` or similar) is being used on the Raspberry Pi 400.
  - Check the connection between the Raspberry Pi 400 and the Pico via USB.

- **SD card not mounting on the Pico**:
  - Ensure the SD card module is connected correctly to the Pico's SPI pins.
  - Format the SD card as FAT32 and ensure it is properly ejected between tests.

- **Telegram alerts not working**:
  - Verify that the Telegram bot token and chat ID are correctly encrypted and stored in the appropriate paths.
  - Ensure the Raspberry Pi 400 has an active internet connection.

## License

This project is open-source and available under the MIT License.
