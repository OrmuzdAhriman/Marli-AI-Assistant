# Marli Git Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the three-person team a single friendly `marli` command plus reusable Claude skills/commands that make the PR-based GitHub Flow easy and hard to misuse.

**Architecture:** One POSIX-bash CLI (`scripts/marli`) wraps `git` + `gh` for the `start → save → pr → ship` lifecycle, with newcomer guardrails. A repo-committed Claude skill maps user intent to `marli` subcommands; slash commands are thin wrappers. `main` is protected; branches are `<handle>/<topic>` with the handle derived at runtime.

**Tech Stack:** bash, `git`, GitHub CLI (`gh`). No new runtimes. Target: Debian 12 / Raspberry Pi OS, aarch64.

## Global Constraints

- Minimal dependencies: bash + `git` + `gh` only.
- Scripts MUST use LF line endings (they run on Linux) — enforced via `.gitattributes`.
- The tool NEVER handles credentials/tokens/passwords — `gh auth login` is delegated to the user.
- `main` is production: `save`/`pr`/`ship` refuse to run on `main`; only reviewed PRs land there.
- Branch handle is derived (`gh` login → sanitized git user.name → `$USER`), never hardcoded.
- All work is built on branch `senad/git-workflow` and merged via the first PR (dogfooding).

---

### Task 1: Enforce LF line endings

**Files:**
- Create: `.gitattributes`

**Interfaces:**
- Produces: normalized LF text files so `scripts/marli` runs on the Pi.

- [ ] **Step 1: Create `.gitattributes`**

```gitattributes
# Normalize all text to LF so shell scripts run on Linux regardless of editor OS.
* text=auto eol=lf
*.py text eol=lf
*.sh text eol=lf
scripts/marli text eol=lf
*.wav binary
*.onnx binary
```

- [ ] **Step 2: Re-normalize already-tracked files**

Run:
```bash
git add --renormalize .
git status --short
```
Expected: `marley_wakeup.py`, `push_to_talk.py` may show as modified (line endings normalized).

- [ ] **Step 3: Commit**

```bash
git add .gitattributes
git add --renormalize .
git commit -m "Enforce LF line endings for cross-platform scripts"
```

---

### Task 2: The `marli` CLI

**Files:**
- Create: `scripts/marli`

**Interfaces:**
- Produces: `marli <start|save|pr|sync|ship|status|doctor|help>` — the commands the skill and slash commands invoke.

- [ ] **Step 1: Create `scripts/marli`** with this exact content:

```bash
#!/usr/bin/env bash
# marli — friendly git workflow for the Marli-AI-Assistant repo.
# Flow: start -> save -> pr -> (review) -> ship.   Run `marli help`.
set -uo pipefail

# --- styling (degrade gracefully with no TTY) ---
if [ -t 1 ]; then
  BOLD=$(tput bold); DIM=$(tput dim); RST=$(tput sgr0)
  RED=$(tput setaf 1); GRN=$(tput setaf 2); YLW=$(tput setaf 3); BLU=$(tput setaf 4)
else
  BOLD=""; DIM=""; RST=""; RED=""; GRN=""; YLW=""; BLU=""
fi
say()  { printf '%s %s\n' "${BLU}▸${RST}" "$*"; }
ok()   { printf '%s %s\n' "${GRN}✓${RST}" "$*"; }
warn() { printf '%s %s\n' "${YLW}!${RST}" "$*"; }
die()  { printf '%s %s\n' "${RED}✗${RST}" "$*" >&2; exit 1; }
next() { printf '%snext:%s %s%s%s\n' "$DIM" "$RST" "$BOLD" "$*" "$RST"; }

in_repo() { git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git repo. cd into the project first."; }
current_branch() { git rev-parse --abbrev-ref HEAD; }
clean_tree() { [ -z "$(git status --porcelain)" ]; }
require_gh() { command -v gh >/dev/null 2>&1 || die "GitHub CLI 'gh' not found. Run: marli doctor"; }
require_not_main() { [ "$(current_branch)" != "main" ] || die "You're on main (production). Start a branch first:  marli start <topic>"; }

handle() {
  local h
  h=$(gh api user --jq .login 2>/dev/null || true)
  [ -n "$h" ] || h=$(git config user.name 2>/dev/null | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
  [ -n "$h" ] || h=${USER:-dev}
  printf '%s' "$h"
}

cmd_start() {
  in_repo
  local topic=${1:-}
  [ -n "$topic" ] || die "Give a topic:  marli start <topic>   (e.g. marli start wakeword)"
  clean_tree || die "You have uncommitted changes. Save them first:  marli save   (or 'git stash')"
  say "Updating main…"
  git switch main >/dev/null 2>&1 || git checkout main
  git pull --ff-only origin main || die "Could not update main. Check your connection / 'gh auth login'."
  local branch; branch="$(handle)/${topic}"
  git switch -c "$branch" || die "Branch '$branch' may already exist. Try: git switch $branch"
  ok "On new branch ${BOLD}${branch}${RST}"
  next "make changes, then  marli save \"what you did\""
}

cmd_save() {
  in_repo; require_not_main
  local msg=${1:-}
  git add -A
  if git diff --cached --quiet; then
    warn "Nothing new to commit."
  else
    if [ -z "$msg" ]; then
      printf '%sCommit message:%s ' "$BOLD" "$RST"; read -r msg
      [ -n "$msg" ] || die "Empty message — nothing committed."
    fi
    git commit -q -m "$msg" || die "Commit failed."
    ok "Committed: $msg"
  fi
  say "Pushing…"
  git push -u origin "$(current_branch)" || die "Push failed. Are you logged in?  gh auth login"
  ok "Pushed ${BOLD}$(current_branch)${RST}"
  next "open a pull request:  marli pr"
}

cmd_pr() {
  in_repo; require_gh; require_not_main
  local branch; branch="$(current_branch)"
  git push -u origin "$branch" >/dev/null 2>&1 || true
  local url
  url=$(gh pr view "$branch" --json url --jq .url 2>/dev/null || true)
  if [ -n "$url" ]; then
    ok "PR already open: $url"
  else
    local title=${1:-}
    if [ -n "$title" ]; then
      gh pr create --base main --head "$branch" --title "$title" --fill || die "Could not create PR."
    else
      gh pr create --base main --head "$branch" --fill || die "Could not create PR."
    fi
    url=$(gh pr view "$branch" --json url --jq .url 2>/dev/null || true)
    ok "PR opened: $url"
  fi
  next "get a teammate to review, then  marli ship"
}

cmd_sync() {
  in_repo
  local prev; prev="$(current_branch)"
  say "Updating main…"
  git switch main >/dev/null 2>&1 || git checkout main
  git pull --ff-only origin main || die "Could not update main."
  ok "main is up to date."
  if [ "$prev" != "main" ]; then
    printf '%sBring latest main into ' "$BOLD"; printf "'%s'? [y/N]%s " "$prev" "$RST"; read -r ans
    git switch "$prev" >/dev/null 2>&1 || return 0
    if [ "${ans:-}" = "y" ] || [ "${ans:-}" = "Y" ]; then
      git merge main && ok "Merged latest main into ${prev}." || warn "Merge hit conflicts — resolve, then 'marli save'."
    fi
  fi
}

cmd_ship() {
  in_repo; require_gh; require_not_main
  local branch; branch="$(current_branch)"
  say "Merging PR for ${branch}…"
  if gh pr merge "$branch" --squash --delete-branch; then
    git switch main >/dev/null 2>&1 || git checkout main
    git pull --ff-only origin main
    git branch -d "$branch" 2>/dev/null || true
    ok "Shipped ${BOLD}${branch}${RST} to main and cleaned up."
    next "start your next task:  marli start <topic>"
  else
    local url; url=$(gh pr view "$branch" --json url --jq .url 2>/dev/null || true)
    die "Couldn't merge yet — main needs an approving review. Ask a teammate: ${url}"
  fi
}

cmd_status() {
  in_repo
  local branch; branch="$(current_branch)"
  printf '%sBranch:%s %s\n' "$BOLD" "$RST" "$branch"
  if clean_tree; then ok "Working tree clean"; else warn "Uncommitted changes:"; git status -s; fi
  git fetch -q origin 2>/dev/null || true
  if git rev-parse --verify -q origin/main >/dev/null; then
    local counts behind ahead
    counts=$(git rev-list --left-right --count origin/main...HEAD 2>/dev/null || printf '0\t0')
    behind=$(printf '%s' "$counts" | cut -f1); ahead=$(printf '%s' "$counts" | cut -f2)
    printf '%sSync:%s %s ahead, %s behind origin/main\n' "$BOLD" "$RST" "${ahead:-0}" "${behind:-0}"
  fi
  if command -v gh >/dev/null 2>&1 && [ "$branch" != "main" ]; then
    local pr; pr=$(gh pr view "$branch" --json state,url --jq '.state+"  "+.url' 2>/dev/null || true)
    if [ -n "$pr" ]; then printf '%sPR:%s %s\n' "$BOLD" "$RST" "$pr"; else printf '%sPR:%s none yet (marli pr)\n' "$BOLD" "$RST"; fi
  fi
}

install_gh() {
  command -v apt-get >/dev/null 2>&1 || die "No apt-get here. Install gh manually: https://github.com/cli/cli#installation"
  say "Installing GitHub CLI via official apt repo…"
  sudo mkdir -p -m 755 /etc/apt/keyrings
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
  sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  sudo apt-get update -qq && sudo apt-get install -y gh && ok "gh installed." || die "gh install failed."
}

cmd_doctor() {
  in_repo
  say "Checking your setup…"
  if command -v gh >/dev/null 2>&1; then
    ok "gh installed ($(gh --version | head -1))"
  else
    warn "GitHub CLI 'gh' not installed."
    printf '%sInstall it now with apt? [y/N]%s ' "$BOLD" "$RST"; read -r ans
    { [ "${ans:-}" = "y" ] || [ "${ans:-}" = "Y" ]; } && install_gh || warn "Skipped. Re-run 'marli doctor' later."
  fi
  if command -v gh >/dev/null 2>&1; then
    if gh auth status >/dev/null 2>&1; then ok "gh authenticated"; else warn "Not logged in. Run:  ${BOLD}gh auth login${RST}  (choose HTTPS)"; fi
  fi
  if [ -n "$(git config user.name || true)" ] && [ -n "$(git config user.email || true)" ]; then
    ok "git identity: $(git config user.name) <$(git config user.email)>"
  else
    warn "git identity not set."
    printf '  Your name:  '; read -r n; printf '  Your email: '; read -r e
    git config --global user.name "$n"; git config --global user.email "$e"; ok "Saved git identity."
  fi
  git remote get-url origin >/dev/null 2>&1 && ok "remote origin: $(git remote get-url origin)" || warn "No 'origin' remote set."
  local self target="$HOME/.local/bin/marli"
  self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  if [ ! -e "$target" ]; then
    printf "%sAdd 'marli' to your PATH (~/.local/bin)? [y/N]%s " "$BOLD" "$RST"; read -r ans
    if [ "${ans:-}" = "y" ] || [ "${ans:-}" = "Y" ]; then
      mkdir -p "$HOME/.local/bin"; ln -sf "$self" "$target"
      case ":$PATH:" in *":$HOME/.local/bin:"*) : ;; *) warn "Add ~/.local/bin to PATH in ~/.bashrc to use 'marli' directly." ;; esac
      ok "Linked marli -> $target"
    fi
  fi
}

cmd_help() {
  cat <<EOF
${BOLD}marli${RST} — friendly git for this repo.   Flow: ${BOLD}start → save → pr → ship${RST}

  ${BOLD}marli start${RST} <topic>   Start fresh work: update main, make your branch
  ${BOLD}marli save${RST} [msg]      Save your work: commit everything + push
  ${BOLD}marli pr${RST} [title]      Open a pull request into main
  ${BOLD}marli sync${RST}            Pull the latest main (optionally into your branch)
  ${BOLD}marli ship${RST}            Merge your approved PR and clean up
  ${BOLD}marli status${RST}          Where am I? branch, changes, PR
  ${BOLD}marli doctor${RST}          One-time setup check (gh, login, identity, PATH)
  ${BOLD}marli help${RST}            This help

Branches are <you>/<topic>. main is production — only reviewed PRs land there.
EOF
}

cmd=${1:-help}; shift 2>/dev/null || true
case "$cmd" in
  start)  cmd_start "$@";;
  save)   cmd_save "$@";;
  pr)     cmd_pr "$@";;
  sync)   cmd_sync "$@";;
  ship)   cmd_ship "$@";;
  status) cmd_status "$@";;
  doctor) cmd_doctor "$@";;
  help|-h|--help) cmd_help;;
  *) warn "Unknown command: $cmd"; cmd_help; exit 1;;
esac
```

- [ ] **Step 2: Make it executable and verify help works (no repo side effects)**

Run:
```bash
chmod +x scripts/marli
./scripts/marli help
```
Expected: the help text prints with the command list; exit 0.

- [ ] **Step 3: Verify guardrail — save refuses on main**

Run (while on any branch, temporarily check behavior on main in a scratch clone or trust the code): on `main`, `./scripts/marli save` prints `✗ You're on main (production)…` and exits non-zero.

- [ ] **Step 4: Commit**

```bash
git add scripts/marli
git commit -m "Add marli git-workflow CLI"
```

---

### Task 3: Branch-protection helper

**Files:**
- Create: `scripts/setup-branch-protection.sh`

**Interfaces:**
- Consumes: `gh` authenticated as a repo admin.
- Produces: `main` protected (PR + 1 approval required).

- [ ] **Step 1: Create `scripts/setup-branch-protection.sh`**

```bash
#!/usr/bin/env bash
# Apply branch protection to main. Run ONCE by a repo ADMIN.
set -uo pipefail
REPO="${1:-OrmuzdAhriman/Marli-AI-Assistant}"
command -v gh >/dev/null 2>&1 || { echo "Need gh. Run: marli doctor"; exit 1; }
echo "Applying protection to 'main' on $REPO (requires admin rights)…"
gh api -X PUT "repos/$REPO/branches/main/protection" \
  -H "Accept: application/vnd.github+json" --input - <<'JSON'
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": { "required_approving_review_count": 1 },
  "restrictions": null
}
JSON
rc=$?
if [ $rc -eq 0 ]; then
  echo "✓ main now requires a pull request with 1 approving review."
else
  echo "✗ Failed (rc=$rc). Likely you're not an admin on $REPO, or token lacks 'repo' scope."
fi
```

- [ ] **Step 2: Make executable + commit**

```bash
chmod +x scripts/setup-branch-protection.sh
git add scripts/setup-branch-protection.sh
git commit -m "Add branch-protection setup helper (admin-run)"
```

---

### Task 4: Claude skill `marli-git-workflow`

**Files:**
- Create: `.claude/skills/marli-git-workflow/SKILL.md`

**Interfaces:**
- Produces: a skill that routes git intent to `marli` commands (Task 2).

- [ ] **Step 1: Create `.claude/skills/marli-git-workflow/SKILL.md`**

```markdown
---
name: marli-git-workflow
description: Use when doing git work in the Marli-AI-Assistant repo — committing, pushing, creating branches, opening or merging pull requests, or explaining the git process. Routes every git action through the `marli` CLI so main (production) is never touched directly.
---

# Marli Git Workflow

This repo uses GitHub Flow with a protected `main` (production). Work happens on `<handle>/<topic>` branches and reaches main only through reviewed PRs. The `marli` CLI (`scripts/marli`, usually on PATH as `marli`) wraps every step.

**Never run raw `git commit`/`git push` on main, and never `git merge` into main locally.** Use marli.

## Map intent → command

| User wants | Run |
|---|---|
| start new work | `marli start <topic>` |
| save / commit / push current work | `marli save "message"` |
| open a pull request | `marli pr ["title"]` |
| pull the latest main | `marli sync` |
| merge an approved PR + clean up | `marli ship` |
| "where am I?" | `marli status` |
| first-time setup / gh broken | `marli doctor` |

## Rules
- "commit and open a PR" → run `marli save` then `marli pr`.
- On `main`, `save`/`pr`/`ship` refuse — run `marli start <topic>` first.
- `marli ship` only succeeds after an approving review (main is protected). If it fails for that reason, relay the PR URL and stop — never bypass protection.
- Run `marli status` before acting to report the current branch/PR state.
- If `marli` isn't found, it's `./scripts/marli`; suggest `marli doctor` to add it to PATH.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/marli-git-workflow/SKILL.md
git commit -m "Add marli-git-workflow Claude skill"
```

---

### Task 5: Slash commands

**Files:**
- Create: `.claude/commands/save.md`
- Create: `.claude/commands/pr.md`
- Create: `.claude/commands/ship.md`
- Create: `.claude/commands/sync.md`

- [ ] **Step 1: Create `.claude/commands/save.md`**

```markdown
---
description: Commit and push the current work via marli
---
Run `marli save` to stage, commit, and push the current branch. If there are changes and no message is given, summarize them into a concise commit message and pass it: `marli save "<message>"`. Report the result and the suggested next step.
```

- [ ] **Step 2: Create `.claude/commands/pr.md`**

```markdown
---
description: Open a pull request into main via marli
---
Run `marli pr` to open a pull request from the current branch into main. If a clear title fits the changes, pass it: `marli pr "<title>"`. Report the PR URL.
```

- [ ] **Step 3: Create `.claude/commands/ship.md`**

```markdown
---
description: Merge the approved PR and clean up via marli
---
Run `marli ship` to squash-merge the current branch's approved PR into main and delete the branch. If it fails because main requires a review, relay the PR URL and stop — do not bypass protection.
```

- [ ] **Step 4: Create `.claude/commands/sync.md`**

```markdown
---
description: Pull the latest main via marli
---
Run `marli sync` to update main from origin. If on a work branch, offer to merge the latest main into it.
```

- [ ] **Step 5: Commit**

```bash
git add .claude/commands
git commit -m "Add marli slash commands (save, pr, ship, sync)"
```

---

### Task 6: CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Create `CONTRIBUTING.md`**

````markdown
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
````

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "Add newcomer-friendly CONTRIBUTING guide"
```

---

### Task 7: End-to-end verification on the Pi, then open the PR

**Files:** none (verification + integration)

- [ ] **Step 1: Deploy the branch to the Pi and dry-run marli**

Run (from Windows):
```bash
# push the branch so the Pi can fetch it (requires gh-auth'd push access)
git push -u origin senad/git-workflow
```
On the Pi:
```bash
cd ~/Marli-AI-Assistant && git fetch origin && git switch senad/git-workflow
./scripts/marli help          # expect command list
./scripts/marli status        # expect branch + clean/dirty + PR state
./scripts/marli doctor        # expect gh install offer (gh absent today), identity OK
```
Expected: `help` and `status` succeed; `doctor` reports gh missing and offers apt install.

- [ ] **Step 2: Verify guardrail on main**

On the Pi:
```bash
git switch main
~/Marli-AI-Assistant/scripts/marli save
```
Expected: `✗ You're on main (production)…`, exit non-zero. Then `git switch senad/git-workflow`.

- [ ] **Step 3: Open the PR for this work**

```bash
marli pr "Add marli git workflow, Claude skill, commands, and docs"
```
Expected: PR URL printed. (Merging waits on branch protection + a review.)

- [ ] **Step 4: Apply branch protection (admin, once)**

```bash
./scripts/setup-branch-protection.sh
```
Expected: `✓ main now requires a pull request with 1 approving review` — or a clear admin-rights error to relay to the repo owner.

---

## Notes for the executor
- The `senad/git-workflow` branch already contains the portable-paths commit (`d4777d4`) and the spec (`e24a455`); Tasks 1–6 add commits on top.
- Pushing and PR creation require `gh` auth with write access to `OrmuzdAhriman/Marli-AI-Assistant`. On the Windows box `gh` is authed as `mcberbo`; confirm that account has push rights, or push from an account that does.
- Do not merge to `main` outside the `marli`/PR flow — this work dogfoods the process.
