# Skill Card

## Description

download-webpage-as-pdf saves a live webpage as a high-fidelity PDF that preserves the original layout and every image, including lazy-loaded ones, using the agent-browser CLI. It fixes the blank-rectangle failures of naive headless-Chrome capture on JS-heavy sites via a scroll-and-await-images eval step, with an optional trim-and-compress cleanup pipeline.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Anyone who needs a local PDF archive of a webpage that looks like the browser version - articles, engineering blogs, dashboards, marketing pages - especially on modern sites with IntersectionObserver lazy loading where plain chrome --headless --print-to-pdf produces broken images.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Dependencies:
- Required binary (declared in metadata.openclaw requires.bins, node package agent-browser): agent-browser (verified against agent-browser@0.26.0)
- Environment variable (declared in metadata.openclaw envVars, optional): AGENT_BROWSER_HEADED - set to "false" for headless capture, the recipe default
- pdfinfo (poppler) for verification
- Optional cleanup: qpdf, ghostscript (gs)
- Alternative path: npx percollate for reader-mode output

## Known Risks and Mitigations

Risk: The recipe launches a real browser and executes an injected JavaScript eval on arbitrary user-supplied URLs, and writes PDF files to local disk.

Mitigation: The skill runs headless via AGENT_BROWSER_HEADED=false, isolates concurrent runs with --session, and closes the browser at the end; output paths are explicit and user-chosen.

Risk: A capture can silently miss content (images that never loaded, wrong session state), producing an incomplete archive that looks complete.

Mitigation: The eval returns the count of still-broken images (expect 0) and the recipe ends with a pdfinfo page-count/size check; non-zero counts are flagged as untrustworthy captures.

Risk: The pinned agent-browser version matters - the --headed false CLI flag in 0.26.0 corrupts the session and yields blank PDFs; newer versions may change behavior.

Mitigation: metadata.upstream pins the verified version (agent-browser@0.26.0) and the CHANGELOG records the verified workaround; re-verify when upgrading agent-browser.

## References

- agent-browser CLI (upstream pin: agent-browser@0.26.0)
- percollate (reader-mode alternative documented in the skill)
- Source: https://github.com/tenequm/skills/tree/main/skills/download-webpage-as-pdf

## Skill Output

Output type(s): Files - a PDF of the target webpage, plus a short verification report

Output format: PDF on disk; terminal output with broken-image count and pdfinfo page/size numbers

Output parameters: Output path chosen by the user (e.g. /tmp/page.pdf, then trimmed/compressed final path); letter-size pagination by default

Other properties: Side effects are browser session usage and files written to disk; capturing paywalled or access-controlled pages requires the user to have legitimate access

## Skill Version

0.1.5

## Ethical Considerations

Users should respect copyright and site terms of service when archiving web content; captured PDFs are for personal or licensed reference use, and completeness checks should be reviewed before treating a capture as a faithful record.
