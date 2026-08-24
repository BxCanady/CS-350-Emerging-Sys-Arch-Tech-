#
# ButtonTest.py - This is the Python code used to demonstrate
# the functionality of buttons and PWMLED controls from the
# gpiozero library by displaying a Red or Blue LED fading in and out.
#
# This code works with the test circuit that was built for module 5.
#
#------------------------------------------------------------------
# Change History
#------------------------------------------------------------------
# Version   |   Description
#------------------------------------------------------------------
#    1          Initial Development
#------------------------------------------------------------------

##
## Imports required to handle our Button, and our PWMLED devices
##
from gpiozero import Button, PWMLED

##
## Import required to allow us to pause for a specified length of time
##
from time import sleep

##
## DEBUG flag - boolean value to indicate whether or not to print 
## status messages on the console of the program
## 
DEBUG = True

##
## Our two LEDs, utilizing GPIO 18, and GPIO 23
##
red = PWMLED(18)
blue = PWMLED(23)

##
## swap - utility function used to alternate between
## the red and the blue LED
##
def swap():
    ## Only display if the DEBUG flag is set
    if(DEBUG):
        print("Button Pressed *")
        print(f"Red: {red.value}, Blue: {blue.value}")

    ##
    ## if everything is off, start red
    ##
    if(red.value == 0 and blue.value == 0):
        ## Only display if the DEBUG flag is set
        if(DEBUG):
            print('Initializing red')
        red.pulse()
    ##
    ## If red is running, switch to blue
    ## 
    elif(red.value > 0):
        ## Only display if the DEBUG flag is set
        if(DEBUG):
            print('Switching to blue')
        red.off()
        blue.pulse()
    ##
    ## If blue is running, switch to red
    ## 
    elif(blue.value > 0):
        ## Only display if the DEBUG flag is set
        if(DEBUG):
            print('Switching to red')
        blue.off()
        red.pulse()
    ##
    ## Catchall: switch to red
    ## 
    else:
        ## Only display if the DEBUG flag is set
        if(DEBUG):
            print('Resetting to red')
        red.off()
        blue.off()
        red.pulse()

##
## Configure our button to use GPIO 24 and to execute
## the swap method when pressed.
##
greenButton = Button(24)
greenButton.when_pressed = swap

##
## Setup our loop control flag
##
repeat = True

##
## Dummy loop to run over time.
##
while repeat:
    try:
        if(greenButton.is_pressed):
            ## Only display if the DEBUG flag is set
            if(DEBUG):
                print("Button Pressed")
        sleep(20)
    except KeyboardInterrupt:
        print("Cleaning up. Exiting...")
        repeat = False
        sleep(1)