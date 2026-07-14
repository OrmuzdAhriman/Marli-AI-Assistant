---
name: marli-docs
description: Use when starting a session in the Marli-AI-Assistant repo, when finishing any feature/integration/setup work, or when asked "what are we working on" / "šta radimo". Keeps the project's living docs (JOURNAL, TASKS, HANDBOOK in EN+BS) and Claude's memory in sync so the project constantly grows without losing knowledge.
---

# Marli Docs — the growth loop

This repo's knowledge lives in files, not in anyone's head. Your job with this skill: **read them at session start, update them at work end.**

## At session START

1. Read `docs/TASKS.md` — the open tasks. Mention the relevant ones to the user.
2. Skim the newest entry of `docs/JOURNAL.md` for context on where work left off.
3. Check open PRs (`gh pr list`) — stacked PR chains merge in order.

## When work FINISHES (feature, integration, setup, decision)

Update, in this order:

1. **`docs/JOURNAL.md`** — add/extend the day's entry (newest first): what was built, key decisions, PR numbers. Short EN paragraph + short BS paragraph.
2. **`docs/TASKS.md`** — delete completed tasks, add newly discovered ones. Keep the Now / Next / Ideas structure, bilingual labels.
3. **`docs/HANDBOOK.en.md` + `docs/HANDBOOK.bs.md`** — only if the change affects how things work (new component, new process, changed config). **Both languages, always — never let them drift.**
4. **Repo `CLAUDE.md`** — only for gotchas future Claude instances need when editing code.
5. **Claude memory** (`~/.claude/.../memory/`) — update the Marley project/reference files with durable facts (hardware, access, decisions). Repo docs are for humans+Claude; memory is Claude's cross-session recall. Both matter.

Then commit through the workflow: `marli save "docs: ..."` on the current work branch (or a `<handle>/docs-...` branch if main-bound).

## Writing rules

- **Bilingual is non-negotiable** for HANDBOOK (full mirror) and TASKS/JOURNAL (short BS summaries). Team includes git newcomers reading in Bosnian.
- Journal = history (append, never rewrite). Tasks = present (prune aggressively). Handbook = how it works now (rewrite freely).
- Specs/plans in `docs/superpowers/` are immutable records — don't retro-edit them; new decisions get new entries.
- Keep it short. A doc nobody reads is worse than no doc.
