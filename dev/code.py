import board
import busio
import adafruit_scd30

i2c = busio.I2C(board.GP21, board.GP20)
scd30 = adafruit_scd30.SCD30(i2c)

while True:
    if scd30.data_available:
        print(f"CO2: {scd30.CO2} ppm, Temp: {scd30.temperature} °C, Humidity: {scd30.relative_humidity} %")