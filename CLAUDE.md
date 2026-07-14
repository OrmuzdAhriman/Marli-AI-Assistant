# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Start here

- Open tasks: `docs/TASKS.md` (read first every session). Running log: `docs/JOURNAL.md`.
- Full project handbook: `docs/HANDBOOK.en.md` / `docs/HANDBOOK.bs.md` (keep both in sync — see the `marli-docs` skill).
- Git work goes through the `marli` CLI (`scripts/marli`) — see the `marli-git-workflow` skill. `main` is production; PRs only.

## What this is

A local, offline voice assistant ("Marley") that runs entirely on-device via a Linux host. There is no cloud API — every stage is a local process/binary. Despite the repo being checked out on Windows, the code targets Linux (ALSA audio, `/home/aprasovic/...` paths) and must be run there (e.g. a Raspberry Pi / Linux box).

## Pipeline architecture

Both scripts implement the same four-stage loop; they differ only in how a turn is triggered:

1. **Record** → `arecord` (ALSA) captures 5s of 16 kHz mono S16_LE WAV to `input.wav`.
2. **STT** → `whisper-cli` (whisper.cpp, `ggml-base.en` model) transcribes the WAV to text.
3. **LLM** → HTTP POST to a local **Ollama** server at `localhost:11434`, model `qwen2.5:0.5b`, `stream: False`.
4. **TTS** → pipe the response text through **Piper** (`en_US-lessac-medium.onnx`) to `output.wav`, then play via `aplay`.

`requests` is the only Python dependency. Everything else (`arecord`, `aplay`, `whisper-cli`, `piper`, `ollama`) is an external binary the pipeline shells out to.

## The two entrypoints

- **`push_to_talk.py`** — blocks on `input()` (press ENTER) before each recording; exits when transcription contains "exit". Interactive, manual-trigger.
- **`marley_wakeup.py`** — records continuously in a loop and only proceeds to LLM+TTS when the transcript contains the wake phrase `"marley wake up"`. Hands-free.

## Running

```bash
python push_to_talk.py     # manual push-to-talk
python marley_wakeup.py    # wake-word listening
```

Prerequisites that must already be installed and running on the host:
- Ollama serving the model on `localhost:11434` (`ollama pull qwen2.5:0.5b`)
- whisper.cpp built at `~/whisper.cpp/build/bin/whisper-cli`, with `~/whisper.cpp/models/ggml-base.en.bin`
- Piper (prebuilt aarch64 binary) at `~/piper/piper`, with `~/piper/en_US-lessac-medium.onnx`
- ALSA (`arecord`/`aplay`) with a working capture + playback device

There is no build step, no test suite, and no linter configured.

## Per-machine configuration

Both scripts read their paths and audio devices from environment variables with `~`-relative defaults, so the same code runs unchanged on any user's Pi as long as the default install layout is used. Override any of these in the shell/env if your layout differs:

| Env var | Default |
|---|---|
| `MARLEY_WHISPER` | `~/whisper.cpp/build/bin/whisper-cli` |
| `MARLEY_WHISPER_MODEL` | `~/whisper.cpp/models/ggml-base.en.bin` |
| `MARLEY_PIPER` | `~/piper/piper` |
| `MARLEY_PIPER_MODEL` | `~/piper/en_US-lessac-medium.onnx` |
| `MARLEY_MIC` / `MARLEY_SPEAKER` | `plughw:CARD=Headset,DEV=0` |
| `MARLEY_MODEL` | `qwen2.5:0.5b` |
| `MARLEY_OLLAMA_URL` | `http://localhost:11434/api/generate` |

Find your ALSA device names with `arecord -L` / `aplay -L` (numeric `plughw:2,0` also works but card numbers can shuffle across reboots, so the `CARD=<name>` form is preferred).

## Gotchas when editing

- **The scripts assume a fixed install layout** (`~/whisper.cpp`, `~/piper`). If a Pi installs elsewhere, set the env vars above rather than editing the source.
- `tts()` pipes the LLM text to Piper via `subprocess` stdin (no shell), so response text needs no escaping — do not reintroduce `shell=True`/`echo` interpolation.
- Generated audio (`*.wav`) and the venv are git-ignored.
