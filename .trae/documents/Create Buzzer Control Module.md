I will create a standalone MicroPython module `buzzer.py` to control the MH-FMD buzzer.

The module will include a `Buzzer` class with the following features:
1.  **Support for both Passive and Active Buzzers**:
    -   `tone(freq, duration)`: Uses PWM to generate sound (ideal for Passive buzzers).
    -   `on()` / `off()`: Uses simple GPIO levels (ideal for Active buzzers).
    -   `beep(times, ...)`: A helper to beep multiple times.
2.  **Configuration**: It will accept the pin number (14 as requested) during initialization.
3.  **Self-Test**: The file will include a `test_buzzer()` function that runs if the file is executed directly, allowing you to verify the buzzer immediately.

**Steps:**
1.  Create `buzzer.py` with the `Buzzer` class and test logic.
2.  (Optional) If you wish, I can also add the buzzer pin definition to your `config.py` for consistency with your other modules, but I will keep the `buzzer.py` standalone as requested first.
