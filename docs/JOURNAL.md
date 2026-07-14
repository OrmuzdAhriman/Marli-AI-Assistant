# Journal / Dnevnik

Running log of what we did and what we're working on. Newest first.
Tekući dnevnik: šta smo radili i na čemu radimo. Najnovije prvo.

---

## 2026-07-14 — Bootstrap day (Senad + Claude)

**EN:** Set up everything from zero on Senad's Pi 5 (`sosmic-pi`):
- Provisioned the full voice stack: whisper.cpp (base.en), Ollama (`qwen2.5:0.5b`), Piper (lessac-medium). All stages smoke-tested individually.
- Refactored `push_to_talk.py` / `marley_wakeup.py`: portable `~`-relative paths + `MARLEY_*` env overrides, removed `shell=True` injection risk. One codebase now runs on any teammate's Pi.
- Built the git process: protected-main GitHub Flow, `marli` CLI (`start/save/pr/sync/ship/status/doctor`), Claude skill + slash commands, CONTRIBUTING.md → **PR #1**.
- Found the 128×32 SSD1306 OLED at `0x3c`/`i2c-1`, enabled I2C persistently, built the animated face (`face.py`: idle/listening/thinking/speaking, mouth synced to TTS playback) wired into both pipelines → **PR #2** (stacked on #1).
- Wrote bilingual handbook, `setup-pi.sh` provisioning script, this journal, TASKS.md, and the `marli-docs` growth skill → **PR #3** (stacked on #2).
- Pi shut down cleanly at end of session.

**BS:** Postavljeno sve od nule na Senadovom Pi 5 (`sosmic-pi`): kompletan glasovni stack (whisper.cpp, Ollama, Piper), prenosivi kod sa env varijablama, git proces sa `marli` komandom (PR #1), animirano OLED lice sinhronizovano sa govorom (PR #2), dvojezična dokumentacija + skripta za postavljanje novog Pi-ja + petlja rasta (PR #3). Pi uredno ugašen na kraju sesije.
