import RPi.GPIO as GPIO
import time
import requests  # important
from datetime import datetime

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(25, GPIO.OUT)  # GPIO25 as Trig
GPIO.setup(27, GPIO.IN)  # GPIO27 as Echo

# Variable to track the last sent date
last_sent_date = None

# Define a function called distance:
def distance():
    # Produce a 10us pulse at Trig
    GPIO.output(25, 1)
    time.sleep(0.00001)
    GPIO.output(25, 0)

    # Measure pulse width (i.e., time of flight) at Echo
    StartTime = time.time()
    StopTime = time.time()
    while GPIO.input(27) == 0:
        StartTime = time.time()  # Capture start of high pulse
    while GPIO.input(27) == 1:
        StopTime = time.time()  # Capture end of high pulse
    ElapsedTime = StopTime - StartTime

    # Compute distance in cm, from time of flight
    Distance = (ElapsedTime * 34300) / 2
    return Distance


def ultra_to_tank():
    global last_sent_date  # Use the global variable to track the last sent date
    measured_distance = distance()

    # Get the current date in "YYYY-MM-DD" format
    current_date = datetime.now().strftime("%Y-%m-%d")

    if measured_distance > 50:
        # Check if a message has already been sent today
        if last_sent_date != current_date:
            TOKEN = "7094057858:AAGU0CMWAcTnuMBJoUmBlg8HxUc8c1Mx3jw"
            chat_id = "-1002405515611"
            message = "Refill the tank"
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
            
            # Send the Telegram message
            response = requests.get(url).json()
            print("Message sent:", response)

            # Update the last sent date
            last_sent_date = current_date
        else:
            print("Message already sent today. No message sent again.")
    else:
        print("Measured distance = {0:0.1f} cm".format(measured_distance))

    time.sleep(1)

while (True):
    ultra_to_tank()
    
    
