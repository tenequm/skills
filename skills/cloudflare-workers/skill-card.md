# Skill Card

## Description

cloudflare-workers guides building and deploying serverless applications on Cloudflare Workers: handlers, bindings (KV, D1, R2, Durable Objects, Queues, and more), wrangler configuration and deployment, testing, framework integration, and advanced features like Workflows, Containers, and observability.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers building APIs, full-stack apps, edge middleware, scheduled jobs, queue consumers, or MCP servers on Cloudflare's network, from first wrangler init through production deployment and CI/CD.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): Cloudflare account; CLOUDFLARE_API_TOKEN (scoped API token) and CLOUDFLARE_ACCOUNT_ID for non-interactive wrangler auth and CI deploys - interactive use can rely on wrangler login instead. Declared as optional envVars in the openclaw block.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Instructs the agent to use the wrangler CLI (installed via npm) and npm/create-cloudflare; optional third-party observability sinks (Datadog, Honeycomb) appear in examples only.

## Known Risks and Mitigations

Risk: Deployment commands (wrangler deploy, wrangler secret put) mutate live Cloudflare resources and can overwrite production Workers, routes, or secrets.

Mitigation: Use scoped API tokens with least privilege, separate staging/production environments in wrangler config as the skill shows, and review wrangler output before deploying to production.

Risk: Secrets could end up committed in wrangler.toml [vars] or hardcoded in Worker source.

Mitigation: The skill explicitly directs secrets to `wrangler secret put` (encrypted server-side, never written to disk) and restricts [vars] to non-secret values; code review should enforce this.

Risk: Example code (CORS with Access-Control-Allow-Origin "*", permissive auth stubs) is illustrative and insecure if shipped verbatim.

Mitigation: Treat examples as scaffolding; tighten CORS origins, authentication, and error handling to the application's actual requirements before production.

## References

- Cloudflare Workers docs (https://developers.cloudflare.com/workers/), Wrangler CLI (https://developers.cloudflare.com/workers/wrangler/), Workflows (https://developers.cloudflare.com/workflows/), Containers (https://developers.cloudflare.com/containers/), workers-sdk (https://github.com/cloudflare/workers-sdk)
- Source: https://github.com/tenequm/skills/tree/main/skills/cloudflare-workers

## Skill Output

Output type(s): Worker source code, wrangler configuration, CI/CD pipeline definitions, test files, and deployment/debugging guidance.

Output format: Code in TypeScript/JavaScript, TOML/JSONC configuration, YAML CI configs; Markdown explanations.

Output parameters: Not applicable

Other properties: Five references/ files cover bindings, wrangler/deployment, development patterns, advanced features, and observability; wrangler commands have side effects on the user's Cloudflare account.

## Skill Version

3.1.2

## Ethical Considerations

The skill enables deployment of code to public infrastructure; users are responsible for what their Workers serve, for securing credentials, and for complying with Cloudflare's terms of service.
