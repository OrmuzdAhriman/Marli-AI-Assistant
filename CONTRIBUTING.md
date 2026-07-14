# Contributing to Marli

`main` is **production**. You never edit it directly — you make a branch, open a Pull Request, get one review, and merge. The `marli` command does all of this for you.

## One-time setup
```bash
cd ~/Marli-AI-Assistant
./scripts/marli doctor      # installs gh, checks login + identity, adds `marli` to PATH
gh auth login               # if doctor says you're not logged in (choose HTTPS)
```

## Everyday flow
```bash
marli start wakeword          # 1. new branch off the latest main → you/wakeword
# ...edit files...
marli save "add wake word"    # 2. commit + push
marli pr                      # 3. open a pull request into main
# 4. a teammate reviews & approves on GitHub
marli ship                    # 5. merge it and clean up
```

Lost? `marli status` shows where you are. `marli help` lists everything.

## Rules
- Branch names are `<you>/<topic>` — `marli start` sets this automatically.
- `main` changes only through a reviewed PR; `marli save` refuses to commit to main.
- One approval is required before `marli ship` will merge.
