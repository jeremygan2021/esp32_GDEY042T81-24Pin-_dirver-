The buzzer is continuously sounding because the module is likely **Low Level Triggered** (Active Low). This means sending a `0` (Low) signal turns it ON, and `1` (High) turns it OFF. My previous code initialized it to `0`, which caused it to sound immediately.

I will update `buzzer.py` to:

1. Add an `active_low` parameter to the `Buzzer` class (defaulting to `True` to fix your issue).
2. Initialize the pin to `1` (High) so it starts silently.
3. Update `on()` and `off()` methods to respect the active-low logic.

   * `on()` -> sends `0`

   * `off()` -> sends `1`

