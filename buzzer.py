from machine import Pin, PWM
import time
try:
    import json
except ImportError:
    import ujson as json
import gc
import sys

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

# Song Library (System Sounds only - Long songs moved to songs_lib.py to save RAM)
SONGS = {
    7: {
        "name": "Mac Startup (Classic Bong)",
        "tempo": 1.0,
        "notes": [
            ('C3', 100), ('G3', 100), ('C4', 100), ('E4', 800)
        ]
    },
    8: {
        "name": "Mac Shutdown",
        "tempo": 1.0,
        "notes": [
            ('E4', 150), ('C4', 150), ('G3', 150), ('C3', 400)
        ]
    },
    9: {
        "name": "Success / Alert (Glass)",
        "tempo": 1.0,
        "notes": [
            ('C6', 80), ('G6', 150)
        ]
    },
    10: {
        "name": "Error (Basso/Sosumi)",
        "tempo": 1.0,
        "notes": [
            ('G2', 100), ('REST', 50), ('G2', 100)
        ]
    },
    11: {
        "name": "Delete / Empty Trash",
        "tempo": 1.0,
        "notes": [
            ('E5', 50), ('C5', 50), ('G4', 50), ('C4', 100)
        ]
    },
    12: {
        "name": "Question / Help",
        "tempo": 1.0,
        "notes": [
            ('C5', 100), ('E5', 100), ('G5', 200)
        ]
    },
    13: {
        "name": "Mac 'Hello' Intro (Long Startup)",
        "tempo": 0.8,
        "notes": [
            ('G3', 150), ('C4', 150), ('E4', 150), ('G4', 150), 
            ('C5', 400), ('REST', 100),
            ('C5', 100), ('D5', 100), ('E5', 100), ('G5', 400)
        ]
    },
    14: {
        "name": "Finder Success (Complex Operation)",
        "tempo": 1.2,
        "notes": [
            ('C5', 80), ('E5', 80), ('G5', 80), ('C6', 200),
            ('REST', 50),
            ('G5', 80), ('C6', 300)
        ]
    },
    15: {
        "name": "Mac System Alert (Indigo Style)",
        "tempo": 1.0,
        "notes": [
            ('A4', 100), ('E5', 100), ('REST', 50), 
            ('A4', 100), ('E5', 100), ('REST', 50),
            ('A4', 50), ('B4', 50), ('C5', 50), ('D5', 50), ('E5', 300)
        ]
    },
    16: {
        "name": "Classic Mac Game Over (Sad but Retro)",
        "tempo": 1.0,
        "notes": [
            ('E5', 200), ('DS5', 200), ('D5', 200), ('CS5', 400),
            ('REST', 100),
            ('C5', 200), ('G4', 200), ('C4', 600)
        ]
    },
    20: {
        "name": "Mac Click (Standard)",
        "tempo": 1.0,
        "notes": [
            ('C7', 30)
        ]
    },
    21: {
        "name": "Mac Double Click",
        "tempo": 1.0,
        "notes": [
            ('C7', 20), ('REST', 30), ('C7', 20)
        ]
    },
    22: {
        "name": "Mac Confirm (Enter)",
        "tempo": 1.0,
        "notes": [
            ('G5', 50), ('C6', 100)
        ]
    },
    23: {
        "name": "Mac Cancel (Escape)",
        "tempo": 1.0,
        "notes": [
            ('C6', 50), ('G5', 100)
        ]
    },
    24: {
        "name": "Mac Scroll / Tick",
        "tempo": 1.0,
        "notes": [
            ('E6', 15)
        ]
    },
    25: {
        "name": "Mac Selection",
        "tempo": 1.0,
        "notes": [
            ('A5', 40), ('B5', 40), ('C6', 40)
        ]
    },
    26: {
        "name": "Mac Modal Pop-up",
        "tempo": 1.0,
        "notes": [
            ('F5', 60), ('REST', 20), ('F5', 60)
        ]
    },
    27: {
        "name": "Processing / Loading",
        "tempo": 1.5,
        "notes": [
            ('C5', 50), ('REST', 50), ('E5', 50), ('REST', 50), 
            ('G5', 50), ('REST', 50), ('C6', 50), ('REST', 50)
        ]
    }
}

class Buzzer:
    def __init__(self, pin_num, active_low=True, volume=10):
        """
        Initialize the Buzzer.
        pin_num: GPIO pin number
        active_low: True if buzzer is Low Level Triggered (default), False if High Level
        volume: Volume percentage (0-100), default 10 (recommended for passive buzzers)
        """
        self.pin_num = pin_num
        self.active_low = active_low
        self.volume = volume
        self.pwm = None
        
        # Initialize as regular IO first
        self.pin = Pin(pin_num, Pin.OUT)
        
        # Ensure it's OFF initially
        initial_state = 1 if active_low else 0
        self.pin.value(initial_state)
        
        self._stop_flag = False

    def stop(self):
        """Stop current playback"""
        self._stop_flag = True
        self.quiet()

    def set_volume(self, volume):
        """Set volume percentage (0-100)"""
        self.volume = max(0, min(100, volume))

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

    def tone(self, freq=1000, duration_ms=None, duty=None):
        """
        Play a tone using PWM (For Passive Buzzer or Variable Active)
        freq: Frequency in Hz
        duration_ms: Duration in milliseconds (optional, blocking if set)
        duty: Duty cycle (0-1023). If None, calculated from volume.
        """
        if freq == 0:
            self.quiet()
            if duration_ms:
                time.sleep_ms(duration_ms)
            return

        self._ensure_pwm()
        self.pwm.freq(freq)
        
        # Calculate duty cycle from volume if not specified
        if duty is None:
            # Volume 0-100 maps to Duty 0-512 (50% duty is max volume for square wave)
            target_duty = int((self.volume / 100) * 512)
            self.pwm.duty(target_duty)
        else:
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
        val = 0 if self.active_low else 1
        self.pin.value(val)

    def off(self):
        """Turn OFF (Silence)"""
        self._ensure_pin()
        val = 1 if self.active_low else 0
        self.pin.value(val)

    def beep(self, times=1, freq=1000, duration_ms=100, pause_ms=100):
        """
        Beep multiple times
        """
        self._stop_flag = False
        for i in range(times):
            if self._stop_flag: break
            self.tone(freq, duration_ms)
            if i < times - 1:
                self._sleep_interruptible(pause_ms)
    
    def _sleep_interruptible(self, ms):
        """Sleep for ms milliseconds, but wake up if stop flag is set"""
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < ms:
            if self._stop_flag:
                return
            time.sleep_ms(10)

    def play_melody(self, melody, tempo=1.0, unstoppable=False):
        """
        Play a melody defined by a list of (note_name, note_duration)
        Returns True if completed, False if interrupted.
        """
        self._stop_flag = False
        for note_name, duration in melody:
            if not unstoppable and self._stop_flag:
                self.quiet()
                return False
                
            freq = NOTES.get(note_name, 0)
            duration_ms = int(duration * tempo)
            
            if freq > 0:
                self.tone(freq, duration_ms=None) # Start sound (non-blocking)
            else:
                self.quiet() # Rest
                
            # Wait for note duration
            if unstoppable:
                time.sleep_ms(duration_ms)
            else:
                self._sleep_interruptible(duration_ms)
            
            if not unstoppable and self._stop_flag:
                self.quiet()
                return False
            
            self.quiet() # Stop note
            
            # Tiny pause between notes for articulation
            pause_ms = int(20 * tempo)
            if unstoppable:
                time.sleep_ms(pause_ms)
            else:
                self._sleep_interruptible(pause_ms)
            
        return True

    def play_song(self, index, unstoppable=False):
        """Play a song by index"""
        song = None
        
        # 1. Try local SONGS (short effects)
        if index in SONGS:
            song = SONGS[index]
        
        # 2. Try external library (long songs)
        else:
            try:
                import songs_lib
                if index in songs_lib.SONGS_EXT:
                    song = songs_lib.SONGS_EXT[index]
            except ImportError:
                print("songs_lib not found")

        if song:
            print(f"Playing: {song['name']} (Vol: {self.volume}%)")
            completed = self.play_melody(song['notes'], song['tempo'], unstoppable=unstoppable)
            
            # If interrupted and NOT playing the Cancel sound (23), play Cancel sound
            if not completed and index != 23:
                print("Playback interrupted.")
                # Play Cancel/Escape sound
                self.play_song(23, unstoppable=True)
            
            # 尝试在播放完大歌曲后清理内存
            if index not in SONGS:
                if 'songs_lib' in sys.modules:
                    del sys.modules['songs_lib']
                gc.collect()
        else:
            print(f"Song index {index} not found.")

    def play_from_json(self, json_data):
        """
        Play a song from JSON data (string or dict).
        Example JSON: {"name": "Test", "tempo": 1.0, "notes": [["C4", 500], ["E4", 500]]}
        """
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except ValueError:
                print("Error: Invalid JSON string")
                return
        else:
            data = json_data

        if not isinstance(data, dict):
            print("Error: Invalid data format, expected dict or JSON string")
            return

        name = data.get("name", "JSON Song")
        tempo = data.get("tempo", 1.0)
        notes = data.get("notes", [])

        print(f"Playing: {name} (Vol: {self.volume}%)")
        self.play_melody(notes, tempo)

    # -------------------------------------------------------------------------
    # Semantic Sound Methods
    # -------------------------------------------------------------------------
    def play_startup(self):
        """Play startup sound (Song #13: Mac 'Hello')"""
        self.play_song(13, unstoppable=True)

    def play_shutdown(self):
        """Play shutdown sound (Song #8: Mac Shutdown)"""
        self.play_song(8, unstoppable=True)

    def play_success(self):
        """Play success sound (Song #9: Success / Alert)"""
        self.play_song(9, unstoppable=True)

    def play_error(self):
        """Play error sound (Song #10: Error)"""
        self.play_song(10, unstoppable=True)

    def play_click(self):
        """Play a short click sound"""
        self.tone(1000, 20) # 1kHz, 20ms

    def play_wifi_connected(self):
        """Play WiFi connected sound (Song #14: Finder Success)"""
        self.play_song(14, unstoppable=True)
        
    def play_wifi_fail(self):
        """Play WiFi failure sound (Song #15: System Alert)"""
        self.play_song(15, unstoppable=True)

    def play_process_async(self):
        """Play processing sound asynchronously (Song #27)"""
        self.play_song_async(27, unstoppable=True)

    def play_song_async(self, index, unstoppable=False):
        """Play a song in a separate thread"""
        try:
            import _thread
            _thread.start_new_thread(self.play_song, (index, unstoppable))
        except ImportError:
            print("Warning: _thread module not found, playing synchronously")
            self.play_song(index, unstoppable=unstoppable)
        except Exception as e:
            print(f"Error starting thread: {e}")

# -------------------------------------------------------------------------
# Global Instance
# -------------------------------------------------------------------------
try:
    import config
    # Initialize global buzzer instance
    # Use pin from config, default to 14 if not found
    _pin = getattr(config, 'buzzer_pin', 14)
    system_buzzer = Buzzer(_pin, active_low=True, volume=50)
except Exception as e:
    print(f"Warning: Could not initialize system_buzzer: {e}")
    system_buzzer = None


# -------------------------------------------------------------------------
# Test Function
# -------------------------------------------------------------------------
def test_buzzer(song_index=None):
    try:
        import config
        pin = config.buzzer_pin
    except ImportError:
        pin = 14
        
    print(f"=== Testing Buzzer on Pin {pin} ===")
    
    # Initialize Buzzer
    # Use global system_buzzer if available to ensure interrupts work
    if system_buzzer:
        buzzer = system_buzzer
        print("Using global system_buzzer instance")
    else:
        buzzer = Buzzer(pin, active_low=True, volume=50)
        print("Created local Buzzer instance")
    
    try:
        # Initial state check
        buzzer.quiet()
        time.sleep(0.5)

        if song_index is not None:
            # Play specific song
            buzzer.play_song(song_index)
        else:
            # Interactive mode or Default
            print("\nAvailable Songs (System):")
            for k, v in SONGS.items():
                print(f"{k}. {v['name']}")
            
            print("\nExternal Songs (may require more RAM):")
            print("1-6, 61-63")

            try:
                choice = input(f"\nEnter song number to play: ")
                idx = int(choice)
                buzzer.play_song(idx)
            except (ValueError, OSError):
                # If input fails (e.g. non-interactive), play Mario by default
                print("\nNo input detected, playing Song #1 (Mario)...")
                buzzer.play_song(1)
        
        print("\nTest Complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        buzzer.quiet()

if __name__ == "__main__":
    test_buzzer()
