import os
import subprocess
from pathlib import Path

import requests

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
    input("🎤 ENTER za snimanje (5 sec)...")

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

    text = result.stdout.strip()
    print("🧠 TI:", text)
    return text


def ollama(prompt):
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    ans = r.json()["response"]
    print("🤖 AI:", ans)
    return ans


def tts(text):
    subprocess.run(
        [PIPER, "--model", PIPER_MODEL, "--output_file", OUT],
        input=text.encode()
    )
    subprocess.run(["aplay", "-D", SPEAKER, OUT])


def main():
    print("\n🟢 PUSH TO TALK MODE\n")

    while True:
        record()

        text = whisper()
        if not text:
            continue

        if "exit" in text.lower():
            break

        answer = ollama(text)
        tts(answer)


if __name__ == "__main__":
    main()
