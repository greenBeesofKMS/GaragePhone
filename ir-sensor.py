import RPi.GPIO as GPIO
import time
from datetime import datetime

# Set the GPIO mode to BCM
# This means we are referring to the pins by the "Broadcom SOC channel" number
GPIO.setmode(GPIO.BCM)

# Define the GPIO pin that the OUT pin of the sensor is connected to
PIR_PIN = 17

# Set the PIR_PIN as an input pin
GPIO.setup(PIR_PIN, GPIO.IN)

print("PIR Module Test (CTRL+C to exit)")
time.sleep(2)
print("Ready")

try:
    while True:
        # Wait until the sensor reads something
        GPIO.wait_for_edge(PIR_PIN, GPIO.RISING)
        print(datetime.now())

except KeyboardInterrupt:
    print(" Quit")
    # Reset the GPIO pins
    GPIO.cleanup()