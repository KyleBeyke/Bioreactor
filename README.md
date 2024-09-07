# Bioreactor Project

This project automates the control of a bioreactor using a Raspberry Pi 4 and a Pico microcontroller. It monitors environmental conditions using sensors, sends alerts through Telegram, logs data for future analysis, and automates various functions.

## Features

- **Sensor Monitoring:** CO2, temperature, humidity, pressure, and altitude readings.
- **Telegram Alerts:** Notifications when sensor thresholds are crossed.
- **Data Logging:** Logs sensor data to an SD card (Pico) and events on the Raspberry Pi.
- **Secure:** Sensitive data like bot token and chat ID are encrypted.
- **Automated:** Automatically starts control system after a reboot.

## Hardware Requirements

1. **Raspberry Pi 4** (with Raspbian OS)
2. **Raspberry Pi Pico** (with CircuitPython)
3. **SCD30 CO2 Sensor**
4. **BMP280 Pressure/Altitude Sensor**
5. **DS3231 RTC Module**
6. **MicroSD Card (for Pico logging)**
7. **Jumper Wires** for connections between components

## Wiring Setup

- **SCD30** (CO2 Sensor): I2C (SDA to `GP20`, SCL to `GP21`).
- **BMP280** (Pressure/Altitude Sensor): I2C (shares SDA and SCL with SCD30).
- **DS3231** (RTC Module): I2C (shares SDA and SCL with SCD30 and BMP280).
- **SD Card**: SPI (`GP10` MOSI, `GP11` MISO, `GP12` SCLK, `GP13` CS).
- **GPIO Wake-Up Pin**: GPIO17 (Pi) to GP15 (Pico) to wake the Pico from deep sleep.

## Software Requirements

### Install Python Libraries

Run the following command to install all required Python libraries:
pip install -r requirements.txt

### Included Libraries

- `python.dotenv`
- `serial`
- `RPi.GPIO`
- `cryptography`
- `requests`
- `adafruit-circuitpython-scd30`
- `adafruit-circuitpython-bmp280`
- `adafruit-circuitpython-ds3231`
- `adafruit-circuitpython-sdcard`

## Project Setup

### Step 1: Clone the Repository
git clone https://github.com/KyleBeyke/Bioreactor.git
cd Bioreactor

### Step 2: Run the Setup Script
Run the setup script to configure the environment, set up Telegram credentials, and install dependencies:
chmod +x setup_bioreactor.sh
./setup_bioreactor.sh

### Step 3: Virtual Environment Setup
Create and activate a virtual environment for isolating dependencies:
python3 -m venv venv
source venv/bin/activate

### Step 4: Configure Telegram Notifications

The setup script will ask for your Telegram bot token and chat ID. These credentials will be encrypted and securely stored in `~/.config/bioreactor_secure_config`. Follow these steps to set up a Telegram bot and obtain the credentials:

1. Open Telegram and search for "BotFather."
2. Start a chat with BotFather and use `/newbot` to create a new bot.
3. Follow the prompts to name your bot and receive the bot token.
4. Use `@get_id_bot` to obtain your chat ID.

## Accessing the Program After Reboot

After running the setup script, the system will automatically start the control system when the Raspberry Pi is rebooted. You can access the program by navigating to the project directory and running:

source venv/bin/activate
python3 pi_control_system.py

The Raspberry Pi Pico will automatically begin running `pico_sensor_system.py` when it starts, ensuring that the sensors and data logging continue without manual intervention.

## Project Components

### pi_control_system.py
Manages the bioreactor by handling commands, sending Telegram alerts, and logging events. It communicates with the Raspberry Pi Pico via serial and triggers actions such as feeding, recalibration, shutdown, and restart.

### pico_sensor_system.py
Runs on the Pico, gathering sensor data (CO2, temperature, humidity, pressure, altitude) and responding to commands from the Raspberry Pi. It logs data to an SD card and enters deep sleep when instructed.

### setup_bioreactor_env.py
Handles environment setup, including encryption of sensitive data, setting environment variables, and running a test script to ensure the Telegram bot connection is working.

### test_telegram_connection.py
Tests the Telegram bot by sending a test message to verify the connection and logs the result.

## Data Logging and Alerts

### Data Logging
- Sensor data is logged to a CSV file on the Pico's SD card every 15 minutes.
- All commands and events are logged on the Raspberry Pi for debugging and monitoring.

### Telegram Alerts
- Alerts are sent when CO2 levels exceed a preset threshold or return below it after exceeding the threshold.

## Troubleshooting

### Common Issues
1. **No response from the Pico:**
   - Check the serial connection between the Raspberry Pi and the Pico.
   - Ensure that the Pico has power and is not in deep sleep mode.
  
2. **Telegram messages not sending:**
   - Verify that the bot token and chat ID are correctly set.
   - Ensure the Raspberry Pi has internet access to send the Telegram messages.

3. **Sensor data not logging:**
   - Check that the SD card is properly mounted on the Pico.
   - Verify that the sensors are properly connected.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.