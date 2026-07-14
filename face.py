"""Animated face for Marley on a 128x32 SSD1306 OLED.

Degrades to a silent no-op if the panel or luma.oled is unavailable, so the
voice pipeline never breaks. Import Face; call start(), set_state(...), stop().
"""
import math
import threading
import time

STATES = ("idle", "listening", "thinking", "speaking")

# Layout for 128x32: two eyes up top, mouth row below.
_EYE_Y = 11          # eye vertical center
_EYE_R = 6           # base eye radius
_LEFT_X = 40         # left eye center x
_RIGHT_X = 88        # right eye center x
_MOUTH_Y = 25        # mouth vertical center


def _open_device(i2c_port, address, width, height):
    """Return a luma device, or None if unavailable."""
    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306
        return ssd1306(i2c(port=i2c_port, address=address), width=width, height=height)
    except Exception as e:  # missing lib, no panel, I2C off, wrong address
        print(f"[face] display unavailable ({e}); running without a face.")
        return None


class Face:
    def __init__(self, i2c_port=1, address=0x3C, width=128, height=32, fps=20):
        self.width = width
        self.height = height
        self._interval = 1.0 / fps
        self._device = _open_device(i2c_port, address, width, height)
        self.enabled = self._device is not None
        self._state = "idle"
        self._lock = threading.Lock()
        self._thread = None
        self._running = False
        self._frame = 0

    @property
    def state(self):
        with self._lock:
            return self._state

    def set_state(self, state):
        if state not in STATES:
            state = "idle"
        with self._lock:
            self._state = state

    def start(self):
        if not self.enabled or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if self.enabled:
            try:
                self._device.clear()
            except Exception:
                pass

    def _loop(self):
        from luma.core.render import canvas
        while self._running:
            state = self.state
            with canvas(self._device) as draw:
                _draw_state(draw, state, self._frame, self.width, self.height)
            self._frame += 1
            time.sleep(self._interval)


def _eye(draw, cx, cy, rx, ry):
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)


def _draw_idle(draw, frame, w, h):
    # Blink ~every 4s: at 20fps that's every 80 frames, blink for ~3 frames.
    blinking = (frame % 80) < 3
    ry = 1 if blinking else _EYE_R
    _eye(draw, _LEFT_X, _EYE_Y, _EYE_R, ry)
    _eye(draw, _RIGHT_X, _EYE_Y, _EYE_R, ry)
    draw.line((_LEFT_X, _MOUTH_Y, _RIGHT_X, _MOUTH_Y), fill=255)  # calm flat mouth


def _draw_listening(draw, frame, w, h):
    # Eyes "breathe": radius oscillates ~1.5Hz.
    pulse = (math.sin(frame / 20.0 * 2 * math.pi * 1.5) + 1) / 2  # 0..1
    r = _EYE_R + int(round(pulse * 2))
    _eye(draw, _LEFT_X, _EYE_Y, r, r)
    _eye(draw, _RIGHT_X, _EYE_Y, r, r)
    draw.line((_LEFT_X, _MOUTH_Y, _RIGHT_X, _MOUTH_Y), fill=255)


def _draw_thinking(draw, frame, w, h):
    # Eyes look up (smaller, raised); dots cycle 0..3.
    ey = _EYE_Y - 3
    _eye(draw, _LEFT_X, ey, _EYE_R, _EYE_R - 2)
    _eye(draw, _RIGHT_X, ey, _EYE_R, _EYE_R - 2)
    dots = (frame // 6) % 4
    draw.text((_LEFT_X - 6, _MOUTH_Y - 4), "." * dots, fill=255)


def _draw_speaking(draw, frame, w, h):
    _eye(draw, _LEFT_X, _EYE_Y, _EYE_R, _EYE_R)
    _eye(draw, _RIGHT_X, _EYE_Y, _EYE_R, _EYE_R)
    # Mouth flaps ~7Hz: height oscillates 1..6 px.
    flap = (math.sin(frame / 20.0 * 2 * math.pi * 7) + 1) / 2  # 0..1
    mh = 1 + int(round(flap * 5))
    cx = (_LEFT_X + _RIGHT_X) // 2
    draw.ellipse((cx - 14, _MOUTH_Y - mh, cx + 14, _MOUTH_Y + mh), outline=255, fill=255)


def _draw_state(draw, state, frame, w, h):
    if state == "listening":
        _draw_listening(draw, frame, w, h)
    elif state == "thinking":
        _draw_thinking(draw, frame, w, h)
    elif state == "speaking":
        _draw_speaking(draw, frame, w, h)
    else:
        _draw_idle(draw, frame, w, h)


if __name__ == "__main__":
    # Cycle every state on the real panel for a quick visual check.
    f = Face()
    f.start()
    try:
        for st in ("idle", "listening", "thinking", "speaking"):
            print(f"[face] demo: {st}")
            f.set_state(st)
            time.sleep(3)
    finally:
        f.stop()
