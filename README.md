# Raspberry Pi Pico and Raspberry Pi 4 Bioreactor Control System

This project is designed to control a bioreactor using a **Raspberry Pi 4** connected to a **Raspberry Pi Pico**. It monitors CO2 levels, temperature, humidity, pressure, and altitude using connected sensors and logs the data to an SD card. The system also allows remote control of the Pico from the Raspberry Pi and can send alerts via Telegram when CO2 levels drop below a set threshold.

## Features

- Logs **CO2**, **temperature**, **humidity**, **pressure**, and **altitude** every 15 minutes.
- Allows the Raspberry Pi to send **remote commands** to the Pico, such as:
  - **Time synchronization** (automatically every 10 minutes).
  - **CO2 calibration**.
  - **Logging feed operations**.
  - **Shutdown** the Pico (enters deep sleep).
  - **Restart** the Pico from deep sleep via GPIO.
- Sends **Telegram alerts** when CO2 levels fall below a set threshold.
- Logs data to a CSV file on the Pico’s SD card and tracks control events on the Raspberry Pi.

---

## Components Required

### Hardware

1. **Raspberry Pi Pico** (with CircuitPython installed).
2. **Raspberry Pi 4**.
3. **SCD30 CO2 Sensor**.
4. **BMP280 Pressure and Altitude Sensor**.
5. **DS3231 RTC Module**.
6. **MicroSD Card and Adapter** (for the Pico).
7. **Jumper wires** for connections.
8. **GPIO connection** between Raspberry Pi and Pico for deep sleep wake-up (e.g., GPIO17 on Pi and GP15 on Pico).

### Libraries

Install the following CircuitPython libraries on the Pico:

- `adafruit_scd30.mpy`
- `adafruit_bmp280.mpy`
- `adafruit_ds3231.mpy`
- `sdcardio.mpy`
- `digitalio.mpy`
- `busio.mpy`
- `alarm.mpy`

You can download these from the [Adafruit CircuitPython Library Bundle](https://circuitpython.org/libraries).

Additionally, install the following Python libraries on the Raspberry Pi:

- `cryptography`
- `requests`
- `RPi.GPIO`

You can install these using pip:

pip install cryptography requests RPi.GPIO

---

## Setting Up the Encryption for Telegram Bot Token and Chat ID

This project uses **Fernet encryption** to securely store your **Telegram bot token** and **chat ID**.

1. Create an encryption script (`encrypt_token.py`) to encrypt your bot token and chat ID.
2. Run the script to generate two files:
   - `encrypted_data.txt`: This file will contain the encrypted bot token and chat ID.
   - `secret_key.key`: This file contains the encryption key, which must be stored securely.

You can run the script using the following command:

python3 encrypt_token.py

Ensure that the `encrypted_data.txt` and `secret_key.key` files are in the same directory as the control script on the Raspberry Pi.

---

## Running the System

### 1. Start the Raspberry Pi Control System

To start the system, execute the following command on the Raspberry Pi:

python3 pi_control_system.py

### 2. Using the Raspberry Pi Console

Once the control system is running, the following commands are available via the Raspberry Pi terminal:

- **`f` (feed)**: Logs a feed operation on the Pico.
  - Example: Enter `f` and provide the feed amount in grams.
  
- **`c` (calibrate)**: Calibrates the CO2 sensor on the Pico.
  - Example: Enter `c` and provide the CO2 value for calibration.

- **`s` (shutdown)**: Puts the Pico into deep sleep.

- **`r` (restart)**: Wakes the Pico from deep sleep by toggling the GPIO pin.

- **`e` (exit)**: Exits the Raspberry Pi control system.

---

## Logging

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

## GPIO Wake-Up Pin

The Pico enters **deep sleep** after receiving the `SHUTDOWN` command. To wake the Pico:

1. The Raspberry Pi sends the **restart command** (`r`).
2. The Raspberry Pi toggles **GPIO17**, connected to **GP15** on the Pico, to wake it up from deep sleep.

---

## Troubleshooting

### Common Issues

1. **No response from Pico**:
   - Ensure the GPIO connection between the Raspberry Pi and Pico is set up correctly.
   - Check the serial connection (`/dev/ttyACM0`) for the correct port on the Raspberry Pi.

2. **Time not syncing**:
   - Ensure both the Raspberry Pi and Pico are powered on and that the time sync commands are being sent.

3. **Data not logging**:
   - Verify that the SD card is correctly connected and mounted on the Pico.

---

## Additional Notes

- The Pico logs data to the SD card every 15 minutes, even when no commands are being sent.
- Ensure you have the correct libraries installed on the Pico for the sensors and RTC to function properly.
- Telegram alerts are sent if the CO2 level falls below the threshold (120% of the calibration value) after exceeding it.

---

## Summary

This system provides a secure and reliable setup for monitoring and controlling a bioreactor using a Raspberry Pi and Pico. It integrates Telegram notifications, data logging to an SD card, and remote control from the Raspberry Pi to the Pico with deep sleep functionality.
```