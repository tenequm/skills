---
name: journal-update
description: Updates or creates today's work journal in the current project's docs/journal/, then commits and pushes it. Use when asked to update the journal, log or record today's work, or wrap up a work session. Not for other dated docs.
argument-hint: "[optional: what to focus on]"
metadata:
  version: "0.1.0"
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
- Today's file follows the newest files exactly: name, day counter, header,
  sections. Work continuing past midnight in the same sitting stays in the day it
  started.
- A new file starts its open threads fresh from what is actually open, never
  copied forward.
- More than one candidate for today: ask which. No `docs/journal/`: stop and say so;
  never invent a format.

## What goes in

- Facts, not framing: what was done, decided, delivered, posted or found. Mark
  anything unconfirmed; no opinions or speculation.
- Link what can be linked; give timestamps with their timezone.
- Add or extend one section for this session, in the file's own style. Never
  rewrite earlier entries. Never write a secret value.
- Exactly one open-threads block, always last, rewritten in place.

## Finish

Quote what changed. If nothing warranted an entry, say so and stop. Otherwise the
journal file - and only it - ends up committed, in the repo's message style, and
pushed. Never force anything, and leave everyone else's uncommitted work as it is.
