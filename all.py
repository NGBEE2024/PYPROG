import RPi.GPIO as GPIO
import time
import requests  # important

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(25, GPIO.OUT)  # GPIO25 as Trig
GPIO.setup(27, GPIO.IN)  # GPIO27 as Echo

# Define a function called distance below:
def distance():
    # Produce a 10us pulse at Trig
    GPIO.output(25, 1)
    time.sleep(0.00001)
    GPIO.output(25, 0)

    # Measure pulse width (i.e. time of flight) at Echo
    StartTime = time.time()
    StopTime = time.time()

    timeout = StartTime + 1  # 1-second timeout
    while GPIO.input(27) == 0 and time.time() < timeout:
        StartTime = time.time()  # Capture start of high pulse

    timeout = StartTime + 1  # Reset timeout
    while GPIO.input(27) == 1 and time.time() < timeout:
        StopTime = time.time()  # Capture end of high pulse

    ElapsedTime = StopTime - StartTime

    # Compute distance in cm, from time of flight
    Distance = (ElapsedTime * 34300) / 2
    # distance = time * speed of ultrasound, /2 because to & fro
    return Distance


def ultra_to_tank():
    measured_distance = distance()
    if measured_distance > 50:
        # Send a message to Telegram
        url = "https://api.telegram.org/bot7094057858:AAGU0CMWAcTnuMBJoUmBlg8HxUc8c1Mx3jw/sendMessage"
        payload = {
            "chat_id": "-1002405515611",  # Replace with your chat ID
            "text": f"Measured distance is {measured_distance:0.1f} cm, which is above 50 cm."
        }
        requests.post(url, json=payload)

    print("Measured distance = {0:0.1f} cm".format(measured_distance))
    time.sleep(1)


while (True):
    ultra_to_tank()
    
    
