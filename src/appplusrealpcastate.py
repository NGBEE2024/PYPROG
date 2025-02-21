from flask import Flask, render_template, request, redirect
import Adafruit_DHT
import spidev
import I2C_LCD_driver
import RPi.GPIO as GPIO
import json
import time
import requests
import os
from datetime import datetime, timedelta

# Initialize Flask
app = Flask(__name__)

# Hardware and Sensor Setup
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.OUT)
LCD = I2C_LCD_driver.lcd()
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# Configurations
SYSTEM_STATE_FILE = "system_state.json"
THINGSPEAK_API_KEY = "IJ7JE71BJ5DVEMG7"  #write api
TELEGRAM_TOKEN = "7094057858:AAGU0CMWAcTnuMBJoUmBlg8HxUc8c1Mx3jw"
CHAT_ID = "-1002405515611"


DEFAULT_STATE = {
    "system": True,
    "temp_humi": True,
    "ldr": True
}

def read_system_state():
    if not os.path.exists(SYSTEM_STATE_FILE):
        with open(SYSTEM_STATE_FILE, "w") as f:
            json.dump(DEFAULT_STATE, f)
    with open(SYSTEM_STATE_FILE, "r") as f:
        return json.load(f)

def write_system_state(state):
    with open(SYSTEM_STATE_FILE, "w") as f:
        json.dump(state, f)

# thread that run in the background
def sensor_loop():
    last_temp_alert_time = None
    last_humidity_alert_time = None
    last_thingspeak_upload_time = None

    while True:
        state = read_system_state()
        
        if not state["system"]:
            LCD.lcd_clear()
            LCD.lcd_display_string("System OFF", 1)
            time.sleep(2)
            continue

        temp, humi = None, None
        if state["temp_humi"]:
            humi, temp = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
            if humi is not None and temp is not None:
                # upload to ThingSpeak every 15s
                if (last_thingspeak_upload_time is None) or \
                   (datetime.now() - last_thingspeak_upload_time).seconds >= 15:
                    requests.get(
                        f"https://api.thingspeak.com/update?api_key={THINGSPEAK_API_KEY}&field1={temp}&field2={humi}"
                    )
                    last_thingspeak_upload_time = datetime.now()
                
            
                if (temp < 18 or temp > 28) and \
                   (last_temp_alert_time is None or (datetime.now() - last_temp_alert_time) > timedelta(hours=24)):
                    requests.get(
                        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text=Temp Alert: {temp}C"
                    )
                    last_temp_alert_time = datetime.now()
                
                if humi > 80 and \
                   (last_humidity_alert_time is None or (datetime.now() - last_humidity_alert_time) > timedelta(hours=24)):
                    requests.get(
                        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text=Humidity Alert: {humi}%"
                    )
                    last_humidity_alert_time = datetime.now()


        ldr_value = None
        if state["ldr"]:
            ldr_value = readadc(0)
            GPIO.output(24, ldr_value < 500)


        LCD.lcd_clear()
        if temp and humi:
            LCD.lcd_display_string(f"T:{temp}C H:{humi}%", 1)
        else:
            LCD.lcd_display_string("T:ERR H:ERR", 1)
        LCD.lcd_display_string(f"LDR:{ldr_value}" if ldr_value else "LDR:OFF", 2)

        time.sleep(2)


@app.route("/")
def home():
    return render_template("index.html", state=read_system_state())

@app.route("/toggle", methods=["POST"])
def toggle():
    state = read_system_state()
    component = request.form.get("toggle")
    if component in state:
        state[component] = not state[component]
        write_system_state(state)
    return redirect("/")

if __name__ == "__main__":
    import threading
    threading.Thread(target=sensor_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)