import Adafruit_DHT
import requests
import spidev
import I2C_LCD_driver
import RPi.GPIO as GPIO
import threading
from time import sleep
from datetime import datetime, timedelta
from flask import Flask, render_template, request

# Flask app setup
app = Flask(__name__)

# Sensor type: DHT11 or DHT22
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 21

# Telegram Bot
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# SPI and GPIO setup
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(24, GPIO.OUT)

# LCD Initialization
LCD = I2C_LCD_driver.lcd()

# **System Control Variables**
temp_humi_enabled = True
ldr_enabled = True

# Temperature & Humidity Thresholds
temp_threshold_min = 18
temp_threshold_max = 28
humidity_threshold_max = 80

# Track last alert times
last_temp_alert_time = None
last_humidity_alert_time = None

def can_send_alert(last_alert_time):
    return last_alert_time is None or datetime.now() - last_alert_time > timedelta(days=1)

def readadc(adcnum):
    if adcnum > 7 or adcnum < 0:
        return -1
    r = spi.xfer2([1, (8 + adcnum) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]

@app.route('/')
def index():
    return render_template('thir.html', temp_humi=temp_humi_enabled, ldr=ldr_enabled,
                           temp_min=temp_threshold_min, temp_max=temp_threshold_max,
                           humidity_max=humidity_threshold_max)

@app.route('/toggle_temp_humi', methods=['POST'])
def toggle_temp_humi():
    global temp_humi_enabled
    temp_humi_enabled = not temp_humi_enabled
    return ('', 204)

@app.route('/toggle_ldr', methods=['POST'])
def toggle_ldr():
    global ldr_enabled
    ldr_enabled = not ldr_enabled
    return ('', 204)

@app.route('/set_thresholds', methods=['POST'])
def set_thresholds():
    global temp_threshold_min, temp_threshold_max, humidity_threshold_max
    temp_threshold_min = int(request.form['temp_min'])
    temp_threshold_max = int(request.form['temp_max'])
    humidity_threshold_max = int(request.form['humidity_max'])
    return ('', 204)

def sensor_monitoring():
    global last_temp_alert_time, last_humidity_alert_time
    while True:
        if temp_humi_enabled:
            humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            if humidity is not None and temperature is not None:
                if (temperature < temp_threshold_min or temperature > temp_threshold_max) and can_send_alert(last_temp_alert_time):
                    message = f"Alert! Temperature is {temperature}°C, outside the threshold!"
                    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}")
                    last_temp_alert_time = datetime.now()
                if humidity > humidity_threshold_max and can_send_alert(last_humidity_alert_time):
                    message = f"Alert! Humidity is {humidity}%, too high!"
                    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}")
                    last_humidity_alert_time = datetime.now()
            else:
                print("Failed to retrieve data from sensor!")
        
        if ldr_enabled:
            LDR_value = readadc(0)
            GPIO.output(24, 1 if LDR_value < 500 else 0)
            print(f"LDR = {LDR_value}")

        LCD.lcd_display_string(f"Temp: {'ON' if temp_humi_enabled else 'OFF'}", 1)
        LCD.lcd_display_string(f"LDR: {'ON' if ldr_enabled else 'OFF'}", 2)
        sleep(2)

threading.Thread(target=sensor_monitoring, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
