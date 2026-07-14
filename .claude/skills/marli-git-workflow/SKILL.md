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
