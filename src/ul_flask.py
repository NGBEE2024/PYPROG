from flask import Flask, render_template, jsonify
import RPi.GPIO as GPIO
import time
import requests
from datetime import datetime
import json

app = Flask(__name__)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(25, GPIO.OUT)  # Trig
GPIO.setup(27, GPIO.IN)  # Echo

# ThingSpeak & Telegram Config
THING_SPEAK_CHANNEL_ID = "2746200"
TELEGRAM_TOKEN = "7094057858:AAGU0CMWAcTnuMBJoUmBlg8HxUc8c1Mx3jw"
CHAT_ID = "-1002405515611"

def distance():
    GPIO.output(25, 1)
    time.sleep(0.00001)
    GPIO.output(25, 0)
    StartTime = time.time()
    StopTime = time.time()
    while GPIO.input(27) == 0:
        StartTime = time.time()
    while GPIO.input(27) == 1:
        StopTime = time.time()
    return (StopTime - StartTime) * 34300 / 2

def get_last_refill_timestamp():
    url = f"https://api.thingspeak.com/channels/{THING_SPEAK_CHANNEL_ID}/feeds.json?results=10&api_key=IJ7JE71BJ5DVEMG7"
    response = requests.get(url)
    
    if response.status_code == 200:
        records = json.loads(response.text)["feeds"]
        last_seen_1 = None
        for record in reversed(records):  # Loop from latest to oldest
            if record.get("field3") == "1":
                last_seen_1 = record["created_at"]  # Store full timestamp
            elif record.get("field3") == "0" and last_seen_1:
                return last_seen_1  # Return the last 0 after last 1
    
    return "Unknown"

def get_days_since_refill():
    last_refill = get_last_refill_timestamp()
    if last_refill == "Unknown":
        return "Unknown"
    
    try:
        last_refill_date = datetime.strptime(last_refill, "%Y-%m-%dT%H:%M:%SZ").date()
        return (datetime.now().date() - last_refill_date).days
    except ValueError:
        return "Unknown"

def upload_to_thingspeak(value):
    url = f"https://api.thingspeak.com/update?api_key=ATNCBN0ZUFSYGREX&field3={value}"  # Write to field3
    requests.get(url)

def check_and_notify():
    level = distance()
    if level > 50:
        upload_to_thingspeak(1)
        last_refill_date = get_last_refill_timestamp()
        
        if last_refill_date != "Unknown":
            try:
                last_refill_date_only = datetime.strptime(last_refill_date, "%Y-%m-%dT%H:%M:%SZ").date()
                today_date = datetime.now().date()

                if last_refill_date_only != today_date:
                    requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text=Refill the tank")
            except ValueError:
                pass
    else:
        upload_to_thingspeak(0)
    
    return level

def fetch_thingspeak_data():
    url = f"https://api.thingspeak.com/channels/{THING_SPEAK_CHANNEL_ID}/feeds.json?results=5&api_key=IJ7JE71BJ5DVEMG7"
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)["feeds"]
    return []

@app.route('/')
def index():
    return render_template('ul.html', 
                           days_since_refill=get_days_since_refill(), 
                           last_refill_timestamp=get_last_refill_timestamp())

@app.route('/update')
def update():
    return jsonify({
        "days_since_refill": get_days_since_refill(),
        "tank_level": check_and_notify(),
        "last_refill_timestamp": get_last_refill_timestamp(),  # Get date and time
        "history": fetch_thingspeak_data()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
