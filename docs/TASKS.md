# Open Tasks / Otvoreni zadaci

First thing to read when starting a session. Keep it current: add new tasks, delete done ones (the journal records history).
Prvo što se čita na početku sesije. Držati ažurnim: dodaj nove, briši završene (dnevnik čuva historiju).

## Now / Sada

- [ ] **Review & merge the PR chain / Pregledati i spojiti lanac PR-ova** — in order / redom:
      [#1 git workflow](https://github.com/OrmuzdAhriman/Marli-AI-Assistant/pull/1) → [#2 OLED face](https://github.com/OrmuzdAhriman/Marli-AI-Assistant/pull/2) → #3 docs & growth.
      Each needs one approving review; merge with `marli ship` (or GitHub UI). PRs #2/#3 auto-retarget to main as their base merges.
- [ ] **Branch protection on `main`** — the repo OWNER (`OrmuzdAhriman`) must run `./scripts/setup-branch-protection.sh` (mcberbo got HTTP 404 = not admin). Until then protection is convention-only.
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
