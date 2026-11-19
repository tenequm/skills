---
name: journal-update
description: Updates or creates today's work journal in the current project's docs/journal/, then commits and pushes it. Use when asked to update the journal, log or record today's work, or wrap up a work session. Not for other dated docs.
argument-hint: "[optional: what to focus on]"
metadata:
  version: "0.1.1"
  categories: "productivity"
  topics: "journal, work-log, daily-notes"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/journal-update
    emoji: "📓"
---

# Journal update

Record this work session in today's entry of the current project's journal,
`docs/journal/`. If the invocation names a focus, lead with it; otherwise cover the
salient work since the journal was last touched.

This skill knows nothing about the project. The format comes from the existing
journal files; what may or may not be written comes from the project's own
instructions, which win over anything here.

## Today's entry

- The date and weekday are the real current ones, never recalled from memory.
- Today's file follows the newest files exactly: name, any day counter, header,
  sections. Work around midnight goes where the newest files put it.
- A new file's open threads are rebuilt from what is still open now - each previous
  item re-checked, not pasted forward.
- More than one candidate for today: ask which. No `docs/journal/`: stop and say so;
  never invent a format.

## What goes in

- Facts, not framing: what was done, decided, delivered, posted or found. Mark
  anything unconfirmed; no opinions or speculation.
- Link what can be linked; timestamps carry their timezone the way the file
  already states it.
- Add or extend one section for this session, in the file's own style. Never
  rewrite earlier entries. Never write a secret value.
- Exactly one open-threads block, always last, rewritten in place.

## Finish

Quote what changed. If nothing warranted an entry, say so and stop. Otherwise the
journal entry ends up committed, in the repo's message style, and pushed. The commit
carries nothing unrelated (files the repo's own hooks regenerate are fine), and
everyone else's uncommitted work stays as it is. If the journal file already held
uncommitted changes that are not this session's, ask before committing. A rejected
push is resolved by integrating upstream, never by force-pushing.
