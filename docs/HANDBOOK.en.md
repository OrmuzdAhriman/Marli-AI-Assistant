# Marli Handbook (English)

> Bosanska verzija: [HANDBOOK.bs.md](HANDBOOK.bs.md)

Everything about how this project works: the assistant, the hardware, the git process, and how we work with Claude. If you are new, read this top to bottom — it takes 10 minutes.

## 1. What is Marli

Marli ("Marley") is a **fully offline voice assistant** that runs on a Raspberry Pi 5. No cloud — every stage runs on the Pi itself:

```
you speak → arecord → whisper.cpp (speech→text) → Ollama LLM (answer) → Piper (text→speech) → aplay → you hear
                          ↑ the OLED face animates in sync with each stage ↑
```

Two ways to run it:
- `python3 push_to_talk.py` — press ENTER, speak 5 seconds, get an answer. Say "exit" to quit.
- `python3 marley_wakeup.py` — hands-free; it listens in a loop and activates on the phrase **"marley wake up"**.

## 2. Hardware

| Part | Detail |
|---|---|
| Raspberry Pi 5 | Debian 12 (Raspberry Pi OS), aarch64 |
| USB wireless headset | mic + speaker, ALSA `plughw:CARD=Headset,DEV=0` |
| OLED display 128×32 (SSD1306) | I2C address `0x3c` on `/dev/i2c-1` (GPIO pins 3/5) |

## 3. The voice pipeline

Each stage is a local binary; Python only glues them together (`requests` is the single pip dependency of the pipeline; `luma.oled` drives the display).

| Stage | Tool | Where |
|---|---|---|
| Record | `arecord` (ALSA) | 5 s, 16 kHz mono WAV |
| Speech→text | `whisper-cli` (whisper.cpp) | `~/whisper.cpp/build/bin/`, model `ggml-base.en.bin` |
| Answer | Ollama, model `qwen2.5:0.5b` | HTTP `localhost:11434` |
| Text→speech | Piper, voice `en_US-lessac-medium` | `~/piper/` |
| Play | `aplay` | to the headset |

**Configuration** is per-machine via environment variables (defaults assume the layout above). See the table in [CLAUDE.md](../CLAUDE.md): `MARLEY_WHISPER`, `MARLEY_WHISPER_MODEL`, `MARLEY_PIPER`, `MARLEY_PIPER_MODEL`, `MARLEY_MIC`, `MARLEY_SPEAKER`, `MARLEY_MODEL`, `MARLEY_OLLAMA_URL`.

## 4. The OLED face

`face.py` renders an animated face on the OLED in a background thread. The pipeline just switches states; the face follows:

| State | When | Look |
|---|---|---|
| `idle` | waiting | open eyes, slow blink, flat mouth |
| `listening` | recording | eyes pulse ("breathing") |
| `thinking` | transcribing + LLM | eyes look up, dots cycle |
| `speaking` | while the reply plays | mouth flaps — for exactly as long as the audio plays |

- Demo without the pipeline: `python3 face.py` (cycles all four states).
- No display connected? The face silently disables itself — the assistant still works.

## 5. Setting up a NEW Pi from zero

One script does it all (run it on the Pi):

```bash
git clone https://github.com/OrmuzdAhriman/Marli-AI-Assistant.git ~/Marli-AI-Assistant
cd ~/Marli-AI-Assistant
./scripts/setup-pi.sh
```

It installs build tools, builds whisper.cpp, installs Ollama (+ pulls the model), installs Piper (+ voice), installs `luma.oled`, and enables I2C for the display. Each big step asks before it runs. After it finishes: plug in the headset, run `python3 push_to_talk.py`.

## 6. Git process — how code reaches production

`main` = **production**. Nobody edits it directly. Everything goes through a Pull Request with one review. The `marli` command does the whole dance for you:

```bash
marli start my-topic      # 1. new branch from the latest main  (→ you/my-topic)
# ... edit files ...
marli save "what I did"   # 2. commit + push
marli pr                  # 3. open a Pull Request
# 4. teammate approves on GitHub
marli ship                # 5. merge + clean up
```

Lost? `marli status`. First time on a machine? `marli doctor`. Full newcomer guide: [CONTRIBUTING.md](../CONTRIBUTING.md).

## 7. Working with Claude

Claude Code is a team member here. The repo carries its knowledge so it works the same for everyone:

- `.claude/skills/marli-git-workflow/` — Claude always uses `marli` for git in this repo.
- `.claude/skills/marli-docs/` — after finishing any feature/integration, Claude updates the docs (both languages), the journal, and the task list. This is how the project **constantly grows without losing knowledge**.
- `.claude/commands/` — shortcuts: `/save`, `/pr`, `/ship`, `/sync`.
- [docs/JOURNAL.md](JOURNAL.md) — running log of what we did and what we're working on.
- [docs/TASKS.md](TASKS.md) — open tasks; the first thing to read when starting a session.
- `docs/superpowers/specs/` + `plans/` — design docs and implementation plans for every feature.

**The growth loop:** finish work → update JOURNAL + TASKS + HANDBOOK (via the `marli-docs` skill) → commit through `marli` → next session starts by reading TASKS. Nothing gets forgotten.
