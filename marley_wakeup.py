import subprocess
import requests

WHISPER = "/home/aprasovic/whisper.cpp/build/bin/whisper-cli"
MODEL = "/home/aprasovic/whisper.cpp/models/ggml-base.en.bin"

AUDIO = "input.wav"
OUT = "output.wav"

PIPER = "/home/aprasovic/ai-asistant/venv/bin/piper"
PIPER_MODEL = "/home/aprasovic/piper/en_US-lessac-medium.onnx"


def record():
    subprocess.run([
        "arecord",
        "-D", "hw:2,0",
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
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:0.5b",
            "prompt": prompt,
            "stream": False
        }
    )
    return r.json()["response"]


def tts(text):
    subprocess.run(
        f'echo "{text}" | {PIPER} --model {PIPER_MODEL} --output_file {OUT}',
        shell=True
    )
    subprocess.run(["aplay", OUT])


def main():
    print("\n🔵 MARLEY WAKE MODE\n")

    while True:
        record()

        text = whisper()
        print("🧠 HEARD:", text)

        if "marley wake up" in text:
            print("🔥 ACTIVATED")

            answer = ollama(text)
            tts(answer)


if __name__ == "__main__":
    main()
