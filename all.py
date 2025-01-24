import RPi.GPIO as GPIO
import time
import requests #important

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(25,GPIO.OUT) #GPIO25 as Trig
GPIO.setup(27,GPIO.IN) #GPIO27 as Echo

#define a function called distance below:
def distance():
    #produce a 10us pulse at Trig
    GPIO.output(25,1) 
    time.sleep(0.00001)
    GPIO.output(25,0)

    #measure pulse width (i.e. time of flight) at Echo
    StartTime=time.time()
    StopTime=time.time()
    while GPIO.input(27)==0:
        StartTime=time.time() #capture start of high pulse       
    while GPIO.input(27)==1:
        StopTime=time.time() #capture end of high pulse
    ElapsedTime=StopTime-StartTime

    #compute distance in cm, from time of flight
    Distance=(ElapsedTime*34300)/2
       #distance=time*speed of ultrasound,
       #/2 because to & fro
    return Distance

def ultra_to_tank():
    measured_distance = distance()    
    if measured_distance > 50:
        TOKEN= "7094057858:AAGU0CMWAcTnuMBJoUmBlg8HxUc8c1Mx3jw"
        chat_id="-1002405515611"
        message = "refill the tank"
        url =f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
        print(requests.get(url).json())

    print("Measured distance = {0:0.1f} cm".format(distance()))
    time.sleep(1)

while (True):
    ultra_to_tank()
    
    
