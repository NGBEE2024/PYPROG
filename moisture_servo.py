import RPi.GPIO as GPIO #import RPi.GPIO module
from time import sleep

GPIO.setmode(GPIO.BCM) #choose BCM mode
GPIO.setwarnings(False)

GPIO.setup(26,GPIO.OUT) #set servo
GPIO.setup(4,GPIO.IN) #set moisture sensor
PWM=GPIO.PWM(26,50) #set 50Hz PWM output at GPIO26
sdelay=4
PWM.start(3) #3% duty cycle
print('duty cycle:', 3) #3 o'clock position
sleep(4) #allow time for movement

while (True):


    if GPIO.input(4): #if read a high at GPIO 4, moisture present
        print('detected HIGH i.e. moisture')
        PWM.start(13) #13% duty cycle
        print('duty cycle:', 13) #9 o'clock position
        sleep(sdelay) #allow time for movement
        PWM.start(3) #3% duty cycle
        sleep(sdelay)
    else: #otherwise (i.e. read a low) at GPIO 4, no moisture
        print('detected LOW i.e. no moisture')
        sleep(0.5) # to limit print() frequency

