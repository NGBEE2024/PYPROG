import I2C_LCD_driver #import the library
from time import sleep
import Adafruit_DHT


sensor=Adafruit_DHT.AM2302 #refer to this AM2302 as "sensor"
pin=4 #sensor output connected to GPIO 4

while(True):
    humidity,temperature=Adafruit_DHT.read_retry(sensor,pin)
        #read_retry function tries up to 15 times to get a sensor reading,
        #with 2-second wait between retries

    if humidity is not None and temperature is not None: #if both temp & humi are ok...
        print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature,humidity))
            #printed as "Temp=25.2*C  Humidity=56.7%" for instance
    else:
        print('Failed to get reading. Try again!')
    sleep(2)

    LCD = I2C_LCD_driver.lcd() #instantiate an lcd object, call it LCD
    LCD.backlight(1) #turn backlight on 
    humidity,temperature=Adafruit_DHT.read_retry(sensor,pin)
    if humidity is not None and temperature is not None: #if both temp & humi are ok...
        LCD.lcd_display_string("Temp:{0:0.1f}*C", 1) #write on line 1
        LCD.lcd_display_string("Humidity:{1:0.1f}%", 2, 2) #write on line 2
        if (temperature>32 & temperature<28)&(humidity>80):
            url = "https://api.telegram.org/bot7094057858:AAGU0CMWAcTnuMBJoUmBlg8HxUc8c1Mx3jw/sendMessage"
            payload = {
                "chat_id": "-1002405515611",  # Replace with your chat ID
                "temperature falls out of the range u want: ": f"Measured distance is {temperature}degree celsius"
            }
        if (humidity>80):
            url = "https://api.telegram.org/bot7094057858:AAGU0CMWAcTnuMBJoUmBlg8HxUc8c1Mx3jw/sendMessage"
            payload = {
                "chat_id": "-1002405515611",  # Replace with your chat ID
                "humidity falls out of the range u want: ": f"Measured distance is {humidity}degree celsius"
            }
    sleep(2) #wait 2 sec
    LCD.lcd_clear() #clear the display

    