import time
import board
import busio
import digitalio
import storage
import adafruit_sdcard
import os

# Initialize SPI and CS (Chip Select) for the SD card
spi = busio.SPI(clock=board.GP10, MOSI=board.GP11, MISO=board.GP12)
cs = digitalio.DigitalInOut(board.GP13)  # Chip select pin

# Initialize the SD card using the SPI interface
sdcard = adafruit_sdcard.SDCard(spi, cs)

# Try to mount the SD card to the filesystem
try:
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    print("SD card mounted successfully.")
except OSError as e:
    print("Failed to mount SD card:", e)

# Test if the card is writable and display a simple directory listing
try:
    with open("/sd/test.txt", "w") as f:
        f.write("Testing SD card write...\n")
    print("Write test completed successfully.")
    
    # Display the files on the SD card
    print("Files on the SD card:")
    print(os.listdir("/sd"))

except OSError as e:
    print("Error during SD card operation:", e)

# Function to log data to the SD card (example function)
def log_to_sd(data):
    """Logs the provided data to a file on the SD card."""
    try:
        with open("/sd/log.txt", "a") as log_file:
            log_file.write(f"{data}\n")
        print("Data logged to SD card.")
    except OSError as e:
        print("Failed to log data:", e)

# Main loop (you can add your sensor data logic here)
while True:
    sensor_data = "Sample sensor data"  # Replace with actual sensor data
    log_to_sd(sensor_data)
    time.sleep(15)  # Log every 15 seconds