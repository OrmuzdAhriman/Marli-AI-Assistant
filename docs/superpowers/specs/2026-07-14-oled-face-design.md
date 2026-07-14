# Animated OLED Face — Design

**Date:** 2026-07-14
**Status:** Approved
**Author:** Senad + Claude

## Purpose

Give Marley a visible face on the 128×32 SSD1306 OLED (I2C `0x3c`, `/dev/i2c-1`) that reacts to the assistant's state in real time: calm when idle, attentive while listening, busy while thinking, and mouth-flapping while it speaks — synchronized to the actual `push_to_talk.py` pipeline.

## Hardware

- SSD1306 OLED, 128×32, I2C address `0x3c` on `/dev/i2c-1` (GPIO header pins 3/5). I2C enabled + persisted.
- Runs on Senad's Pi 5 (`sosmic@`), Debian 12, Python 3.11.

## Dependency

- **`luma.oled`** — the single standard library for driving an SSD1306 over I2C with PIL image buffers. One package for one concern (justified addition to the otherwise stdlib+`requests` project).

## Architecture — threaded `Face` module

A new `face.py` owns everything about the display. The voice pipeline only flips a shared state string; a background render thread draws the matching animation. This decouples animation timing from the pipeline's blocking calls (record, inference, playback).

```
face = Face()          # opens the OLED; no-ops if the panel is absent
face.start()           # spawns the render thread (~20 fps loop)
face.set_state("listening")   # thread-safe; render loop picks it up next frame
...
face.set_state("speaking")    # before aplay
   aplay (blocks for the audio's real length)
face.set_state("idle")        # after aplay → mouth stops exactly on cue
face.stop()            # on exit: stop thread, blank/close the panel
```

### Interfaces

- `Face(i2c_port=1, address=0x3c, width=128, height=32)` — constructor. If the device can't be opened, sets an internal `enabled=False` and every method becomes a no-op (voice pipeline still works headless).
- `Face.start()` — start the render thread.
- `Face.set_state(state: str)` — one of `"idle" | "listening" | "thinking" | "speaking"`. Thread-safe (guarded by a lock). Unknown state falls back to `"idle"`.
- `Face.stop()` — stop the thread, clear the display, release the device.
- Internal per-state draw functions render onto a `PIL.Image` (mode "1"); the render loop advances an animation frame counter so motion is time-based, not tied to state changes.

### The sync mechanism

`speaking` is entered immediately before `aplay` and left immediately after `aplay` returns. Because `aplay` blocks for exactly the WAV's duration, the mouth flaps for precisely the speech duration with zero timing math or drift. (This is the "flap for audio duration" decision.)

## States & visuals (128×32, eyes upper ~y3–18, mouth lower ~y22–30)

| State | Trigger in pipeline | Animation |
|---|---|---|
| **idle** | waiting for ENTER (default state) | two open eyes (filled rounded rects/circles), mouth a short flat line; a blink every ~4s (eyes collapse to a 2px line for ~120ms) |
| **listening** | during `record()` (arecord) | eyes "breathe" — radius/height oscillates gently (~1.5 Hz), mouth flat; reads as attentive |
| **thinking** | during `whisper()` + `ollama()` | eyes shift up (looking up), and `.`/`..`/`...` dots cycle in the mouth row (~3 Hz) |
| **speaking** | during `tts()` while `aplay` runs | eyes open steady; mouth = ellipse whose height opens/closes in a talk loop (~6–8 Hz) |

All drawing uses simple PIL primitives (ellipse, rounded_rectangle, line, text) — cheap enough for 20 fps over I2C (a 128×32 mono frame is 512 bytes).

## Integration

- `push_to_talk.py`: construct `Face`, `start()` once; `set_state` around each stage; `stop()` in a `finally` so the panel clears on exit/Ctrl-C. State map: idle (loop top) → listening (record) → thinking (whisper+ollama) → speaking (tts/aplay) → idle.
- `marley_wakeup.py`: same `Face`, reused — idle while looping, listening during record, thinking/speaking on activation. (Wire-up mirrors push_to_talk; included so both entrypoints share one face.)
- `face.py` standalone demo: `python3 face.py` cycles idle→listening→thinking→speaking on the real display (~3s each) to verify driver + layout before pipeline wiring.

## Error handling / degradation

- Missing panel, disabled I2C, or `luma.oled` import failure → `Face.enabled=False`, all methods no-op, a one-line warning printed once. The voice assistant must never crash because of the display.
- `stop()` always clears the screen (no burned-in last frame) and is called from a `finally`.

## Out of scope (YAGNI)

Real amplitude lip-sync, multiple facial expressions/emotions, scrolling the transcript text, brightness/animation config files. Revisit only if asked.

## Success criteria

1. `python3 face.py` shows all four states animating correctly on the 128×32 panel.
2. Running `push_to_talk.py`: face is idle at the prompt, pulses while recording, shows thinking during transcription+LLM, and the mouth flaps for exactly the spoken reply, returning to idle after.
3. Unplugging/disabling the OLED does not break the voice pipeline.
4. Exiting the program clears the display.

## Testing approach

- Standalone: run `face.py` demo on the Pi, watch the panel cycle states.
- Integrated: run `push_to_talk.py` on the Pi, speak a turn, confirm each state matches the pipeline stage and the mouth stops when audio stops.
- Degradation: temporarily point `Face` at a wrong address; confirm it no-ops and the pipeline still records/replies.
