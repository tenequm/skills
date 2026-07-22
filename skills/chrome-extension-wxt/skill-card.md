# Skill Card

## Description

chrome-extension-wxt guides building cross-browser extensions with the WXT framework using TypeScript, React, Vue, or Svelte for developers targeting Chrome, Firefox, Edge, and Safari. It covers project scaffolding, entry points (background, content scripts, popup), Manifest V3 configuration, storage, messaging, and store packaging.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Web developers creating or maintaining browser extensions: initializing a WXT project, wiring background/content/popup entry points, integrating a UI framework, and producing store-ready builds for multiple browsers from one codebase.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None (Chrome Web Store or Firefox Add-ons developer accounts are needed only for publishing, outside this skill's scope)

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Dependencies:
- Node.js with npm (npm create wxt@latest)
- WXT framework and optional modules (@wxt-dev/module-react, etc.)
- Optional: Tailwind CSS, shadcn/ui, Mantine for UI stacks

## Known Risks and Mitigations

Risk: Generated manifest configurations may request broader permissions or host_permissions than the extension needs, expanding its attack surface and risking store rejection.

Mitigation: Review the permissions list before building; request only the narrowest permissions the feature requires (e.g. activeTab over broad host patterns).

Risk: WXT, browser APIs, and store policies evolve; scaffolding commands or API examples pinned to 2025-era versions may be outdated.

Mitigation: Cross-check against the official WXT docs (https://wxt.dev) and Chrome extension docs before shipping; the skill links both.

Risk: The skill drives npm installs and dev-server commands that execute third-party code on the developer machine.

Mitigation: Review commands before running; use lockfiles and audit dependencies as with any Node project.

## References

- WXT documentation: https://wxt.dev
- Chrome Extension documentation: https://developer.chrome.com/docs/extensions
- Source: https://github.com/tenequm/skills/tree/main/skills/chrome-extension-wxt

## Skill Output

Output type(s): Code and files - extension project scaffolding, TypeScript/TSX source, wxt.config.ts, manifest configuration

Output format: TypeScript/TSX, HTML, YAML/JSON config, shell commands

Output parameters: WXT file-based conventions (entrypoints/, components/, utils/, public/); build output at .output/<name>-<version>-<browser>.zip

Other properties: Dev and build commands run npm scripts with side effects on the local project; no network calls beyond package installation

## Skill Version

1.1.2

## Ethical Considerations

Browser extensions can access sensitive page content; developers should follow least-privilege permission design and store policies, and generated code should be reviewed by a human before publishing to extension stores.
