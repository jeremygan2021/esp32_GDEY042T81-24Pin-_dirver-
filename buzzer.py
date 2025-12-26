from machine import Pin, PWM
import time
try:
    import json
except ImportError:
    import ujson as json

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

# Song Library
SONGS = {
    1: {
        "name": "Super Mario Theme",
        "tempo": 1.2,
        "notes": [
            ('E5', 100), ('E5', 100), ('REST', 100), ('E5', 100), 
            ('REST', 100), ('C5', 100), ('E5', 100), ('REST', 100),
            ('G5', 100), ('REST', 300), ('G4', 100), ('REST', 300),
            ('C5', 150), ('REST', 50), ('G4', 150), ('REST', 150), 
            ('E4', 150), ('REST', 100), ('A4', 100), ('B4', 100), 
            ('AS4', 50), ('A4', 100), ('G4', 100), ('E5', 100), ('G5', 100), 
            ('A5', 100), ('F5', 100), ('G5', 100), ('REST', 50), 
            ('E5', 100), ('C5', 100), ('D5', 100), ('B4', 100)
        ]
    },
    2: {
        "name": "Star Wars - Imperial March",
        "tempo": 1.0,
        "notes": [
            ('A3', 500), ('A3', 500), ('A3', 500), ('F3', 350), ('C4', 150),
            ('A3', 500), ('F3', 350), ('C4', 150), ('A3', 1000),
            ('E4', 500), ('E4', 500), ('E4', 500), ('F4', 350), ('C4', 150),
            ('GS3', 500), ('F3', 350), ('C4', 150), ('A3', 1000)
        ]
    },
    3: {
        "name": "Nokia Ringtone",
        "tempo": 1.2,
        "notes": [
            ('E5', 150), ('D5', 150), ('FS4', 300), ('GS4', 300),
            ('CS5', 150), ('B4', 150), ('D4', 300), ('E4', 300),
            ('B4', 150), ('A4', 150), ('CS4', 300), ('E4', 300),
            ('A4', 600)
        ]
    },
    4: {
        "name": "Happy Birthday",
        "tempo": 1.0,
        "notes": [
            ('G4', 200), ('G4', 200), ('A4', 400), ('G4', 400), ('C5', 400), ('B4', 800),
            ('G4', 200), ('G4', 200), ('A4', 400), ('G4', 400), ('D5', 400), ('C5', 800),
            ('G4', 200), ('G4', 200), ('G5', 400), ('E5', 400), ('C5', 400), ('B4', 400), ('A4', 400),
            ('F5', 200), ('F5', 200), ('E5', 400), ('C5', 400), ('D5', 400), ('C5', 800)
        ]
    },
    5: {
        "name": "Jingle Bells",
        "tempo": 1.5,
        "notes": [
            ('E5', 200), ('E5', 200), ('E5', 400),
            ('E5', 200), ('E5', 200), ('E5', 400),
            ('E5', 200), ('G5', 200), ('C5', 200), ('D5', 200), ('E5', 800),
            ('F5', 200), ('F5', 200), ('F5', 200), ('F5', 200),
            ('F5', 200), ('E5', 200), ('E5', 200), ('E5', 100), ('E5', 100),
            ('E5', 200), ('D5', 200), ('D5', 200), ('E5', 200), ('D5', 400), ('G5', 400)
        ]
    },
    6: {
        "name": "Merry Christmas Mr. Lawrence (Sakamoto Style - Lyrical)",
        "tempo": 0.9,
        "legato": True,
        "notes": [
            # --- Intro / Motif (Deep & Resonant) ---
            ('DS5', 200), ('F5', 200), ('DS5', 200), ('AS4', 200), ('DS5', 800), # Theme A
            ('REST', 50),
            ('DS5', 200), ('F5', 200), ('DS5', 200), ('F5', 200), ('GS5', 200), ('F5', 800), # Theme B
            ('REST', 50),
            ('DS5', 200), ('F5', 200), ('DS5', 200), ('CS5', 200), ('AS4', 1000), # Theme C
            ('REST', 150),
            
            # Bridge (Gentle descent)
            ('CS5', 300), ('C5', 300), ('GS4', 300), ('F4', 300),
            ('REST', 300),

            # --- Main Melody (Legato & Emotional) ---
            ('DS5', 180), ('F5', 180), ('DS5', 180), ('AS4', 180), ('DS5', 1200), # Long sustain
            ('DS5', 180), ('F5', 180), ('DS5', 180), ('F5', 180), ('GS5', 180), ('F5', 1200),
            ('DS5', 180), ('F5', 180), ('DS5', 180), ('CS5', 180), ('AS4', 1500), # Emotional peak
            
            # Rapid Arpeggio / Run
            ('AS4', 100), ('C5', 100), ('CS5', 100), ('DS5', 100), ('F5', 100), ('FS5', 100), ('GS5', 100), ('AS5', 100),

            # --- High Octave (Ethereal) ---
            ('F6', 180), ('DS6', 180), ('F6', 180), ('AS5', 180), ('DS6', 1200),
            ('DS6', 180), ('F6', 180), ('DS6', 180), ('F6', 180), ('GS6', 180), ('F6', 1200),
            ('F6', 180), ('DS6', 180), ('F6', 180), ('CS6', 180), ('AS5', 1500),

            # --- Outro (Fading away) ---
            ('CS6', 400), ('C6', 400), ('GS5', 400), ('F5', 400),
            ('REST', 400),
            ('DS5', 600), ('CS5', 600), ('AS4', 2000), # Very long final note
            ('REST', 500)
        ]
    },
    61: {

       "name": "Merry Christmas Mr. Lawrence (Guqin Style - Slow & Emotional)",

    # 基础节拍设定为 600ms (相当于慢板 50 BPM)，让每个音符都充分延展

    "tempo": 1.0, 

    "notes": [

        # --- 第一句：起 (悠长) ---

        # 2(3)2 6 | 2 - 

        ('E5', 300), ('FS5', 300), ('E5', 600), ('B5', 600), 

        ('E5', 1200), # 长音，核心情感点

        ('REST', 600), # 留白呼吸

        

        # --- 第二句：承 (流动) ---

        # 2(3)2(3) | 5 3

        ('E5', 300), ('FS5', 300), ('E5', 300), ('FS5', 300), 

        ('A5', 600), ('FS5', 600),

        

        # --- 第三句：转 (变化) ---

        # 2(3)2 6 | 1 -

        ('E5', 300), ('FS5', 300), ('E5', 600), ('B5', 600),

        ('D5', 1200), # 另一个长音高点

        ('REST', 600), # 呼吸

        # 1 7(5) | 3 -

        ('D5', 600), ('CS5', 300), ('A5', 300),

        ('FS5', 1200), # 长音收束

        

        # --- 第四句：回 (再现) ---

        # 2(3)2 6 | 2 -

        ('E5', 300), ('FS5', 300), ('E5', 600), ('B5', 600),

        ('E5', 1200),

        ('REST', 600),

        # 2(3)2(3) | 5 3

        ('E5', 300), ('FS5', 300), ('E5', 300), ('FS5', 300), 

        ('A5', 600), ('FS5', 600),

        

        # --- 第五句：合 (余韵) ---

        # 2(3)2 1 | 6 - (低八度的6，增加厚重感)

        ('E5', 300), ('FS5', 300), ('E5', 600), ('D5', 600),

        ('B4', 1800), # 最后的超长余音

        ('REST', 600)

    ]

},
    62: {
        "name": "Merry Christmas Mr. Lawrence",
        "tempo": 1.0,
        "notes": [
            # --- 第一部分：序曲 (Measures 1-8) ---
            ('E5', 1200), ('E5', 1200), ('D5', 1200), ('D5', 1200), 
            ('C5', 1200), ('C5', 1200), ('A4', 1200), ('A4', 1200),

            # --- 第二部分：流动背景音 (Measures 9-16) ---
            ('E5', 200), ('D5', 200), ('E5', 200), ('A4', 200), ('E5', 200), ('D5', 200),
            ('E5', 200), ('D5', 200), ('E5', 200), ('A4', 200), ('E5', 200), ('D5', 200),
            ('D5', 200), ('C5', 200), ('D5', 200), ('B4', 200), ('D5', 200), ('C5', 200),
            ('G4', 200), ('C5', 200), ('D5', 200), ('B4', 200), ('D5', 200), ('C5', 200),

            # --- 第三部分：主旋律 (Measures 17-24) ---
            ('D5', 200), ('E5', 200), ('D5', 200), ('A4', 200), ('D5', 800), # 2-3-2-6-2--
            ('D5', 200), ('E5', 200), ('D5', 200), ('E5', 200), ('G5', 200), ('E5', 600), # 2-3-2-3-5-3
            ('D5', 200), ('E5', 200), ('D5', 200), ('C5', 200), ('A4', 800), # 2-3-2-1-6--
            ('C5', 400), ('B4', 200), ('G4', 200), ('E5', 800), # 1-7-5-3--
            
            # --- 第四部分：高八度变奏 (Measures 25-32) ---
            ('E6', 200), ('D6', 200), ('E6', 200), ('A5', 200), ('D6', 800),
            ('D6', 200), ('E6', 200), ('D6', 200), ('E6', 200), ('G6', 200), ('E6', 600),
            ('D6', 200), ('E6', 200), ('D6', 200), ('C6', 200), ('A5', 800),
            ('C6', 400), ('B5', 200), ('G5', 200), ('E6', 800),

            # --- 第五部分：快节奏切分音 (Measures 49-52) ---
            ('A5', 200), ('G5', 200), ('A5', 200), ('G5', 200), ('G5', 200), ('A5', 200), ('A5', 400), 
            ('A5', 200), ('G5', 200), ('A5', 200), ('G5', 200), ('G5', 200), ('A5', 200), ('G5', 200), ('F5', 400),
            ('E5', 200), ('D5', 200), ('E5', 200), ('D5', 200), ('D5', 200), ('E5', 400),
            ('E5', 200), ('D5', 200), ('E5', 200), ('D5', 200), ('D5', 200), ('E5', 400)
        ]
    },
    63: {
        "name": "Butterfly Love (Die Lian)",
        "tempo": 1.0,
        "notes": [
            # --- 前奏 (Measures 1-4) ---
            ('REST', 600), ('A4', 300), ('B4', 300), ('C5', 300), ('B4', 300), ('A4', 300), ('E4', 300), # 0 67 17 63
            ('REST', 600), ('A4', 300), ('B4', 300), ('C5', 300), ('B4', 300), ('A4', 300), ('E4', 300), # 0 67 17 63
            ('REST', 600), ('REST', 600), ('D4', 300), ('G4', 300), ('FS4', 300), ('D4', 300),         # 0 0 26 #42
            ('A5', 600), ('E5', 600), ('C5', 600), ('REST', 600),                                     # 6(高) 3(高) 1(高) 0

            # --- 主旋律 A 段 (Measures 6-9) ---
            ('E5', 300), ('E5', 300), ('E5', 300), ('D5', 300), ('E5', 1200),                         # 3 3 3 2 3 - -
            ('D5', 300), ('E5', 300), ('D5', 300), ('D5', 300), ('A4', 600), ('A4', 300), ('B4', 300), # 2 3 2 2 6 6 7
            ('C5', 600), ('REST', 600), ('D5', 300), ('C5', 300), ('B4', 600), ('A4', 300), ('G4', 300),# 1 - 2 1 7 6 5
            ('A4', 1800),                                                                              # 6 - - -

            # --- 主旋律 B 段 (Measures 10-13) ---
            ('A4', 300), ('E5', 300), ('E5', 300), ('D5', 300), ('E5', 900), ('A4', 300),              # 6 3 3 2 3. 6
            ('A4', 300), ('B4', 300), ('A4', 300), ('G4', 300), ('D4', 600), ('D4', 300), ('E4', 300), # 6 7 6 5 2 2 3
            ('F4', 600), ('REST', 600), ('G4', 300), ('F4', 300), ('E4', 300), ('REST', 300), ('D4', 300), ('C4', 300), # 4 - 5 4 3 2 1
            ('E4', 1800), ('E4', 300), ('E4', 300),                                                    # 3 - - 3 3

            # --- 副歌过渡 (Measures 14-17) ---
            ('A5', 600), ('REST', 300), ('B4', 300), ('A4', 300), ('G4', 600), ('E4', 300),            # 6 7 6 5. 3
            ('G4', 1200), ('REST', 600), ('G4', 300), ('G4', 300),                                     # 5 - - 5 5
            ('D4', 600), ('A4', 300), ('G4', 300), ('E4', 300), ('D4', 300), ('C4', 300),              # 2 6 5 3 2 1
            ('E4', 1800)                                                                               # 3 - - -
        ]
    },
    7: {
        "name": "Mac Startup (Classic Bong)",
        "tempo": 1.0,
        "notes": [
            ('C3', 100), ('G3', 100), ('C4', 100), ('E4', 800)  # 模仿经典的 C 大调和弦上升
        ]
    },
    8: {
        "name": "Mac Shutdown",
        "tempo": 1.0,
        "notes": [
            ('E4', 150), ('C4', 150), ('G3', 150), ('C3', 400)  # 开机音的反向序列
        ]
    },
    9: {
        "name": "Success / Alert (Glass)",
        "tempo": 1.0,
        "notes": [
            ('C6', 80), ('G6', 150)  # 清脆的高音
        ]
    },
    10: {
        "name": "Error (Basso/Sosumi)",
        "tempo": 1.0,
        "notes": [
            ('G2', 100), ('REST', 50), ('G2', 100)  # 低沉的两次短促响声
        ]
    },
    11: {
        "name": "Delete / Empty Trash",
        "tempo": 1.0,
        "notes": [
            ('E5', 50), ('C5', 50), ('G4', 50), ('C4', 100)  # 快速下降音，模拟物体掉落
        ]
    },
    12: {
        "name": "Question / Help",
        "tempo": 1.0,
        "notes": [
            ('C5', 100), ('E5', 100), ('G5', 200)  # 典型的询问式上升音阶
        ]
    },
    13: {
        "name": "Mac 'Hello' Intro (Long Startup)",
        "tempo": 0.8,
        "notes": [
            # 模拟从低沉到明亮的宽广感
            ('G3', 150), ('C4', 150), ('E4', 150), ('G4', 150), 
            ('C5', 400), ('REST', 100),
            # 后半段欢快的装饰音
            ('C5', 100), ('D5', 100), ('E5', 100), ('G5', 400)
        ]
    },
    14: {
        "name": "Finder Success (Complex Operation)",
        "tempo": 1.2,
        "notes": [
            # 一种任务圆满完成的跃动感
            ('C5', 80), ('E5', 80), ('G5', 80), ('C6', 200),
            ('REST', 50),
            ('G5', 80), ('C6', 300)
        ]
    },
    15: {
        "name": "Mac System Alert (Indigo Style)",
        "tempo": 1.0,
        "notes": [
            # 模仿 System 7 中那种带节奏的警告音
            ('A4', 100), ('E5', 100), ('REST', 50), 
            ('A4', 100), ('E5', 100), ('REST', 50),
            ('A4', 50), ('B4', 50), ('C5', 50), ('D5', 50), ('E5', 300)
        ]
    },
    16: {
        "name": "Classic Mac Game Over (Sad but Retro)",
        "tempo": 1.0,
        "notes": [
            # 模仿早期苹果游戏失败时的下行序列
            ('E5', 200), ('DS5', 200), ('D5', 200), ('CS5', 400),
            ('REST', 100),
            ('C5', 200), ('G4', 200), ('C4', 600)
        ]
    },
    20: {
        "name": "Mac Click (Standard)",
        "tempo": 1.0,
        "notes": [
            ('C7', 30)  # 极短的高频音，模拟物理按键反馈
        ]
    },
    21: {
        "name": "Mac Double Click",
        "tempo": 1.0,
        "notes": [
            ('C7', 20), ('REST', 30), ('C7', 20)  # 快速的双击声
        ]
    },
    22: {
        "name": "Mac Confirm (Enter)",
        "tempo": 1.0,
        "notes": [
            ('G5', 50), ('C6', 100)  # 向上跳跃的四度音，表示肯定
        ]
    },
    23: {
        "name": "Mac Cancel (Escape)",
        "tempo": 1.0,
        "notes": [
            ('C6', 50), ('G5', 100)  # 向下跳跃的四度音，表示取消/退出
        ]
    },
    24: {
        "name": "Mac Scroll / Tick",
        "tempo": 1.0,
        "notes": [
            ('E6', 15)  # 极短促，用于旋钮或列表滚动
        ]
    },
    25: {
        "name": "Mac Selection",
        "tempo": 1.0,
        "notes": [
            ('A5', 40), ('B5', 40), ('C6', 40)  # 快速上升的三连音
        ]
    },
    26: {
        "name": "Mac Modal Pop-up",
        "tempo": 1.0,
        "notes": [
            ('F5', 60), ('REST', 20), ('F5', 60)  # 经典的“咚咚”警告预备声
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
            # Using a non-linear mapping or just simple linear for now
            # Typically 50% duty is VERY loud. 1-5% is pleasant.
            # Let's map 100% volume -> 512 duty
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
        """Play a song by index (1-5)"""
        if index in SONGS:
            song = SONGS[index]
            print(f"Playing: {song['name']} (Vol: {self.volume}%)")
            completed = self.play_melody(song['notes'], song['tempo'], unstoppable=unstoppable)
            
            # If interrupted and NOT playing the Cancel sound (23), play Cancel sound
            if not completed and index != 23:
                print("Playback interrupted.")
                # Play Cancel/Escape sound
                self.play_song(23, unstoppable=True)
        else:
            print(f"Song index {index} not found. Please choose 1-{len(SONGS)}")

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
            print("\nAvailable Songs:")
            for k, v in SONGS.items():
                print(f"{k}. {v['name']}")
            
            try:
                choice = input(f"\nEnter song number (1-{len(SONGS)}) to play: ")
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


