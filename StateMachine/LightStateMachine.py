#
# LightStateMachine.py - This is the Python code used to demonstrate
# building a StateMachine that processes events to switch between 
# displaying a Red or Blue LED fading in and out.
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
## Imports required to allow us to build a fully functional state machine
##
from statemachine import StateMachine, State

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
## LightMachine - This is our StateMachine implementation class.
## The purpose of this state machine is to alternate between 
## a red and a blue LED. This example state machine provides the
## basis for the Milestone assignment.
##
class LightMachine(StateMachine):
    "A state machine designed to fade between two LEDs using PWM"

    ##
    ## Our two LEDs, utilizing GPIO 18, and GPIO 23
    ##
    redLight = PWMLED(18)
    blueLight = PWMLED(23)

    ##
    ## Define the three states for our machine.
    ##
    ##  off - nothing lit up
    ##  red - only red LED fading in and out
    ##  blue - only blue LED fading in and out
    ##
    off = State(initial = True)
    red = State()
    blue = State()

    ##
    ## begin - event that launches the state machine behavior
    ## by transitioning between off and the red light
    ##
    begin = (
        off.to(red)
    )

    ##
    ## cycle - event that provides the state machine behavior
    ## of transitioning between the red and the blue light
    ##
    cycle = (
        red.to(blue) |
        blue.to(red)
    )

    ##
    ## before_begin - event handler that runs just before the begin event
    ##
    def before_begin(self, event: str, source: State, target: State, message: str = ""):
        message = "* " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"
    
    ##
    ## before_cycle - event handler that runs just before the cycle event
    ##
    def before_cycle(self, event: str, source: State, target: State, message: str = ""):
        message = "* " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"
    
    ##
    ## on_enter_red - Action performed when the state machine transitions
    ## into the red state
    ##
    def on_enter_red(self):
        self.redLight.pulse()
        if(DEBUG):
            print("* Changing state to red")

    ##
    ## on_exit_red - Action performed when the statemachine transitions
    ## out of the red state.
    ##
    def on_exit_red(self):
        self.redLight.off()

    ##
    ## on_enter_blue - Action performed when the state machine transitions
    ## into the blue state
    ##
    def on_enter_blue(self):
        self.blueLight.pulse()
        if(DEBUG):
            print("* Changing state to blue")
    
    ##
    ## on_exit_blue - Action performed when the statemachine transitions
    ## out of the blue state.
    ##
    def on_exit_blue(self):
        self.blueLight.off()

    ##
    ## processButton - Utility method used to send events to the 
    ## state machine. This is triggered by the button_pressed event
    ## handler
    ##
    def processButton(self):
        if(self.current_state.id == 'off'):
            self.send("begin")
        else:
            self.send("cycle")

    ## End class LightMachine definition


##
## Initialize our State Machine
##
lightMachine = LightMachine()

##
## greenButton - setup our Button, tied to GPIO 24. Configure the
## action to be taken when the button is pressed to be the 
## execution of the processButton function in our State Machine
##
greenButton = Button(24)
greenButton.when_pressed = lightMachine.processButton

##
## Setup loop variable
##
repeat = True

##
## Repeat until the user creates a keyboard interrupt (CTRL-C)
##
while repeat:
    try:
        ## Only display if the DEBUG flag is set
        if(DEBUG):
            print("Killing time in a loop...")

        ## sleep for 20 seconds at a time. This value is not crucial, 
        ## all of the work for this application is handled by the 
        ## Button.when_pressed event process
        sleep(20)
    except KeyboardInterrupt:
        ## Catch the keyboard interrupt (CTRL-C) and exit cleanly
        ## we do not need to manually clean up the GPIO pins, the 
        ## gpiozero library handles that process.
        print("Cleaning up. Exiting...")

        ## Stop the loop
        repeat = False
        sleep(1)