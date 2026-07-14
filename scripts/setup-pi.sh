#!/usr/bin/env bash
# setup-pi.sh — provision a fresh Raspberry Pi 5 for Marli, end to end.
# Mirrors the steps used to set up the first Pi (2026-07-14). Idempotent:
# already-installed pieces are detected and skipped. Big steps ask first.
# EN: run this on the Pi, inside the cloned repo:  ./scripts/setup-pi.sh
# BS: pokreni ovo na Pi-ju, unutar kloniranog repoa: ./scripts/setup-pi.sh
set -uo pipefail

ok()   { printf '✓ %s\n' "$*"; }
say()  { printf '▸ %s\n' "$*"; }
warn() { printf '! %s\n' "$*"; }
ask()  { printf '%s [y/N] ' "$1"; read -r a; [ "${a:-}" = "y" ] || [ "${a:-}" = "Y" ]; }

say "Marli Pi setup — whisper.cpp + Ollama + Piper + OLED. Ctrl-C anytime."

# --- 1. apt packages -------------------------------------------------------
say "1/6 apt packages (build tools, ALSA, I2C)…"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  git cmake build-essential libopenblas-dev wget curl i2c-tools python3-pip alsa-utils
ok "apt packages present"

# --- 2. whisper.cpp --------------------------------------------------------
if [ -x "$HOME/whisper.cpp/build/bin/whisper-cli" ]; then
  ok "whisper.cpp already built"
else
  if ask "2/6 Build whisper.cpp (~5 min on Pi 5)?"; then
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git "$HOME/whisper.cpp"
    cmake -S "$HOME/whisper.cpp" -B "$HOME/whisper.cpp/build" -DCMAKE_BUILD_TYPE=Release >/dev/null
    cmake --build "$HOME/whisper.cpp/build" -j"$(nproc)" --target whisper-cli
    ok "whisper.cpp built"
  fi
fi
if [ ! -f "$HOME/whisper.cpp/models/ggml-base.en.bin" ] && [ -d "$HOME/whisper.cpp" ]; then
  say "Downloading whisper model base.en (~141 MB)…"
  bash "$HOME/whisper.cpp/models/download-ggml-model.sh" base.en
fi
[ -f "$HOME/whisper.cpp/models/ggml-base.en.bin" ] && ok "whisper model present"

# --- 3. Ollama + LLM model -------------------------------------------------
if command -v ollama >/dev/null 2>&1; then
  ok "Ollama already installed ($(ollama --version 2>/dev/null | head -1))"
else
  # NOTE: this pipes the official install script into a root shell — standard
  # Ollama install, but it downloads and runs remote code. Skip if not comfortable.
  if ask "3/6 Install Ollama via the official script (runs remote code as root)?"; then
    curl -fsSL https://ollama.com/install.sh | sh
  fi
fi
if command -v ollama >/dev/null 2>&1 && ! ollama list 2>/dev/null | grep -q "qwen2.5:0.5b"; then
  say "Pulling qwen2.5:0.5b (~400 MB)…"
  ollama pull qwen2.5:0.5b
fi
command -v ollama >/dev/null 2>&1 && ok "Ollama + model ready"

# --- 4. Piper TTS ----------------------------------------------------------
if [ -x "$HOME/piper/piper" ]; then
  ok "Piper already installed"
else
  say "4/6 Installing Piper (prebuilt aarch64) + lessac voice…"
  wget -q "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz" -O /tmp/piper.tar.gz
  tar -xzf /tmp/piper.tar.gz -C "$HOME"
  BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
  wget -q "$BASE/en_US-lessac-medium.onnx"      -O "$HOME/piper/en_US-lessac-medium.onnx"
  wget -q "$BASE/en_US-lessac-medium.onnx.json" -O "$HOME/piper/en_US-lessac-medium.onnx.json"
  ok "Piper installed"
fi

# --- 5. Python deps + OLED I2C --------------------------------------------
say "5/6 Python deps (requests, luma.oled)…"
pip3 install --user --break-system-packages -q requests luma.oled && ok "python deps installed"
if [ "$(sudo raspi-config nonint get_i2c 2>/dev/null)" != "0" ]; then
  say "Enabling I2C for the OLED (persists across reboots)…"
  sudo raspi-config nonint do_i2c 0 && ok "I2C enabled"
else
  ok "I2C already enabled"
fi

# --- 6. Sanity checks ------------------------------------------------------
say "6/6 Sanity checks…"
[ -x "$HOME/whisper.cpp/build/bin/whisper-cli" ] && ok "whisper-cli" || warn "whisper-cli missing"
command -v ollama >/dev/null 2>&1 && curl -s -m 5 http://localhost:11434/api/tags >/dev/null && ok "ollama API" || warn "ollama API not responding"
[ -x "$HOME/piper/piper" ] && ok "piper" || warn "piper missing"
arecord -l 2>/dev/null | grep -q "^card" && ok "ALSA capture device found" || warn "no mic detected — plug in the headset"
/usr/sbin/i2cdetect -y 1 2>/dev/null | grep -q "3c" && ok "OLED found at 0x3c" || warn "OLED not detected on i2c-1 (check wiring, or it's fine if you have no display)"

echo
say "Done. Try it:   python3 push_to_talk.py    (headset on!)"
say "Face demo:      python3 face.py"
say "Git workflow:   ./scripts/marli doctor     (first time), then see CONTRIBUTING.md"
