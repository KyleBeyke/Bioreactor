import board
import busio
import digitalio
import adafruit_sdcard
import storage
import os

# SPI configuration for Raspberry Pi Pico
spi = busio.SPI(board.GP10, board.GP11, board.GP12)
cs = digitalio.DigitalInOut(board.GP13)

# Attempt to initialize and mount the SD card
try:
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    
    # Check if the mount point directory exists, if not, create it
    if '/sd' not in os.listdir('/'):
        os.mkdir('/sd')  # Create the mount point

    storage.mount(vfs, "/sd")
    print("SD card mounted successfully!")
except OSError as e:
    print("Failed to mount SD card:", e)