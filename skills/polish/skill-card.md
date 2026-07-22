# Skill Card

## Description

polish runs a pre-release code review on a git diff for developers about to commit, push, or release: automated lint/type checks, four parallel review lenses (cleanliness, design and reuse, efficiency, side-effect gating), finding validation, and approval-gated fixes.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers who want a structured quality gate over their working diff before it lands - catching debug leftovers, AI slop, dead code, missed reuse, over-engineering, performance issues, and side-effects that run before their validation gates - with every finding verified against actual code before being reported.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Dependencies the skill instructs the agent to use:
- git (read-only commands: diff, show, status, rev-parse, log - pre-approved via allowed-tools)
- The project's own lint/type-check command (e.g. pnpm check, just check, cargo clippy, ruff)
- The agent harness's subagent (Agent tool) fan-out for parallel review

## Known Risks and Mitigations

Risk: Phase 1 and Phase 6 modify the user's working tree - the skill fixes lint/type errors and applies approved review fixes, which can alter uncommitted work.

Mitigation: Fixes are minimal targeted edits, the report phase hard-stops with "Awaiting approval before proceeding with fixes," and nothing is committed or pushed by the skill itself.

Risk: Review agents can hallucinate findings (wrong line numbers, nonexistent utilities suggested for reuse), leading to bogus edits if trusted blindly.

Mitigation: A mandatory validation phase re-reads every cited file and line, greps for claimed symbols and utilities, and drops findings that fail verification; dropped findings are listed in the report with reasons.

Risk: A "clean" report can create false confidence - the skill checks code quality and side-effect ordering, not full business-logic correctness.

Mitigation: The skill explicitly scopes business-logic review out (routing it to a separate /review flow), and a correctness zero must state what was traced rather than just report a count.

## References

- Source: https://github.com/tenequm/skills/tree/main/skills/polish

## Skill Output

Output type(s): Analysis (structured review report) and, after explicit approval, code edits

Output format: Markdown report grouped by category (Correctness, Cleanliness, Design, Efficiency, Observations, Dropped after validation) with file:line citations; code fixes in the project's languages

Output parameters: Report ends with a per-finding fix/skip recommendation and the approval-gate line

Other properties: Runs the project's validation command (may fix lint/type errors before review); writes the diff to a scratchpad file for agent fan-out; never commits.

## Skill Version

2.4.1

## Ethical Considerations

The human stays the decision-maker: findings are recommendations, fixes require explicit approval, and the skill is a complement to - not a replacement for - human code review, especially for security- or payment-touching changes.
