# Skill Card

## Description

solana-development guides building, testing, deploying, and auditing Solana programs with Anchor or native Rust, plus building with ZK Compression (Light Protocol). It covers accounts, PDAs, CPIs, tokens, security review process, and compressed tokens/PDAs.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Solana smart-contract developers writing or reviewing on-chain programs: scaffolding Anchor or native Rust projects, implementing token operations, optimizing compute, deploying to devnet/mainnet, running structured security audits, or adopting rent-free compressed accounts via Light Protocol. The agent uses the reference map to load the topic-specific guide the task needs.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): RPC provider API key (e.g. Helius) for mainnet forking and ZK Compression indexer queries; Solana keypairs for deployment. Declared env var: SURFPOOL_DATASOURCE_RPC_URL (optional).

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Tools the skill instructs the agent to use: solana CLI, anchor/avm, cargo (build-sbf), surfpool, solana-verify, Mollusk, Trident, @lightprotocol packages (stateless.js, compressed-token, zk-compression-cli), photon-indexer.

## Known Risks and Mitigations

Risk: The skill produces deployment and upgrade-authority commands that move real funds and change program ownership on mainnet; a wrong flag (e.g. upgrade authority transfer) is irreversible.

Mitigation: Test every deployment flow on devnet or a surfpool mainnet fork first; require human review of any command that touches mainnet, keypairs, or authorities, and use multisig (Squads) for authority operations as the references recommend.

Risk: Audit guidance can produce a false sense of security - a review that follows the checklists may still miss vulnerabilities, and the exploit-writing patterns could be misused against third-party programs.

Mitigation: Treat skill-assisted reviews as a supplement to, not a replacement for, professional audits (the skill's own roadmap requires external audits before mainnet); apply exploit scenarios only to programs the user is authorized to test.

Risk: Version-sensitive facts (Anchor versions, Token-2022 handling, V2 batched state trees, RPC method names) drift as the Solana ecosystem moves quickly.

Mitigation: Cross-check versions and APIs against official Anchor/Solana/Light Protocol docs before relying on them for production deployments.

## References

- Solana docs: https://solana.com/docs
- Anchor: https://www.anchor-lang.com/docs
- ZK Compression: https://www.zkcompression.com/
- Light Protocol: https://github.com/Lightprotocol/light-protocol
- Source: https://github.com/tenequm/skills/tree/main/skills/solana-development

## Skill Output

Output type(s): Solana program code, tests, deployment/audit shell commands, and security audit reports with severity-ranked findings.

Output format: Rust and TypeScript code blocks, shell commands, and Markdown audit reports (finding template with location, exploit scenario, recommendation).

Output parameters: Audit findings follow the severity scale Critical/High/Medium/Low/Informational with the report format defined in SKILL.md.

Other properties: Generated commands can deploy to live networks and spend SOL; local tooling (surfpool, photon) makes network calls to configured RPC endpoints.

## Skill Version

0.7.1

## Ethical Considerations

Security and exploit knowledge in this skill is for defending and auditing programs the user owns or is authorized to review; using it against third-party programs without consent is misuse. All mainnet deployments and authority changes warrant explicit human sign-off.
