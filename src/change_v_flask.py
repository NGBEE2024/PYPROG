from flask import Flask, request, render_template
import RPi.GPIO as GPIO
from time import sleep
import threading

app = Flask(__name__)

# Set up GPIO and PWM
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(26, GPIO.OUT)
GPIO.setup(4, GPIO.IN)
PWM = GPIO.PWM(26, 50)
PWM.start(3)  # Start servo at initial position
sdelay = 4  # Default delay value


def moisture_detection():
    global sdelay  # Ensure we are using the global sdelay
    while True:
        if GPIO.input(4):
            print('Detected HIGH (moisture present)')

            PWM.ChangeDutyCycle(8)
            print('duty cycle:', 8)
            sleep(2)
            PWM.ChangeDutyCycle(0)
            sleep(sdelay-2)
            

            PWM.ChangeDutyCycle(3)
            print('duty cycle:', 3)
            sleep(2)
        else:
            print('Detected LOW (no moisture)')
            PWM.ChangeDutyCycle(0)
            sleep(0.5)

@app.route('/')
def home():
    return render_template('change_v.html', sdelay=sdelay)

@app.route('/set_delay', methods=['POST'])
def set_delay():
    global sdelay
    try:
        new_delay = int(request.form['sdelay'])
        if 4 <= new_delay <= 20:  # Validate range
            sdelay = new_delay
            print(f"Delay set to: {sdelay} seconds")
        else:
            print("Delay out of range. Must be between 4 and 20 seconds.")
    except (ValueError, TypeError):
        print("Invalid input. Keeping current delay value.")
    return render_template('change_v.html', sdelay=sdelay)

if __name__ == '__main__':
    # Start moisture detection in a separate thread
    threading.Thread(target=moisture_detection, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)  # Changed to be accessible from network