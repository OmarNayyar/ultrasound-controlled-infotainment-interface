"""Serial input adapter for the Arduino / ultrasonic gesture controller."""

import serial


class SerialGestureReader:
    """Reads gesture labels from a serial device and forwards them to a callback."""

    VALID_GESTURES = {"SWIPE_LEFT", "SWIPE_RIGHT", "PUSH", "PULL"}

    def __init__(self, port="COM4", baudrate=9600, callback=None):
        self.callback = callback
        self.port_name = port
        self.baudrate = baudrate
        self.ser = None

        try:
            self.ser = serial.Serial(self.port_name, self.baudrate, timeout=0.01)
            print(f"[SerialGestureReader] Opened {self.port_name} @ {self.baudrate}")
        except Exception as exc:
            print(f"[SerialGestureReader] Could not open {self.port_name}: {exc}")
            self.ser = None

    def poll(self):
        """Non-blocking poll method intended for a Qt timer."""
        if self.ser is None:
            return

        try:
            while self.ser.in_waiting:
                raw = self.ser.readline().decode(errors="ignore").strip()
                if not raw:
                    continue

                line = raw.upper()
                if line.startswith("GESTURE:"):
                    gesture = line.split(":", 1)[1].strip()
                else:
                    gesture = line

                if gesture in self.VALID_GESTURES:
                    print(f"[SerialGestureReader] Gesture from serial: {gesture}")
                    if self.callback:
                        self.callback(gesture)
        except Exception as exc:
            print(f"[SerialGestureReader] Error: {exc}")
