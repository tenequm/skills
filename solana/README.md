# Solana

Three skills for Solana development: **solana-development** (Anchor + native Rust), **solana-security** (auditing), and **solana-compression** (ZK compression via Light Protocol).

## Install

```
/plugin marketplace add tenequm/claude-plugins
/plugin install solana@tenequm-plugins
```

## Example Prompts

### Development
```
"Create an Anchor program for token staking with rewards"
"Convert this Anchor program to native Rust"
"Set up Bankrun tests for my program"
```

### Security
```
"Audit this program for vulnerabilities"
"Run security checklist on my token program"
"Check for PDA seed collisions and signer validation"
```

### ZK Compression
```
"Create a compressed token mint with Light Protocol"
"Build an Anchor program with compressed PDAs"
"Set up local development with light test-validator"
```

## Contents

- `solana-development`: 26 references (accounts, PDAs, CPIs, tokens, testing, deployment, compute optimization)
- `solana-security`: 7 references (vulnerability patterns, checklists, framework-specific guides)
- `solana-compression`: 4 references (compressed tokens, compressed PDAs, client integration)
