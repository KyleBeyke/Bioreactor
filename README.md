# Bioreactor System - Raspberry Pi Pico and Raspberry Pi 4 Sensor System with Telegram Notifications

This project provides a system using a **Raspberry Pi Pico** connected to sensors for monitoring CO2 levels, temperature, humidity, and atmospheric pressure. It integrates with a **Raspberry Pi 4** to control the Pico, log data to an SD card, and send notifications via **Telegram** when necessary thresholds are crossed.

## Features

- Logs **CO2**, **temperature**, **humidity**, **pressure**, and **altitude** data every 15 minutes.
- Sends **Telegram notifications** when CO2 levels cross a defined threshold.
- Allows **remote control** of the Pico from the Raspberry Pi for calibration, feed logging, shutdown, and restart operations.
- Pico enters **deep sleep** after a shutdown command and can be woken up via a GPIO pin connected to the Raspberry Pi.
- Logs all sensor data to a CSV file on the Pico's SD card and commands on the Raspberry Pi.

---

## Components Required

### Hardware

1. **Raspberry Pi Pico** (with CircuitPython installed).
2. **Raspberry Pi 4**.
3. **SCD30 CO2 Sensor**.
4. **BMP280 Pressure and Altitude Sensor**.
5. **DS3231 RTC Module**.
6. **MicroSD Card and Adapter** (for the Pico).
7. **Jumper wires** (for connections).
8. **GPIO connection** between Raspberry Pi and Pico for deep sleep wake-up (e.g., GPIO17 on Pi and GP15 on Pico).

---

## Software Requirements

### Python Libraries for Raspberry Pi

Make sure the following libraries are installed on the Raspberry Pi:

- `requests`
- `cryptography`
- `RPi.GPIO`
- `pyserial`

You can install these using `pip` by running the following command:

sudo pip install requests cryptography RPi.GPIO pyserial

### CircuitPython Libraries for the Pico

Install the following CircuitPython libraries on the Pico:

- `adafruit_scd30.mpy`
- `adafruit_bmp280.mpy`
- `adafruit_ds3231.mpy`
- `sdcardio.mpy`
- `digitalio.mpy`
- `busio.mpy`
- `alarm.mpy`

You can download these from the [Adafruit CircuitPython Library Bundle](https://circuitpython.org/libraries).

---

## Setting Up the Hardware

### Wiring

- **SCD30**: Connect via I2C (e.g., `GP20` for SDA, `GP21` for SCL).
- **BMP280**: Connect via I2C (same as SCD30).
- **DS3231 RTC**: Connect via I2C (same as SCD30).
- **SD Card**: Connect via SPI (`GP10` for MOSI, `GP11` for MISO, `GP12` for SCLK, `GP13` for CS).
- **GPIO for Wake-Up**: 
  - Connect **GPIO17** on Raspberry Pi to **GP15** on Pico.

---

## Setting Up the Environment

### 1. Install CircuitPython on Raspberry Pi Pico

Follow the [Adafruit guide](https://learn.adafruit.com/welcome-to-circuitpython) to install CircuitPython on the Pico. After installation, copy the necessary libraries into the `lib` folder on the Pico’s **CIRCUITPY** drive.

### 2. Set up the Raspberry Pi 4

Ensure Python 3 is installed on your Raspberry Pi. Use the following command to install Python 3:

sudo apt-get install python3

### 3. Setting Up Telegram Bot and Environment Variables

To enable notifications via Telegram, follow these steps:

1. Create a Telegram bot using the [BotFather](https://core.telegram.org/bots#botfather) and note the **bot token**.
2. Start a chat with your bot and get your **chat ID**. You can get your chat ID by sending `/start` to your bot and querying the Telegram API with this URL:
   
https://api.telegram.org/bot<your-bot-token>/getUpdates

3. Run the provided **`setup_bioreactor_env.py`** script to securely encrypt your bot token and chat ID into environment variables:

python3 setup_bioreactor_env.py

This script will prompt you to enter your bot token and chat ID. The encrypted values will be stored in `~/.config/bioreactor_secure_config`.

---

## Running the System

### 1. Upload the Code to the Raspberry Pi Pico

- Copy the provided Pico code (`pico_sensor_system.py`) to the **CIRCUITPY** drive.
- Ensure that all required libraries are placed in the `lib` folder on the Pico.

### 2. Upload the Code to the Raspberry Pi 4

- Save the Raspberry Pi 4 code (`pi_control_system.py`) to your Raspberry Pi.
- Make the script executable by entering the following command:

chmod +x pi_control_system.py

- Run the script with:

python3 pi_control_system.py

---

## Raspberry Pi Console Commands

Once the control system is running, the following commands are available via the Raspberry Pi terminal:

- **`f` (feed)**: Logs a feed operation on the Pico.
  - Example: Enter `f` and then provide the feed amount in grams.
  
- **`c` (calibrate)**: Calibrates the CO2 sensor on the Pico.
  - Example: Enter `c` and then provide the CO2 value for calibration.

- **`s` (shutdown)**: Puts the Pico into deep sleep.

- **`r` (restart)**: Wakes the Pico from deep sleep by toggling the GPIO pin.

- **`t` (set CO2 threshold)**: Sets a new CO2 warning threshold.
  - Example: Enter `t` and then provide the new CO2 threshold in ppm.

- **`e` (exit)**: Exits the Raspberry Pi control system.

---

## Data Logging

### Raspberry Pi Command Log

All commands issued to the Pico are logged in a file called `commands_log.csv` on the Raspberry Pi, with timestamps.

### Pico Data Logging

The Pico logs sensor data and command-related events in a CSV file on the SD card. The CSV contains the following fields:
- **timestamp**
- **CO2** (ppm)
- **temperature** (°C)
- **humidity** (%)
- **pressure** (hPa)
- **altitude** (m)
- **feed_amount** (if feed command used)
- **recalibration** (if recalibration command used)

---

## Deep Sleep and GPIO Wake-Up

The Pico enters **deep sleep** after receiving the `SHUTDOWN` command. To wake the Pico:
- The Raspberry Pi sends the **restart command** (`r`).
- The Raspberry Pi toggles **GPIO17**, connected to **GP15** on the Pico, to wake it up from deep sleep.

---

## Troubleshooting

### Common Issues

1. **No response from Pico**:
   - Ensure that the GPIO connection between the Raspberry Pi and Pico is correctly set up.
   - Check the serial connection (`/dev/ttyACM0`) for the correct port on the Raspberry Pi.

2. **Time not syncing**:
   - Ensure that both the Raspberry Pi and Pico are powered on and that the time sync commands are being sent.

3. **Data not logging**:
   - Verify that the SD card is correctly connected and mounted on the Pico.

4. **Telegram notifications not working**:
   - Ensure your bot token and chat ID are correct and stored securely.
   - Run `test_telegram_connection.py` to verify the connection.

---

## Additional Notes

- The Pico will log data to the SD card every 15 minutes, even when no commands are being sent.
- Ensure that you have the correct libraries installed on the Pico for the sensors and RTC to function properly.
- Regularly check the SD card for logs and ensure sufficient storage is available.