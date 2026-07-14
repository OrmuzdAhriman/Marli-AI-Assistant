# Marli Git Workflow & Claude Tooling — Design

**Date:** 2026-07-14
**Status:** Approved
**Author:** Senad + Claude

## Purpose

Establish base git processes for the `Marli-AI-Assistant` repo so a three-person team — including members new to GitHub — can contribute safely without stress. `main` is production; all changes reach it through reviewed Pull Requests. A single friendly `marli` command wraps the day-to-day git flow, and reusable Claude skills/commands let teammates drive the same flow through Claude Code.

## Audience & constraints

- Three contributors, each on their own Raspberry Pi 5, pulling this repo to run Marley.
- At least one contributor is new to git/GitHub — the tooling must be forgiving, self-explaining, and hard to misuse.
- Minimal dependencies: bash + `git` + `gh` (GitHub CLI) only. No new language runtimes or frameworks.
- Runs on Debian 12 (Raspberry Pi OS), aarch64.

## Git model — GitHub Flow with protected main

- **`main` = production.** Branch-protected on GitHub: no direct pushes; merges require an open PR with ≥1 approving review.
- **Work branches:** `<handle>/<topic>`, e.g. `senad/wakeword`, `aprasovic/tts-fix`.
  - `<handle>` is derived at runtime, never hardcoded, so it scales to any number of contributors:
    1. `gh api user --jq .login` (GitHub username — preferred, stable), else
    2. sanitized `git config user.name` (lowercased, spaces → `-`), else
    3. `$USER`.
  - `<topic>` is a short kebab-case slug supplied by the user.
- **Lifecycle:** `sync → start → save → pr → (review on GitHub) → ship`.
- Squash-merge on ship, so `main` history stays one-commit-per-change and branches are deleted after merge.

## Component 1 — `scripts/marli` (the CLI)

A single POSIX-bash script committed to the repo, so `git pull` distributes updates to everyone. `marli doctor` offers to symlink it to `~/.local/bin/marli` so contributors just type `marli`.

Every subcommand: (a) prints what it is about to do, (b) does it, (c) prints the **suggested next step**. Failures exit non-zero with a plain-English explanation and a fix.

| Command | Behavior | Guardrail |
|---|---|---|
| `marli start <topic>` | verify clean tree → `git switch main` → `git pull --ff-only` → `git switch -c <handle>/<topic>` | aborts if uncommitted changes (tells user to `save` or stash) |
| `marli save [msg]` | `git add -A` → commit (msg from arg, else prompt) → `git push -u origin HEAD` | **refuses on `main`** → directs to `marli start`; no-ops cleanly if nothing to commit/push |
| `marli pr [title]` | ensure branch pushed → `gh pr create --base main --fill` (or `--title`) → print PR URL; if a PR already exists, print its URL instead | refuses on `main` or if branch has no commits vs main |
| `marli sync` | `git switch main` → `git pull --ff-only` → offer to bring `main` into the previous work branch via merge | — |
| `marli ship` | `gh pr merge --squash --delete-branch` for the current branch's PR → `git switch main` → `git pull` → delete merged local branch | if protection blocks (no approval yet), catches the error and prints the PR URL to get a review |
| `marli status` | plain-English summary: current branch, working-tree changes, ahead/behind vs `origin/main`, open PR state | — |
| `marli doctor` | check/install `gh`; check `gh auth status` (guide `gh auth login` — user does it); set git identity if unset; verify `origin`; offer the `~/.local/bin/marli` symlink | never handles credentials itself |
| `marli help` | list every command with a one-line plain-English description | — |

Notes:
- `gh auth login` is interactive and credential-bearing — `doctor` only *detects* missing auth and instructs the user to run it; the script never enters tokens/passwords.
- `marli` is safe to re-run; commands are idempotent where possible.

## Component 2 — Claude tooling (`.claude/`, in-repo)

- **Skill `marli-git-workflow`** (`.claude/skills/marli-git-workflow/SKILL.md`): teaches Claude the branch model and maps user intent → `marli` subcommand ("commit and open a PR" → `marli save` then `marli pr`). Triggers on commit/push/PR/merge/branch requests within this repo, or questions about the process. Keeps Claude from inventing ad-hoc git commands that could touch `main` directly.
- **Slash commands** (`.claude/commands/`): thin speed wrappers — `/save`, `/pr`, `/ship`, `/sync` — each a short prompt instructing Claude to run the matching `marli` command and summarize the result.

## Component 3 — Onboarding

- **`CONTRIBUTING.md`**: the whole flow in ~15 newcomer-friendly lines — install (`marli doctor`), then the `start → save → pr → ship` loop, with copy-paste examples.
- **Branch protection**: `scripts/setup-branch-protection.sh` applies the rule via `gh api` (require PR + 1 review, no force-push to `main`). **Must be run once by a repo admin** — flagged clearly, since the current `gh` identity may lack admin on `OrmuzdAhriman/Marli-AI-Assistant`.

## File layout (added by this work)

```
scripts/marli                     # the CLI
scripts/setup-branch-protection.sh
.claude/skills/marli-git-workflow/SKILL.md
.claude/commands/{save,pr,ship,sync}.md
CONTRIBUTING.md
docs/superpowers/specs/2026-07-14-marli-git-workflow-design.md
```

All of the above is built on the `senad/git-workflow` branch and merged via the first PR — dogfooding the process it establishes.

## Out of scope (YAGNI)

CI pipelines, release tags/changelogs, multi-environment deploys, automated Pi deployment. Not needed for three people running a local voice assistant; revisit if the team or app grows.

## Success criteria

1. A newcomer runs `marli doctor` once, then completes `start → save → pr` without touching a raw git command.
2. `marli save` cannot commit to `main`; `main` only advances through merged, reviewed PRs.
3. Branch handles are correct for all three contributors with no per-user editing of the script.
4. Asking Claude to "open a PR for my changes" in this repo drives the same `marli` flow via the skill.
5. `marli ship` cleans up local + remote branches after merge.

## Testing approach

- Dry-run each `marli` subcommand on a throwaway branch on the Pi (`sosmic@`): `start`, `save` (trivial change), `status`, `pr` (against a scratch topic), then close the PR.
- Verify guardrails: `marli save` on `main` refuses; `marli start` with dirty tree refuses.
- Confirm `marli doctor` reports gh/auth/identity state accurately on a box where `gh` is absent (the Pi today).
