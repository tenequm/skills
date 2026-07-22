# Skill Card

## Description

playwright-cli-cloakbrowser drives CloakBrowser Manager stealth Chromium profiles with @playwright/cli over CDP for browser automation that needs a persistent logged-in session, anti-detect fingerprints, or to pass Cloudflare challenges.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Users automating logged-in or JS-heavy websites through a self-hosted CloakBrowser Manager (local Docker or a Linux VM over SSH) - attaching to persistent stealth profiles, scraping dynamic content, reverse-engineering same-origin APIs, and handling anti-automation defenses with field-tested gotchas.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): Optional AUTH_TOKEN environment variable (bearer token) for a protected Manager API; optional proxy credentials configured per profile; site logins live inside the browser profiles, not in the skill

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Dependencies the skill instructs the agent to use:
- playwright-cli binary from the @playwright/cli npm package (pinned 0.1.15; declared in metadata.openclaw requires.bins/install)
- Docker 20.10+ running the cloakhq/cloakbrowser-manager image
- curl for the Manager's HTTP API
- SSH (for the remote-VM tunnel setup)

## Known Risks and Mitigations

Risk: The skill drives a real browser that performs live actions on external websites from logged-in sessions - clicks, form submissions, and authenticated API calls can have real-world side effects on user accounts.

Mitigation: Automation runs against profiles the user created and controls; the built-in noVNC viewer lets the user watch and intervene live, and the skill instructs detach (never close/kill) so the user retains the session.

Risk: Stealth fingerprints and Cloudflare bypass can be used to violate site terms of service, evade rate limits, or scrape content at scale against a site's wishes.

Mitigation: Users are responsible for complying with target-site terms and applicable law; the skill's guidance treats anti-automation pushback (mid-run logout, blocks) as a signal to slow down and re-establish sessions, not to escalate evasion.

Risk: An exposed Manager instance grants full control of logged-in browser profiles; by default the Manager runs with no authentication.

Mitigation: The skill binds the Manager to localhost, recommends an SSH tunnel as the auth boundary for remote VMs, and documents AUTH_TOKEN plus HTTPS reverse proxy for any direct exposure.

## References

- Upstream: https://github.com/CloakHQ/CloakBrowser-Manager and https://github.com/CloakHQ/CloakBrowser (pinned @playwright/cli@0.1.15)
- Source: https://github.com/tenequm/skills/tree/main/skills/playwright-cli-cloakbrowser

## Skill Output

Output type(s): Live browser actions (navigation, clicks, eval) and scraped data; shell commands via playwright-cli, curl, and docker

Output format: Command-line invocations; scraped values as JSON-serialized text (via --raw eval); accessibility snapshots as YAML

Output parameters: Not applicable

Other properties: Writes a .playwright-cli/ scratch directory (snapshots, console logs) into the cwd; leaves the stealth browser running on detach; sessions persist cookies and logins across runs.

## Skill Version

0.3.2

## Ethical Considerations

Users must respect target websites' terms of service, robots policies, and applicable data-protection law; stealth automation and persistent identities should only operate on accounts the user owns. Review scraped data handling and keep site credentials inside the controlled profiles, never in prompts or logs.
