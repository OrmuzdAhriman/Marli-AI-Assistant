# Open Tasks / Otvoreni zadaci

First thing to read when starting a session. Keep it current: add new tasks, delete done ones (the journal records history).
Prvo što se čita na početku sesije. Držati ažurnim: dodaj nove, briši završene (dnevnik čuva historiju).

## Now / Sada

- [ ] **Branch protection on `main`** — the repo OWNER (`OrmuzdAhriman`) must run `./scripts/setup-branch-protection.sh` (mcberbo got HTTP 404 = not admin). Until then protection is convention-only.
- [ ] **Pi back to `main` / Pi nazad na `main`** — the Pi was left on `senad/oled-face`, which is now merged+deleted. On next power-up: `cd ~/Marli-AI-Assistant && git switch main && git pull` (everything is in main now).
- [ ] **Live face test / Test lica uživo** — headset on, `python3 push_to_talk.py` on the Pi, one full turn: idle → pulsing eyes → thinking → mouth flapping exactly while the reply plays. Report layout tweaks (eye size/position are one-line changes in `face.py`).
- [ ] **`gh` on Senad's Pi** — run `./scripts/marli doctor` on the Pi (offers apt install), then `gh auth login` (user does auth). Needed to push/PR from the Pi itself.

## Next / Sljedeće

- [ ] **aprasovic onboarding** — clone repo on his Pi 5, run `./scripts/setup-pi.sh`, then `marli doctor`; read HANDBOOK.bs.md. His Piper lives in a venv → either align layout or set `MARLEY_PIPER`.
- [ ] **Wake-word mode + face live test** — `marley_wakeup.py` got the face too; untested end-to-end.
- [ ] **Identify OLED controller variant** — face assumed SSD1306; if the panel ever renders offset/garbled, try SH1106 driver (one-line change in `face.py`).

## Ideas / Ideje (unscheduled / neplanirano)

- Conversation memory for Marley (multi-turn context to Ollama)
- Bosnian voice/STT (whisper multilingual + Piper bs voice, if available)
- Bigger LLM when a Pi with more RAM shows up
