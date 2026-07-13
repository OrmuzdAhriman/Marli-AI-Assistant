import subprocess
import requests

WHISPER = "/home/aprasovic/whisper.cpp/build/bin/whisper-cli"
MODEL = "/home/aprasovic/whisper.cpp/models/ggml-base.en.bin"

AUDIO = "input.wav"
OUT = "output.wav"

PIPER = "/home/aprasovic/ai-assistant/venv/bin/piper"
PIPER_MODEL = "/home/aprasovic/piper/en_US-lessac-medium.onnx"


def record():
    input("🎤 ENTER za snimanje (5 sec)...")

    subprocess.run([
        "arecord",
        "-D", "plughw:CARD=Device,DEV=0",
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
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:0.5b",
            "prompt": prompt,
            "stream": False
        }
    )

    ans = r.json()["response"]
    print("🤖 AI:", ans)
    return ans


def tts(text):
    subprocess.run(
        f'echo "{text}" | {PIPER} --model {PIPER_MODEL} --output_file {OUT}',
        shell=True
    )
    subprocess.run(["aplay", OUT])


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
