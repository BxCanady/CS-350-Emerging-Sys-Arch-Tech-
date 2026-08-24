# Thermostat - This is the Python code used to demonstrate
# the functionality of the thermostat that we have prototyped throughout
# the course.
#
# This code works with the test circuit that was built for module 7.
#
# Functionality:
#
# The thermostat has three states: off, heat, cool
#
# The lights will represent the state that the thermostat is in.
#
# If the thermostat is set to off, the lights will both be off.
#
# If the thermostat is set to heat, the Red LED will be fading in
# and out if the current temperature is below the set temperature;
# otherwise, the Red LED will be on solid.
#
# If the thermostat is set to cool, the Blue LED will be fading in
# and out if the current temperature is above the set temperature;
# otherwise, the Blue LED will be on solid.
#
# One button will cycle through the three states of the thermostat.
#
# One button will raise the setpoint by a degree.
#
# One button will lower the setpoint by a degree.
#
# The LCD display will display the date and time on one line and
# alternate the second line between the current temperature and
# the state of the thermostat along with its set temperature.
#
# The Thermostat will send a status update to the TemperatureServer
# over the serial port every 15 seconds in a comma delimited string
# including the state of the thermostat, the current temperature
# in degrees Fahrenheit, and the setpoint of the thermostat.

from time import sleep
from datetime import datetime
from statemachine import StateMachine, State

import board
import adafruit_ahtx0

import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

import serial
from gpiozero import Button, PWMLED
from threading import Thread, Lock
from math import floor

# DEBUG flag
DEBUG = True


# ------------------------------------------------------------------
# I2C / AHT20 SENSOR SETUP
# ------------------------------------------------------------------

i2c = board.I2C()
thSensor = adafruit_ahtx0.AHTx0(i2c)

# Synchronize multi-threaded access to the I2C bus
i2c_lock = Lock()
last_known_temp = 72.0


# ------------------------------------------------------------------
# SERIAL / UART SETUP
# ------------------------------------------------------------------

ser = serial.Serial(
    port='/dev/ttyS0',
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)


# ------------------------------------------------------------------
# LED SETUP
# ------------------------------------------------------------------

redLight = PWMLED(18)
blueLight = PWMLED(23)


# ------------------------------------------------------------------
# LCD DISPLAY CLASS
# ------------------------------------------------------------------

class ManagedDisplay():
    """
    Class used to manage the 16x2 LCD display.
    """

    def __init__(self):
        self.lcd_rs = digitalio.DigitalInOut(board.D17)
        self.lcd_en = digitalio.DigitalInOut(board.D27)
        self.lcd_d4 = digitalio.DigitalInOut(board.D5)
        self.lcd_d5 = digitalio.DigitalInOut(board.D6)
        self.lcd_d6 = digitalio.DigitalInOut(board.D13)
        self.lcd_d7 = digitalio.DigitalInOut(board.D26)

        self.lcd_columns = 16
        self.lcd_rows = 2

        self.lcd = characterlcd.Character_LCD_Mono(
            self.lcd_rs,
            self.lcd_en,
            self.lcd_d4,
            self.lcd_d5,
            self.lcd_d6,
            self.lcd_d7,
            self.lcd_columns,
            self.lcd_rows
        )
        self.lcd.clear()

    def cleanupDisplay(self):
        try:
            self.lcd.clear()
            self.lcd_rs.deinit()
            self.lcd_en.deinit()
            self.lcd_d4.deinit()
            self.lcd_d5.deinit()
            self.lcd_d6.deinit()
            self.lcd_d7.deinit()
        except Exception:
            pass

    def clear(self):
        self.lcd.clear()

    def updateScreen(self, message):
        self.lcd.clear()
        self.lcd.message = message


screen = ManagedDisplay()


# ------------------------------------------------------------------
# THERMOSTAT STATE MACHINE
# ------------------------------------------------------------------

class TemperatureMachine(StateMachine):
    """
    State machine used to manage the thermostat's off, heat, and cool states.
    """

    off = State(initial=True)
    heat = State()
    cool = State()

    setPoint = 72
    cycleCount = 0

    cycle = (
        off.to(heat) |
        heat.to(cool) |
        cool.to(off)
    )

    # --------------------------------------------------------------
    # STATE TRANSITIONS & HANDLERS
    # --------------------------------------------------------------

    def on_enter_heat(self):
        self.updateLights()
        if DEBUG:
            print("* Changing state to heat")

    def on_exit_heat(self):
        redLight.off()

    def on_enter_cool(self):
        self.updateLights()
        if DEBUG:
            print("* Changing state to cool")

    def on_exit_cool(self):
        blueLight.off()

    def on_enter_off(self):
        redLight.off()
        blueLight.off()
        if DEBUG:
            print("* Changing state to off")

    def flashSignal(self):
        redLight.on()
        blueLight.on()
        sleep(0.15)
        redLight.off()
        blueLight.off()
        sleep(0.15)

    def processTempStateButton(self):
        if DEBUG:
            print(f"\n[BUTTON] Cycle state button pressed (Current: {self.getStateId()})")

        self.flashSignal()
        self.cycle()
        self.cycleCount += 1

        if DEBUG:
            print(f"[STATE] Transitioned to: {self.getStateId()} (Cycles: {self.cycleCount})")

    def processTempIncButton(self):
        if DEBUG:
            print("Increasing Set Point")
        self.setPoint += 1
        self.updateLights()

    def processTempDecButton(self):
        if DEBUG:
            print("Decreasing Set Point")
        self.setPoint -= 1
        self.updateLights()

    # --------------------------------------------------------------
    # UPDATE LED STATES
    # --------------------------------------------------------------

    def updateLights(self):
        """
        Update LEDs based on thermostat state and temperature:
        A. Heat & temp < setPoint  -> Red LED pulses
        B. Cool & temp > setPoint  -> Blue LED pulses
        C. Heat & temp >= setPoint -> Red LED solid ON
        D. Cool & temp <= setPoint -> Blue LED solid ON
        """
        temp = self.getFahrenheit()
        state_id = self.getStateId().lower()

        if DEBUG:
            print(f"[LED] State: {state_id}")
            print(f"[LED] Temperature: {temp:.2f} F")
            print(f"[LED] Set Point: {self.setPoint} F")

        # Always stop active LED modes before switching states
        redLight.off()
        blueLight.off()

        # HEAT MODE
        if state_id == 'heat':
            if temp < self.setPoint:
                # Requirement A: Red LED fades in and out when below set point
                redLight.pulse(fade_in_time=1, fade_out_time=1, n=None, background=True)
                if DEBUG:
                    print("[LED] RED = FADING (Heating active)")
            else:
                # Requirement C: Red LED solid ON when set point reached or exceeded
                redLight.on()
                if DEBUG:
                    print("[LED] RED = SOLID (Set point reached)")

        # COOL MODE
        elif state_id == 'cool':
            if temp > self.setPoint:
                # Requirement B: Blue LED fades in and out when above set point
                blueLight.pulse(fade_in_time=1, fade_out_time=1, n=None, background=True)
                if DEBUG:
                    print("[LED] BLUE = FADING (Cooling active)")
            else:
                # Requirement D: Blue LED solid ON when set point reached or dropped below
                blueLight.on()
                if DEBUG:
                    print("[LED] BLUE = SOLID (Set point reached)")

        # OFF MODE
        else:
            redLight.off()
            blueLight.off()
            if DEBUG:
                print("[LED] BOTH = OFF")

    def run(self):
        myThread = Thread(target=self.manageMyDisplay)
        myThread.start()

    def getFahrenheit(self):
        global last_known_temp
        with i2c_lock:
            try:
                t = thSensor.temperature
                last_known_temp = ((9 / 5) * t) + 32
            except (OSError, RuntimeError) as e:
                if DEBUG:
                    print(f"[I2C BUS ERROR] Reading failed ({e}). Returning cached temp: {last_known_temp:.2f} F")
        return last_known_temp

    def getStateId(self):
        """
        Return the current thermostat state normalized as a lowercase string.
        """
        if hasattr(self, 'current_state_id') and self.current_state_id:
            return str(self.current_state_id).lower()

        if hasattr(self, 'current_state'):
            current_state = self.current_state
            if hasattr(current_state, 'id') and current_state.id:
                return str(current_state.id).lower()
            if hasattr(current_state, 'value') and current_state.value:
                return str(current_state.value).lower()
            if hasattr(current_state, 'name') and current_state.name:
                return str(current_state.name).lower()
            return str(current_state).lower()

        return "off"

    def setupSerialOutput(self):
        state_str = self.getStateId()
        current_temp = floor(self.getFahrenheit())
        return f"{state_str},{current_temp},{self.setPoint}\n"

    def cleanup(self):
        if DEBUG:
            print("Cleaning up. Exiting...")

        self.endDisplay = True
        sleep(1)

        redLight.off()
        blueLight.off()

        for device_name in ('greenButton', 'redButton', 'blueButton', 'redLight', 'blueLight'):
            device = globals().get(device_name)
            if device is not None:
                try:
                    device.close()
                except Exception as e:
                    if DEBUG:
                        print(f"[CLEANUP] Failed to close {device_name}: {e}")

        screen.cleanupDisplay()

        if ser.is_open:
            ser.close()

        if DEBUG:
            print("Cleanup complete.")

    endDisplay = False

    def manageMyDisplay(self):
        counter = 1
        altCounter = 1

        while not self.endDisplay:
            if DEBUG:
                print("Processing Display Info...")

            current_time = datetime.now()
            lcd_line_1 = current_time.strftime("%Y-%m-%d %H:%M\n")

            if altCounter < 6:
                current_temp = floor(self.getFahrenheit())
                lcd_line_2 = f"T:{current_temp}F Cy:{self.cycleCount}"
                altCounter += 1
            else:
                state_str = self.getStateId()
                lcd_line_2 = f"{state_str.upper()} S:{self.setPoint} C:{self.cycleCount}"
                altCounter += 1

                if altCounter >= 11:
                    self.updateLights()
                    altCounter = 1

            screen.updateScreen(lcd_line_1 + lcd_line_2)

            if DEBUG:
                print(f"Counter: {counter}")

            if (counter % 15) == 0:
                serial_output = self.setupSerialOutput()
                if DEBUG:
                    print(f"[UART] Sending: {serial_output.strip()}")
                ser.write(serial_output.encode('utf-8'))
                counter = 1
            else:
                counter += 1

            sleep(1)


# ------------------------------------------------------------------
# CREATE STATE MACHINE & BUTTON HARDWARE SETUP
# ------------------------------------------------------------------

tsm = TemperatureMachine()
tsm.run()

greenButton = Button(24)
greenButton.when_pressed = tsm.processTempStateButton

redButton = Button(25)
redButton.when_pressed = tsm.processTempIncButton

blueButton = Button(12)
blueButton.when_pressed = tsm.processTempDecButton


# ------------------------------------------------------------------
# MAIN PROGRAM LOOP
# ------------------------------------------------------------------

repeat = True

try:
    while repeat:
        sleep(30)
except KeyboardInterrupt:
    if DEBUG:
        print("\nKeyboard interrupt received.")
finally:
    tsm.cleanup()