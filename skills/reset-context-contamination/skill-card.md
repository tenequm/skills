# Skill Card

## Description

reset-context-contamination discards the accumulated drafts and framings of a long conversation thread and re-derives the task from a clean, extracted problem statement. It is a procedural prompt for agents whose output quality has degraded from anchoring on prior attempts.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Anyone working with an AI agent in a long thread where every new attempt keeps echoing earlier drafts or dead-end framings. Invoking the skill makes the agent extract a factual brief (goal, constraints, known facts, ruled-out approaches) and either re-derive in-thread, hand off to a fresh subagent, or recommend a new session depending on contamination severity.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

No external tools, CLIs, or packages; the skill is pure instructions to the agent.

## Known Risks and Mitigations

Risk: The extracted brief may silently drop a real constraint or decision from the discarded history, so the fresh derivation solves a subtly different task.

Mitigation: The skill instructs the agent to show the brief to the user before drafting when unsure; users should verify the brief captures all hard constraints before accepting the re-derived result.

Risk: For deep contamination, an in-thread self-reset can fail because the contaminated context still anchors the model, giving a false sense of a clean restart.

Mitigation: The skill explicitly routes high-stakes or deeply contaminated cases to a fresh subagent or a new session rather than trusting in-thread reset.

## References

- Source: https://github.com/tenequm/skills/tree/main/skills/reset-context-contamination

## Skill Output

Output type(s): A plain-language task brief (parties, desired outcome, constraints, known facts, ruled-out approaches) followed by a freshly derived answer or a handoff recommendation.

Output format: Markdown text in the conversation.

Output parameters: Not applicable

Other properties: May spawn a subagent or recommend ending the session; discards prior drafts by design, which is destructive to in-thread work-in-progress.

## Skill Version

0.1.1

## Ethical Considerations

The reset intentionally voids earlier drafts, so users should confirm nothing valuable is lost before invoking it on work they have not saved. The re-derived output still warrants normal human review.
