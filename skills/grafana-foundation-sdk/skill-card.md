# Skill Card

## Description

grafana-foundation-sdk guides an agent through building Grafana dashboards as code with the grafana-foundation-sdk typed builders (TypeScript primary, Go secondary) for infrastructure and platform teams. It covers installation, the builder pattern, key panel/variable/query recipes, output generation, and known SDK gotchas.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Engineers who need to create, modify, or generate Grafana dashboard JSON programmatically - including converting hand-written dashboard JSON to typed builder code, building reusable panel helpers, and generating dashboards dynamically from service lists or configs.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Dependencies the skill instructs the agent to use:
- @grafana/grafana-foundation-sdk npm package (pinned v0.0.16) or github.com/grafana/grafana-foundation-sdk/go (v0.0.16)
- npm/pnpm or the Go toolchain to install and run generator code
- A TypeScript compiler (project-local npx tsc) for type-checking generators

## Known Risks and Mitigations

Risk: The SDK is pre-1.0 (v0.0.x) and its API churns between releases; code generated from this skill against a different SDK version may fail to compile or produce invalid dashboard JSON.

Mitigation: The skill pins v0.0.16 explicitly in all install commands and tracks the pin in metadata.upstream; users should keep the installed SDK version matching the pin and review generated JSON before provisioning.

Risk: Generated dashboard JSON is deployed to live Grafana instances; a wrong query, threshold, or datasource UID can silently break monitoring views teams rely on.

Mitigation: Regenerate and diff the JSON output after every generator edit, review diffs before commit, and validate dashboards in a non-production Grafana before provisioning.

Risk: Generator files sitting outside any tsconfig are silently unchecked, so type errors surface only at runtime.

Mitigation: The skill documents this gotcha explicitly and instructs wiring generators into a type-checked project and running the project-local compiler.

## References

- Upstream: https://github.com/grafana/grafana-foundation-sdk (pinned @grafana/grafana-foundation-sdk@0.0.16, github.com/grafana/grafana-foundation-sdk/go@0.0.16)
- Source: https://github.com/tenequm/skills/tree/main/skills/grafana-foundation-sdk

## Skill Output

Output type(s): Code (dashboard generator source) and files (generated Grafana dashboard JSON)

Output format: TypeScript or Go source code; JSON dashboard definitions; optional Kubernetes manifest wrappers

Output parameters: Dashboard JSON conforming to Grafana's v1 dashboard schema (k8s apiVersion dashboard.grafana.app/v1beta1)

Other properties: Targets dashboard schema v1; schema v2 (dashboardv2beta1) is noted as still stabilizing. Transformations are passed as raw objects (no typed builders).

## Skill Version

0.2.2

## Ethical Considerations

Generated dashboards feed operational decision-making; humans should review queries and thresholds before deploying, since misleading panels can hide real incidents. The skill produces code and JSON only and handles no personal data.
