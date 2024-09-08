import board
import busio
import sdcardio
import storage
import digitalio

# Initialize SPI bus and chip select pin
spi = busio.SPI(board.GP10, board.GP11, board.GP12)
cs = board.GP13

# Wait for the SPI lock and configure
while not spi.try_lock():
    pass
spi.configure(baudrate=1000000)  # Set the clock speed to 1 MHz
spi.unlock()

# Try mounting the SD card
try:
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    print("SD card mounted successfully!")
except OSError as e:
    print("Failed to mount SD card:", e)