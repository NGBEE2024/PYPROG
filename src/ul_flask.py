import os
from flask import Flask, render_template, jsonify
import RPi.GPIO as GPIO
import time
import requests
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('water_monitor.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
TRIG_PIN = 25
ECHO_PIN = 27
GPIO.setup(TRIG_PIN, GPIO.OUT)  # Trig
GPIO.setup(ECHO_PIN, GPIO.IN)   # Echo

# Configuration
class Config:
    THING_SPEAK_CHANNEL_ID = "2746200"
    THING_SPEAK_READ_KEY = "IJ7JE71BJ5DVEMG7"
    THING_SPEAK_WRITE_KEY = "ATNCBN0ZUFSYGREX"
    TELEGRAM_TOKEN = "7094057858:AAGU0CMWAcTnuMBJoUmBlg8HxUc8c1Mx3jw"
    CHAT_ID = "-1002405515611"
    MEASUREMENT_TIMEOUT = 1.0  # seconds
    TANK_ALERT_THRESHOLD = 50  # cm
    UPDATE_INTERVAL = 5000     # milliseconds

def cleanup_gpio():
    GPIO.cleanup()

def distance():
    """Measure distance using ultrasonic sensor with error handling."""
    try:
        GPIO.output(TRIG_PIN, 1)
        time.sleep(0.00001)
        GPIO.output(TRIG_PIN, 0)
        
        StartTime = time.time()
        StopTime = time.time()
        timeout = time.time() + Config.MEASUREMENT_TIMEOUT
        
        # Wait for echo to start
        while GPIO.input(ECHO_PIN) == 0:
            StartTime = time.time()
            if time.time() > timeout:
                raise RuntimeError('Timed out waiting for Echo start')
        
        # Wait for echo to end
        while GPIO.input(ECHO_PIN) == 1:
            StopTime = time.time()
            if time.time() > timeout:
                raise RuntimeError('Timed out waiting for Echo end')
        
        distance = (StopTime - StartTime) * 34300 / 2
        app.logger.info(f"Measured distance: {distance:.2f} cm")
        return distance
        
    except Exception as e:
        app.logger.error(f"Error measuring distance: {e}")
        return -1

def get_last_refill_datetime():
    """Get the timestamp of the last tank refill."""
    try:
        url = f"https://api.thingspeak.com/channels/{Config.THING_SPEAK_CHANNEL_ID}/feeds.json"
        params = {
            'results': 10,
            'api_key': Config.THING_SPEAK_READ_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        records = response.json()["feeds"]
        last_seen_1 = None
        
        for record in reversed(records):
            if record["field3"] == "1":
                last_seen_1 = record["created_at"]
            elif record["field3"] == "0" and last_seen_1:
                return datetime.strptime(last_seen_1, "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y %H:%M")
        
        return "Unknown"
        
    except Exception as e:
        app.logger.error(f"Error fetching last refill datetime: {e}")
        return "Error"

def get_days_since_refill():
    """Calculate days since last refill."""
    try:
        last_refill = get_last_refill_datetime()
        if last_refill in ["Unknown", "Error"]:
            return last_refill
        return (datetime.now().date() - datetime.strptime(last_refill, "%d/%m/%Y %H:%M").date()).days
    except Exception as e:
        app.logger.error(f"Error calculating days since refill: {e}")
        return "Error"

def upload_to_thingspeak(value):
    """Upload data to ThingSpeak."""
    try:
        url = "https://api.thingspeak.com/update"
        params = {
            'api_key': Config.THING_SPEAK_WRITE_KEY,
            'field3': value
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        app.logger.info(f"Successfully uploaded value {value} to ThingSpeak")
        
    except Exception as e:
        app.logger.error(f"Error uploading to ThingSpeak: {e}")

def send_telegram_notification():
    """Send notification via Telegram."""
    try:
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage"
        params = {
            'chat_id': Config.CHAT_ID,
            'text': "Refill the tank"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        app.logger.info("Successfully sent Telegram notification")
        
    except Exception as e:
        app.logger.error(f"Error sending Telegram notification: {e}")

def check_and_notify():
    """Check water level and send notifications if needed."""
    level = distance()
    if level > Config.TANK_ALERT_THRESHOLD:
        upload_to_thingspeak(1)
        if get_last_refill_datetime() != datetime.now().strftime("%d/%m/%Y %H:%M"):
            send_telegram_notification()
    else:
        upload_to_thingspeak(0)
    return level

def fetch_thingspeak_data():
    """Fetch recent data from ThingSpeak."""
    try:
        url = f"https://api.thingspeak.com/channels/{Config.THING_SPEAK_CHANNEL_ID}/feeds.json"
        params = {
            'results': 5,
            'api_key': Config.THING_SPEAK_READ_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()["feeds"]
        
    except Exception as e:
        app.logger.error(f"Error fetching ThingSpeak data: {e}")
        return []

@app.route('/')
def index():
    """Render main page."""
    return render_template('ul.html',
                         days_since_refill=get_days_since_refill(),
                         last_refill=get_last_refill_datetime(),
                         channel_id=Config.THING_SPEAK_CHANNEL_ID,
                         update_interval=Config.UPDATE_INTERVAL)

@app.route('/update')
def update():
    """API endpoint for AJAX updates."""
    try:
        return jsonify({
            "days_since_refill": get_days_since_refill(),
            "tank_level": check_and_notify(),
            "last_refill_datetime": get_last_refill_datetime(),
            "history": fetch_thingspeak_data()
        })
    except Exception as e:
        app.logger.error(f"Error in update route: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        cleanup_gpio()