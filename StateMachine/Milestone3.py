from gpiozero import Button, LED
from statemachine import StateMachine, State
from time import sleep
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
from threading import Thread, Lock
import logging

# Configure logging once at root level to write to log file
logging.basicConfig(
    filename='Milestone3.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

##
## DEBUG flag - boolean value to indicate whether or not to print 
## status messages on the console of the program
## 
DEBUG = True


##
## ManagedDisplay - Class intended to manage the 16x2 Display
##
class ManagedDisplay():
    # Build the LCD connection one GPIO pin at a time.
    def __init__(self):
        # These six pins are how the Raspberry Pi talks to the LCD.
        self.lcd_rs = digitalio.DigitalInOut(board.D17)
        self.lcd_en = digitalio.DigitalInOut(board.D27)
        self.lcd_d4 = digitalio.DigitalInOut(board.D5)
        self.lcd_d5 = digitalio.DigitalInOut(board.D6)
        self.lcd_d6 = digitalio.DigitalInOut(board.D13)
        self.lcd_d7 = digitalio.DigitalInOut(board.D26)

        self.lcd_columns = 16
        self.lcd_rows = 2 

        self.lcd = characterlcd.Character_LCD_Mono(
            self.lcd_rs, self.lcd_en, 
            self.lcd_d4, self.lcd_d5, self.lcd_d6, self.lcd_d7, 
            self.lcd_columns, self.lcd_rows
        )
        self.lcd.clear()

    # Clear and release LCD pins so the program exits cleanly.
    def cleanupDisplay(self):
        self.lcd.clear()
        self.lcd_rs.deinit()
        self.lcd_en.deinit()
        self.lcd_d4.deinit()
        self.lcd_d5.deinit()
        self.lcd_d6.deinit()
        self.lcd_d7.deinit()
        
    # Quick helper to blank the display.
    def clear(self):
        self.lcd.clear()

    # Replace the screen contents with a new message.
    def updateScreen(self, message):
        self.lcd.clear()
        self.lcd.message = message


##
## CWMachine - State Machine Implementation
##
class CWMachine(StateMachine):
    "A state machine designed to display morse code messages"

    # Timing constants in seconds
    DOT_SECONDS = 0.5
    DASH_SECONDS = 1.5
    DOT_DASH_PAUSE_SECONDS = 0.25
    LETTER_PAUSE_SECONDS = 0.75
    WORD_PAUSE_SECONDS = 3.0

    # Red LED means "dot" and blue LED means "dash".
    redLight = LED(18)
    blueLight = LED(23)

    # These are the two messages the button toggles between.
    message1 = "SOS"
    message2 = "OK"

    # State names used by the state machine engine.
    off = State(initial=True)
    dot = State()
    dash = State()
    dotDashPause = State()
    letterPause = State()
    wordPause = State()

    screen = ManagedDisplay()

    morseDict = {
        "A" : ".-", "B" : "-...", "C" : "-.-.", "D" : "-..",
        "E" : ".", "F" : "..-.", "G" : "--.", "H" : "....",
        "I" : "..", "J" : ".---", "K" : "-.-", "L" : ".-..",
        "M" : "--", "N" : "-.", "O" : "---", "P" : ".--.",
        "Q" : "--.-", "R" : ".-.", "S" : "...", "T" : "-",
        "U" : "..-", "V" : "...-", "W" : ".--", "X" : "-..-",
        "Y" : "-.--", "Z" : "--..", "0" : "-----", "1" : ".----",
        "2" : "..---", "3" : "...--", "4" : "....-", "5" : ".....",
        "6" : "-....", "7" : "--...", "8" : "---..", "9" : "----.",
        "+" : ".-.-.", "-" : "-....-", "/" : "-..-.", "=" : "-...-",
        ":" : "---...", "." : ".-.-.-", "$" : "...-..-", "?" : "..--..",
        "@" : ".--.-.", "&" : ".-...", "\"" : ".-..-.", "_" : "..--.-",
        "|" : "--...-", "(" : "-.--.-", ")" : "-.--.-"
    }

    # Each event goes into a state and then comes back to "off".
    doDot = (off.to(dot) | dot.to(off))
    doDash = (off.to(dash) | dash.to(off))
    doDDP = (off.to(dotDashPause) | dotDashPause.to(off))
    doLP = (off.to(letterPause) | letterPause.to(off))
    doWP = (off.to(wordPause) | wordPause.to(off))

    # Set up message tracking and threading safety.
    def __init__(self):
        super().__init__()
        self.activeMessage = self.message1
        self.pendingMessage = None
        self.endTransmission = False
        self.messageLock = Lock()
        self.workerThread = None

    # Make sure text always fits exactly on a 16-character LCD line.
    def _format_line(self, text):
        return str(text)[:16].ljust(16)

    # Helper to write two lines at once to the LCD.
    def _update_display(self, line1, line2=""):
        self.screen.updateScreen(
            f"{self._format_line(line1)}\n{self._format_line(line2)}"
        )

    # Choose the other message.
    def _next_message(self, current_message):
        if current_message == self.message1:
            return self.message2
        return self.message1

    # Apply a queued message change only after a full message completes.
    def _activate_pending_if_set(self):
        with self.messageLock:
            if self.pendingMessage is not None:
                self.activeMessage = self.pendingMessage
                self.pendingMessage = None
                if DEBUG:
                    print(f"* Applied pending message: {self.activeMessage}")

    # Read active/pending values safely from another thread.
    def _get_message_snapshot(self):
        with self.messageLock:
            return self.activeMessage, self.pendingMessage

    # Dot helper: switch into dot state and back out.
    def _send_dot(self):
        self.doDot()
        self.doDot()

    # Dash helper: switch into dash state and back out.
    def _send_dash(self):
        self.doDash()
        self.doDash()

    # Pause between Morse symbols in one letter.
    def _send_dot_dash_pause(self):
        self.doDDP()
        self.doDDP()

    # Pause between letters.
    def _send_letter_pause(self):
        self.doLP()
        self.doLP()

    # Pause between words or repeated message cycles.
    def _send_word_pause(self):
        self.doWP()
        self.doWP()

    # What to do when we enter the "dot" state.
    def on_enter_dot(self):
        self.redLight.blink(on_time=self.DOT_SECONDS, off_time=0, n=1, background=False)
        if DEBUG:
            print("* Changing state to red - dot")

    # Always turn red LED off when leaving dot state.
    def on_exit_dot(self):
        self.redLight.off()

    # What to do when we enter the "dash" state.
    def on_enter_dash(self):
        self.blueLight.blink(on_time=self.DASH_SECONDS, off_time=0, n=1, background=False)
        if DEBUG:
            print("* Changing state to blue - dash")

    # Always turn blue LED off when leaving dash state.
    def on_exit_dash(self):
        self.blueLight.off()

    # Keep LEDs off briefly between symbols.
    def on_enter_dotDashPause(self):
        sleep(self.DOT_DASH_PAUSE_SECONDS)
        if DEBUG:
            print("* Pausing Between Dots/Dashes - 250ms")

    # No extra cleanup needed for this pause state.
    def on_exit_dotDashPause(self):
        pass

    # Keep LEDs off between letters.
    def on_enter_letterPause(self):
        sleep(self.LETTER_PAUSE_SECONDS)
        if DEBUG:
            print("* Pausing Between Letters - 750ms")

    # No extra cleanup needed for this pause state.
    def on_exit_letterPause(self):
        pass

    # Keep LEDs off between words.
    def on_enter_wordPause(self):
        sleep(self.WORD_PAUSE_SECONDS)
        if DEBUG:
            print("* Pausing Between Words - 3000ms")

    # No extra cleanup needed for this pause state.
    def on_exit_wordPause(self):
        pass

    # Button requests the next message; this does not interrupt current output.
    def queue_next_message(self):
        with self.messageLock:
            reference = self.pendingMessage if self.pendingMessage else self.activeMessage
            self.pendingMessage = self._next_message(reference)
            queued_message = self.pendingMessage

        if DEBUG:
            print(f"* Queued next message: {queued_message}")

    # Called by button press: queue next message and show status.
    def processButton(self):
        self.queue_next_message()
        active, pending = self._get_message_snapshot()
        self._update_display(
            f"Sending:{active}",
            f"Next:{pending if pending else '-'}"
        )

    # Start Morse sending in a background thread.
    def run(self):
        self.workerThread = Thread(target=self.transmit, daemon=True)
        self.workerThread.start()
        
    # Main loop: convert message text to Morse and send it forever.
    def transmit(self):
        while not self.endTransmission:
            active_message, pending_message = self._get_message_snapshot()

            self._update_display(
                f"Sending:{active_message}",
                f"Next:{pending_message if pending_message else '-'}"
            )

            # Break text into words so we can add word-level pauses.
            word_list = active_message.split()

            for words_index, word in enumerate(word_list):
                for char_index, char in enumerate(word.upper()):
                    # Convert each character to its Morse pattern.
                    morse = self.morseDict.get(char)
                    if not morse:
                        logging.warning(f"Skipping unsupported character: {char}")
                        continue

                    self._update_display(
                        f"{active_message}:{char}",
                        f"Morse:{morse}"
                    )

                    for symbol_index, symbol in enumerate(morse):
                        # Dot uses red LED, dash uses blue LED.
                        if symbol == ".":
                            self._send_dot()
                        elif symbol == "-":
                            self._send_dash()

                        # Pause between symbols inside the same character.
                        if symbol_index < len(morse) - 1:
                            self._send_dot_dash_pause()

                    # Pause between letters in the same word.
                    if char_index < len(word) - 1:
                        self._send_letter_pause()

                # Pause between words in a multi-word message.
                if words_index < len(word_list) - 1:
                    self._send_word_pause()

            # Word pause between repeated messages
            self._send_word_pause()

            # Apply pending message toggle if button was pressed during transmit
            self._activate_pending_if_set()

        # Free LCD resources before program exits.
        self.screen.cleanupDisplay()


##
## System Execution Block
##
cwMachine = CWMachine()
cwMachine.run()

# Physical pushbutton connected to GPIO 24.
greenButton = Button(24)
greenButton.when_pressed = cwMachine.processButton

repeat = True

while repeat:
    try:
        if DEBUG:
            print("Killing time in a loop...")
        # Keep main thread alive while worker thread handles Morse output.
        sleep(20)
    except KeyboardInterrupt:
        print("Cleaning up. Exiting...")
        repeat = False
        cwMachine.endTransmission = True
        sleep(1)
        logging.info("State machine shutdown complete. System exited cleanly.")