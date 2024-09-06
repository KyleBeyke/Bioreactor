# Bioreactor - Raspberry Pi Pico and Raspberry Pi 4 Sensor System with Remote Control and Deep Sleep

This project enables a **Raspberry Pi Pico** connected to an **SCD30 (CO2 sensor)**, **BMP280 (pressure and altitude sensor)**, and **DS3231 RTC (real-time clock)** to log sensor data to an SD card while communicating with a **Raspberry Pi 4**. The Raspberry Pi 4 can control the Pico, sending commands like calibrating the sensors, logging feed operations, and shutting down the Pico. After shutdown, the Pico enters **deep sleep** and can be restarted remotely by the Raspberry Pi through a GPIO pin.

## Features

- Logs **CO2**, **temperature**, **humidity**, **pressure**, and **altitude** data every 15 minutes.
- Allows the Raspberry Pi to send **remote commands** to the Pico:
  - **Time synchronization** (automatically every 10 minutes).
  - **CO2 calibration**.
  - **Logging feed operations**.
  - **Shutdown** the Pico (enters deep sleep).
  - **Restart** the Pico from deep sleep via GPIO.
  - **Telegram notifications** for CO2 level alerts.
- Logs data to a CSV file on the Pico’s SD card.
- Logs commands on the Raspberry Pi for tracking control events.
- Pico enters **deep sleep** after shutdown and waits for a restart command from the Pi.

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

---

## Setting Up the Hardware

### Wiring

Here are the detailed wiring instructions for each component:

1. **SCD30 CO2 Sensor** (I2C):
   - **SDA (Data)**: Connect to `GP20` on the Pico.
   - **SCL (Clock)**: Connect to `GP21` on the Pico.
   - **Power (Vin)**: Connect to a 3.3V or 5V pin on the Pico (depending on your sensor’s requirements).
   - **Ground (GND)**: Connect to any ground (GND) pin on the Pico.

2. **BMP280 Pressure and Altitude Sensor** (I2C):
   - **SDA (Data)**: Connect to `GP20` on the Pico (shared with the SCD30 sensor).
   - **SCL (Clock)**: Connect to `GP21` on the Pico (shared with the SCD30 sensor).
   - **Power (Vin)**: Connect to a 3.3V pin on the Pico.
   - **Ground (GND)**: Connect to any ground (GND) pin on the Pico.

3. **DS3231 RTC Module** (I2C):
   - **SDA (Data)**: Connect to `GP20` on the Pico (shared with the SCD30 and BMP280 sensors).
   - **SCL (Clock)**: Connect to `GP21` on the Pico (shared with the SCD30 and BMP280 sensors).
   - **Power (VCC)**: Connect to a 3.3V pin on the Pico.
   - **Ground (GND)**: Connect to any ground (GND) pin on the Pico.

4. **MicroSD Card Adapter** (SPI):
   - **MOSI (Data)**: Connect to `GP10` on the Pico.
   - **MISO (Data)**: Connect to `GP11` on the Pico.
   - **SCLK (Clock)**: Connect to `GP12` on the Pico.
   - **CS (Chip Select)**: Connect to `GP13` on the Pico.
   - **Power (VCC)**: Connect to a 3.3V pin on the Pico.
   - **Ground (GND)**: Connect to any ground (GND) pin on the Pico.

5. **GPIO Wake-Up Connection** (Pico to Raspberry Pi):
   - **Pico Pin GP15**: Connect to **GPIO17** on the Raspberry Pi (this is used for waking up the Pico from deep sleep).

---

## Installing the Software

### 1. Install CircuitPython on Raspberry Pi Pico

Follow the Adafruit guide to install CircuitPython on the Pico. After installation, copy the necessary libraries into the `lib` folder on the Pico’s **CIRCUITPY** drive.

### 2. Set up the Raspberry Pi 4

Ensure Python 3 is installed on your Raspberry Pi. Use the following command to install Python 3:

sudo apt-get install python3

### 3. Upload the Code to the Raspberry Pi Pico

- Copy the provided Pico code (`pico_sensor_system.py`) to the **CIRCUITPY** drive.
- Ensure that all required libraries are placed in the `lib` folder on the Pico.

### 4. Upload the Code to the Raspberry Pi 4

- Save the Raspberry Pi 4 code (`pi_control_system.py`) to your Raspberry Pi.

### 5. Set up Telegram Bot Credentials and Secure Key

1. **Create a Telegram bot**:
   - Open the Telegram app and search for `BotFather`.
   - Start a chat with **BotFather** and use the command `/newbot` to create a new bot.
   - Follow the prompts to name your bot and create a unique username for it.
   - After the bot is created, BotFather will give you a **bot token**. You’ll need this token for your notifications.

2. **Get your chat ID**:
   - Start a conversation with your newly created bot by sending a `/start` message.
   - To find your chat ID, you can use this URL in your browser, replacing `YOUR_BOT_TOKEN` with your actual bot token:
     `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`
   - This will return a JSON object where you can find your **chat ID**.

3. **Run the encrypt_token.py script**:
   This script will prompt you for your **Telegram bot token** and **chat ID**, and it will generate an encryption key. It will store the encrypted token and chat ID in a secure file located at `~/.config/bioreactor_secure_config`. 

4. To run the script, use:

`python3 encrypt_token.py`

5. The sensitive data will be stored securely in the `~/.config/bioreactor_secure_config` file, and this file will be protected by strict file permissions (only readable by the user).

6. Once the bot token and chat ID are encrypted and stored securely, the `pi_control_system.py` script will automatically decrypt and use these values to send notifications via Telegram.

---

## Running the System

### 1. Start the Raspberry Pi Control System

 - Run the following command on your Raspberry Pi to start the control system:

`python3 pi_control_system.py`

### 2. Using the Raspberry Pi Console

Once the control system is running, the following commands are available via the Raspberry Pi terminal:

- **`f` (feed)**: Logs a feed operation on the Pico.
  - Example: Enter `f` and then provide the feed amount in grams.
  
- **`c` (calibrate)**: Calibrates the CO2 sensor on the Pico.
  - Example: Enter `c` and then provide the CO2 value for calibration.

- **`s` (shutdown)**: Puts the Pico into deep sleep.

- **`r` (restart)**: Wakes the Pico from deep sleep by toggling the GPIO pin.

- **`e` (exit)**: Exits the Raspberry Pi control system.

### 3. Time Synchronization

The Raspberry Pi automatically syncs its time with the Pico upon startup and every 10 minutes to ensure accurate timestamps in the logged data.

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

## GPIO Wake-Up Pin

The Pico enters **deep sleep** after receiving the `SHUTDOWN` command. To wake the Pico:
- The Raspberry Pi sends the **restart command** (`r`).
- The Raspberry Pi toggles **GPIO17**, connected to **GP15** on the Pico, to wake it up from deep sleep.

---

## Telegram Notifications

The system will send an alert via Telegram when the CO2 level falls below 120% of the calibration value after initially exceeding it. This is managed by the **`pi_control_system.py`** script, which decrypts the bot token and chat ID from the secure configuration file.

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

---

## Additional Notes

- The Pico will log data to the SD card every 15 minutes, even when no commands are being sent.
- Ensure that you have the correct libraries installed on the Pico for the sensors and RTC to function properly.
- Use **Telegram notifications** to monitor CO2 levels remotely.
