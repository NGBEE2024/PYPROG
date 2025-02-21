import I2C_LCD_driver
import Adafruit_DHT

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN)
print(GPIO.input(21))

lcd = I2C_LCD_driver.lcd()
lcd.lcd_display_string("Hello", 1)


DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 21
humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)

print(f"Temp: {temperature}, Humidity: {humidity}")
