from machine import Pin, PWM
import time

# Standard Note Frequencies
NOTES = {
    'B0': 31, 'C1': 33, 'CS1': 35, 'D1': 37, 'DS1': 39, 'E1': 41, 'F1': 44, 'FS1': 46, 'G1': 49, 'GS1': 52, 'A1': 55, 'AS1': 58, 'B1': 62,
    'C2': 65, 'CS2': 69, 'D2': 73, 'DS2': 78, 'E2': 82, 'F2': 87, 'FS2': 93, 'G2': 98, 'GS2': 104, 'A2': 110, 'AS2': 117, 'B2': 123,
    'C3': 131, 'CS3': 139, 'D3': 147, 'DS3': 156, 'E3': 165, 'F3': 175, 'FS3': 185, 'G3': 196, 'GS3': 208, 'A3': 220, 'AS3': 233, 'B3': 247,
    'C4': 262, 'CS4': 277, 'D4': 294, 'DS4': 311, 'E4': 330, 'F4': 349, 'FS4': 370, 'G4': 392, 'GS4': 415, 'A4': 440, 'AS4': 466, 'B4': 494,
    'C5': 523, 'CS5': 554, 'D5': 587, 'DS5': 622, 'E5': 659, 'F5': 698, 'FS5': 740, 'G5': 784, 'GS5': 831, 'A5': 880, 'AS5': 932, 'B5': 988,
    'C6': 1047, 'CS6': 1109, 'D6': 1175, 'DS6': 1245, 'E6': 1319, 'F6': 1397, 'FS6': 1480, 'G6': 1568, 'GS6': 1661, 'A6': 1760, 'AS6': 1865, 'B6': 1976,
    'C7': 2093, 'CS7': 2217, 'D7': 2349, 'DS7': 2489, 'E7': 2637, 'F7': 2794, 'FS7': 2960, 'G7': 3136, 'GS7': 3322, 'A7': 3520, 'AS7': 3729, 'B7': 3951,
    'C8': 4186, 'CS8': 4435, 'D8': 4699, 'DS8': 4978, 'REST': 0
}

class Buzzer:
    def __init__(self, pin_num, active_low=True):
        """
        Initialize the Buzzer.
        pin_num: GPIO pin number
        active_low: True if buzzer is Low Level Triggered (default), False if High Level
        """
        self.pin_num = pin_num
        self.active_low = active_low
        self.pwm = None
        
        # Initialize as regular IO first
        self.pin = Pin(pin_num, Pin.OUT)
        
        # Ensure it's OFF initially
        # If Active Low: OFF = 1 (High)
        # If Active High: OFF = 0 (Low)
        initial_state = 1 if active_low else 0
        self.pin.value(initial_state)

    def _ensure_pwm(self):
        """Ensure PWM is initialized"""
        if self.pwm is None:
            # Create PWM object
            self.pwm = PWM(Pin(self.pin_num))
            # Standard PWM frequency and duty cycle
            self.pwm.freq(1000)
            self.pwm.duty(0)

    def _ensure_pin(self):
        """Ensure Pin is in GPIO mode (not PWM)"""
        if self.pwm is not None:
            self.pwm.deinit()
            self.pwm = None
        # Re-initialize Pin
        self.pin = Pin(self.pin_num, Pin.OUT)

    def tone(self, freq=1000, duration_ms=None, duty=512):
        """
        Play a tone using PWM (For Passive Buzzer or Variable Active)
        freq: Frequency in Hz
        duration_ms: Duration in milliseconds (optional, blocking if set)
        duty: Duty cycle (0-1023), 512 is 50%
        """
        if freq == 0:
            self.quiet()
            if duration_ms:
                time.sleep_ms(duration_ms)
            return

        self._ensure_pwm()
        self.pwm.freq(freq)
        self.pwm.duty(duty)
        
        if duration_ms:
            time.sleep_ms(duration_ms)
            self.quiet()

    def quiet(self):
        """Stop the sound (Mute)"""
        if self.pwm is not None:
            self.pwm.duty(0)
            self.pwm.deinit()
            self.pwm = None
        
        # Turn OFF via GPIO
        self.off()

    def on(self):
        """Turn ON (Constant Sound)"""
        self._ensure_pin()
        # If Active Low: ON = 0
        # If Active High: ON = 1
        val = 0 if self.active_low else 1
        self.pin.value(val)

    def off(self):
        """Turn OFF (Silence)"""
        self._ensure_pin()
        # If Active Low: OFF = 1
        # If Active High: OFF = 0
        val = 1 if self.active_low else 0
        self.pin.value(val)

    def beep(self, times=1, freq=1000, duration_ms=100, pause_ms=100):
        """
        Beep multiple times
        times: Number of beeps
        freq: Frequency (for passive usage)
        duration_ms: Beep duration
        pause_ms: Pause between beeps
        """
        for i in range(times):
            self.tone(freq, duration_ms)
            if i < times - 1:
                time.sleep_ms(pause_ms)
    
    def play_melody(self, melody, tempo=1.0):
        """
        Play a melody defined by a list of (note_name, note_duration)
        melody: List of (note_name_str, duration_ms_int)
        tempo: Speed multiplier (1.0 = normal, 0.5 = fast, 2.0 = slow)
        """
        for note_name, duration in melody:
            freq = NOTES.get(note_name, 0)
            # Play tone
            self.tone(freq, int(duration * tempo))
            # Tiny pause between notes for articulation
            time.sleep_ms(int(20 * tempo))

# -------------------------------------------------------------------------
# Test Function
# -------------------------------------------------------------------------
def test_buzzer():
    print("=== Testing Buzzer on Pin 14 ===")
    
    # Initialize Buzzer on Pin 14 (Active Low by default)
    print("Initializing Buzzer (Active Low mode)...")
    buzzer = Buzzer(14, active_low=True)
    
    try:
        # Initial state check
        print("Buzzer should be silent now.")
        time.sleep(0.5)

        print("\n[Mode 1] Playing Super Mario Theme...")
        
        # Super Mario Theme (Simplified)
        # Note, Duration (ms)
        mario_theme = [
            ('E5', 100), ('E5', 100), ('REST', 100), ('E5', 100), 
            ('REST', 100), ('C5', 100), ('E5', 100), ('REST', 100),
            ('G5', 100), ('REST', 300), ('G4', 100), ('REST', 300),
            
            ('C5', 150), ('REST', 50), ('G4', 150), ('REST', 150), 
            ('E4', 150), ('REST', 100), ('A4', 100), ('B4', 100), 
            ('AS4', 50), ('A4', 100), ('G4', 100), ('E5', 100), ('G5', 100), 
            ('A5', 100), ('F5', 100), ('G5', 100), ('REST', 50), 
            ('E5', 100), ('C5', 100), ('D5', 100), ('B4', 100)
        ]
        
        buzzer.play_melody(mario_theme, tempo=1.2)
        
        print("\n[Mode 2] Testing Simple Beep...")
        buzzer.beep(times=2, freq=2000, duration_ms=100, pause_ms=100)
        
        print("\nTest Complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        buzzer.quiet()

if __name__ == "__main__":
    test_buzzer()
