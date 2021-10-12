import RPi.GPIO as GPIO
import time

class Ultrasonic():

    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        self.GPIO_TRIGGER = 23
        self.GPIO_ECHO = 24

        GPIO.setup(self.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO, GPIO.IN)

        


    def distance(self):
        GPIO.output(self.GPIO_TRIGGER,True)
        
        time.sleep(0.0001)
        GPIO.output(self.GPIO_TRIGGER, False)
        
        StartTime = time.time()
        StopTime = time.time()
        
        # save StartTime
        while GPIO.input(self.GPIO_ECHO) == 0:
            StartTime = time.time()
        
        while GPIO.input(self.GPIO_ECHO) == 1:
            StopTime = time.time()
        
        TimeElapsed = StopTime - StartTime
        
        distance = (TimeElapsed*34300)/2
        
        return distance
        
    def cleanup(self):
        GPIO.cleanup()

if __name__ == '__main__':
    try:
        while True:
            ultrasonic = Ultrasonic()
            dist = ultrasonic.distance()
            print("Measured distance = %.1f cm" %dist)
            time.sleep(1)
    except KeyboardInterrupt:
        print('Measurement stopped by User')
        GPIO.cleanup()
        
                        