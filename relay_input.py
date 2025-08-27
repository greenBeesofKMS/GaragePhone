import RPi.GPIO as GPIO
import time

# --- Pin Definitions ---
# Set the GPIO pin that the relay's IN1 pin is connected to
RELAY_PIN = 22 

# --- Setup ---
# Set GPIO mode to BCM (Broadcom SOC channel numbers)
GPIO.setmode(GPIO.BCM)

# Set RELAY_PIN as an output, and initialize it to LOW (relay is off)
GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)

# --- Instructions ---
print("Relay Input Control")
print("Type 'o' + enter to turn the light ON")
print("Type 'f' + enter to turn the light OFF")
print("Type 'q' + enter to quit")
print("-----------------------------------")

# A variable to prevent printing the same message over and over
light_is_on = False


try:
    # This is the main loop that will run continuously
    while True:
        keyboardInput = input()
        # Check if the 'o' key is currently being pressed
        if keyboardInput == 'o':
            if not light_is_on:
                print("Key 'o' pressed: Turning light ON")
                GPIO.output(RELAY_PIN, GPIO.HIGH) # Send HIGH signal to activate relay
                light_is_on = True

        # Check if the 'f' key is currently being pressed
        if keyboardInput == 'f':
            if light_is_on:
                print("Key 'f' pressed: Turning light OFF")
                GPIO.output(RELAY_PIN, GPIO.LOW) # Send LOW signal to deactivate relay
                light_is_on = False

        # Check if the 'q' key is pressed to quit the loop
        if keyboardInput == 'q':
            print("Key 'q' pressed: Exiting program.")
            break # Exit the while loop

        time.sleep(0.1) # A short delay to prevent the script from using too much CPU

finally:
    # This part of the code will run when the loop is exited (by pressing 'q')
    # It's important to clean up the GPIO channels to reset them to their default state.
    print("Cleaning up GPIO pins.")
    GPIO.cleanup()