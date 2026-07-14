# Marli priručnik (Bosanski)

> English version: [HANDBOOK.en.md](HANDBOOK.en.md)

Sve o tome kako ovaj projekat funkcioniše: asistent, hardver, git proces i kako radimo sa Claudeom. Ako si nov — pročitaj od vrha do dna, treba ti 10 minuta.

## 1. Šta je Marli

Marli ("Marley") je **potpuno offline glasovni asistent** koji radi na Raspberry Pi 5. Bez clouda — svaki korak se izvršava na samom Pi-ju:

```
ti govoriš → arecord → whisper.cpp (govor→tekst) → Ollama LLM (odgovor) → Piper (tekst→govor) → aplay → ti čuješ
                        ↑ OLED lice se animira sinhronizovano sa svakim korakom ↑
```

Dva načina pokretanja:
- `python3 push_to_talk.py` — pritisni ENTER, govori 5 sekundi, dobiješ odgovor. Reci "exit" za izlaz.
- `python3 marley_wakeup.py` — bez ruku; sluša u petlji i aktivira se na frazu **"marley wake up"**.

## 2. Hardver

| Dio | Detalj |
|---|---|
| Raspberry Pi 5 | Debian 12 (Raspberry Pi OS), aarch64 |
| USB bežične slušalice | mikrofon + zvučnik, ALSA `plughw:CARD=Headset,DEV=0` |
| OLED ekran 128×32 (SSD1306) | I2C adresa `0x3c` na `/dev/i2c-1` (GPIO pinovi 3/5) |

## 3. Glasovni pipeline

Svaki korak je lokalni program; Python ih samo povezuje (`requests` je jedina pip zavisnost pipelinea; `luma.oled` pokreće ekran).

| Korak | Alat | Gdje |
|---|---|---|
| Snimanje | `arecord` (ALSA) | 5 s, 16 kHz mono WAV |
| Govor→tekst | `whisper-cli` (whisper.cpp) | `~/whisper.cpp/build/bin/`, model `ggml-base.en.bin` |
| Odgovor | Ollama, model `qwen2.5:0.5b` | HTTP `localhost:11434` |
| Tekst→govor | Piper, glas `en_US-lessac-medium` | `~/piper/` |
| Reprodukcija | `aplay` | na slušalice |

**Konfiguracija** je po mašini preko environment varijabli (podrazumijevane vrijednosti prate raspored iznad). Vidi tabelu u [CLAUDE.md](../CLAUDE.md): `MARLEY_WHISPER`, `MARLEY_WHISPER_MODEL`, `MARLEY_PIPER`, `MARLEY_PIPER_MODEL`, `MARLEY_MIC`, `MARLEY_SPEAKER`, `MARLEY_MODEL`, `MARLEY_OLLAMA_URL`.

## 4. OLED lice

`face.py` iscrtava animirano lice na OLED-u u pozadinskom threadu. Pipeline samo mijenja stanje; lice ga prati:

| Stanje | Kada | Izgled |
|---|---|---|
| `idle` | čeka | otvorene oči, sporo treptanje, ravna usta |
| `listening` | snima | oči pulsiraju ("dišu") |
| `thinking` | transkripcija + LLM | oči gledaju gore, tačkice kruže |
| `speaking` | dok se odgovor reprodukuje | usta se otvaraju/zatvaraju — tačno koliko traje zvuk |

- Demo bez pipelinea: `python3 face.py` (prođe kroz sva četiri stanja).
- Ekran nije priključen? Lice se tiho isključi — asistent i dalje radi.

## 5. Postavljanje NOVOG Pi-ja od nule

Jedna skripta radi sve (pokreni je na Pi-ju):

```bash
git clone https://github.com/OrmuzdAhriman/Marli-AI-Assistant.git ~/Marli-AI-Assistant
cd ~/Marli-AI-Assistant
./scripts/setup-pi.sh
```

Instalira build alate, kompajlira whisper.cpp, instalira Ollamu (+ povuče model), instalira Piper (+ glas), instalira `luma.oled` i uključi I2C za ekran. Svaki veliki korak pita prije nego što krene. Kad završi: priključi slušalice i pokreni `python3 push_to_talk.py`.

## 6. Git proces — kako kod stiže u produkciju

`main` = **produkcija**. Niko je ne mijenja direktno. Sve ide kroz Pull Request uz jednu recenziju (review). Komanda `marli` odradi cijeli posao za tebe:

```bash
marli start moja-tema       # 1. nova grana sa najnovijeg maina  (→ ti/moja-tema)
# ... mijenjaš fajlove ...
marli save "šta sam uradio" # 2. commit + push
marli pr                    # 3. otvori Pull Request
# 4. kolega odobri na GitHubu
marli ship                  # 5. spoji + počisti
```

Izgubio si se? `marli status`. Prvi put na mašini? `marli doctor`. Kompletan vodič za početnike: [CONTRIBUTING.md](../CONTRIBUTING.md).

## 7. Rad sa Claudeom

Claude Code je član tima. Repo nosi njegovo znanje, pa radi isto za svakoga:

- `.claude/skills/marli-git-workflow/` — Claude uvijek koristi `marli` za git u ovom repou.
- `.claude/skills/marli-docs/` — nakon svake završene funkcionalnosti/integracije, Claude ažurira dokumentaciju (oba jezika), dnevnik i listu zadataka. Tako projekat **stalno raste bez gubljenja znanja**.
- `.claude/commands/` — prečice: `/save`, `/pr`, `/ship`, `/sync`.
- [docs/JOURNAL.md](JOURNAL.md) — tekući dnevnik: šta smo radili i na čemu radimo.
- [docs/TASKS.md](TASKS.md) — otvoreni zadaci; prvo što se čita na početku sesije.
- `docs/superpowers/specs/` + `plans/` — dizajn dokumenti i planovi implementacije za svaku funkcionalnost.

**Petlja rasta:** završi posao → ažuriraj JOURNAL + TASKS + HANDBOOK (kroz `marli-docs` skill) → commituj kroz `marli` → sljedeća sesija počinje čitanjem TASKS-a. Ništa se ne zaboravlja.
