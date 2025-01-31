import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(26, GPIO.OUT)
GPIO.setup(4, GPIO.IN)
PWM = GPIO.PWM(26, 50)
sdelay = 4

# Start servo at initial position
PWM.start(3)
print('duty cycle:', 3)



while True:
    if GPIO.input(4):
        print('Detected HIGH (moisture present)')
        # Turn to 8% position and hold for full sdelay
        PWM.ChangeDutyCycle(8)
        print('duty cycle:', 8)
        sleep(2)
        PWM.ChangeDutyCycle(0)
        sleep(sdelay-2)
        
        # Turn back to 3% position and hold for full sdelay
        PWM.ChangeDutyCycle(3)
        print('duty cycle:', 3)
        sleep(2)
    else:
        print('Detected LOW (no moisture)')
        PWM.ChangeDutyCycle(0)
        sleep(0.5)

