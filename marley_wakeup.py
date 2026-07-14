import os
import subprocess
from pathlib import Path

import requests

from face import Face

HOME = str(Path.home())

# Binaries / models — per-machine layout; override via env if yours differs.
WHISPER = os.environ.get("MARLEY_WHISPER", f"{HOME}/whisper.cpp/build/bin/whisper-cli")
MODEL = os.environ.get("MARLEY_WHISPER_MODEL", f"{HOME}/whisper.cpp/models/ggml-base.en.bin")
PIPER = os.environ.get("MARLEY_PIPER", f"{HOME}/piper/piper")
PIPER_MODEL = os.environ.get("MARLEY_PIPER_MODEL", f"{HOME}/piper/en_US-lessac-medium.onnx")

# Audio (ALSA). Find yours with `arecord -L` / `aplay -L`.
MIC = os.environ.get("MARLEY_MIC", "plughw:CARD=Headset,DEV=0")
SPEAKER = os.environ.get("MARLEY_SPEAKER", "plughw:CARD=Headset,DEV=0")

# Ollama
OLLAMA_MODEL = os.environ.get("MARLEY_MODEL", "qwen2.5:0.5b")
OLLAMA_URL = os.environ.get("MARLEY_OLLAMA_URL", "http://localhost:11434/api/generate")

AUDIO = "input.wav"
OUT = "output.wav"


def record():
    subprocess.run([
        "arecord",
        "-D", MIC,
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        "-d", "5",
        AUDIO
    ])


def whisper():
    result = subprocess.run([
        WHISPER,
        "-m", MODEL,
        "-f", AUDIO
    ], capture_output=True, text=True)

    return result.stdout.lower()


def ollama(prompt):
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
    )
    return r.json()["response"]


def tts(text):
    subprocess.run(
        [PIPER, "--model", PIPER_MODEL, "--output_file", OUT],
        input=text.encode()
    )
    subprocess.run(["aplay", "-D", SPEAKER, OUT])


def main():
    print("\n🔵 MARLEY WAKE MODE\n")
    face = Face()
    face.start()
    try:
        while True:
            face.set_state("listening")
            record()

            face.set_state("thinking")
            text = whisper()
            print("🧠 HEARD:", text)

            if "marley wake up" in text:
                print("🔥 ACTIVATED")
                answer = ollama(text)
                face.set_state("speaking")
                tts(answer)
            face.set_state("idle")
    finally:
        face.stop()


if __name__ == "__main__":
    main()
