---
name: grafana-foundation-sdk
description: Build Grafana dashboards as code with the grafana-foundation-sdk typed builders (TypeScript or Go). Use when creating, modifying, or generating Grafana dashboard JSON programmatically, converting hand-written dashboard JSON to typed code, building monitoring dashboards, or working with Prometheus/Loki queries in dashboards.
metadata:
  version: "0.2.2"
  upstream: "@grafana/grafana-foundation-sdk@0.0.16, github.com/grafana/grafana-foundation-sdk/go@0.0.16"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/grafana-foundation-sdk
    emoji: "📊"
---

# Grafana Foundation SDK

The grafana-foundation-sdk provides strongly typed builder libraries for defining Grafana dashboards as code. Instead of writing raw JSON (which is error-prone and hard to review in diffs), you compose dashboards using chained builder calls that produce valid Grafana JSON.

The SDK is auto-generated from Grafana's internal CUE schemas via the `cog` tool. It supports Go, TypeScript, Python, PHP, and Java. This skill focuses on **TypeScript** (primary) and **Go** (secondary) since those are the most common choices for infrastructure teams.

## When to use this skill

- Creating new Grafana dashboards from scratch
- Converting existing hand-written dashboard JSON to typed code
- Adding panels, variables, or queries to dashboards
- Building reusable dashboard components (helper functions for common panel patterns)
- Generating dashboards dynamically based on service lists or configs

## Installation

The SDK is published as concrete `v0.0.x` tags (latest: **v0.0.16**). Pin explicitly - it is pre-1.0 and the API churns between releases (see Known Gotchas).

**TypeScript:**
```bash
npm install '@grafana/grafana-foundation-sdk@~0.0.16'
# or
pnpm add '@grafana/grafana-foundation-sdk@~0.0.16'
```

**Go:**
```bash
go get github.com/grafana/grafana-foundation-sdk/go@v0.0.16
```

## Core Architecture

Everything follows the **builder pattern**: create a builder, chain configuration methods, call `.build()` (TS) or `.Build()` (Go) to produce the final object. The output is standard Grafana dashboard JSON - compatible with Grafana's API, file-based provisioning, and Kubernetes ConfigMaps.

Each panel type, query type, and variable type lives in its own package. You import only what you need:

```typescript
// Each concern has its own import
import { DashboardBuilder, RowBuilder } from '@grafana/grafana-foundation-sdk/dashboard';
import { PanelBuilder as TimeseriesBuilder } from '@grafana/grafana-foundation-sdk/timeseries';
import { PanelBuilder as StatBuilder } from '@grafana/grafana-foundation-sdk/stat';
import { DataqueryBuilder as PromQueryBuilder } from '@grafana/grafana-foundation-sdk/prometheus';
import { DataqueryBuilder as LokiQueryBuilder } from '@grafana/grafana-foundation-sdk/loki';
```

## Quick Start - TypeScript

```typescript
import { DashboardBuilder, RowBuilder, QueryVariableBuilder } from '@grafana/grafana-foundation-sdk/dashboard';
import { PanelBuilder as StatBuilder } from '@grafana/grafana-foundation-sdk/stat';
import { PanelBuilder as TimeseriesBuilder } from '@grafana/grafana-foundation-sdk/timeseries';
import { DataqueryBuilder } from '@grafana/grafana-foundation-sdk/prometheus';
import * as common from '@grafana/grafana-foundation-sdk/common';

const dashboard = new DashboardBuilder('My Service Overview')
  .uid('my-service-overview')
  .tags(['my-service'])
  .editable()
  .refresh('30s')
  .time({ from: 'now-24h', to: 'now' })
  .timezone('browser')
  .withVariable(
    new QueryVariableBuilder('service')
      .label('Service')
      .query('label_values(up{namespace="default"}, job)')
      .datasource({ type: 'prometheus', uid: 'prometheus' })
      .refresh(1)
      .includeAll(true)
      .allValue('.*')
      .sort(1)
  )
  .withRow(new RowBuilder('Overview'))
  .withPanel(
    new StatBuilder()
      .title('Request Rate')
      .datasource({ type: 'prometheus', uid: 'prometheus' })
      .withTarget(
        new DataqueryBuilder()
          .expr('sum(rate(http_requests_total{job=~"$service"}[5m]))')
          .legendFormat('req/s')
      )
      .unit('reqps')
      .decimals(1)
      .height(4)
      .span(6)
      .colorMode(common.BigValueColorMode.Background)
      .graphMode(common.BigValueGraphMode.Area)
      .reduceOptions(
        new common.ReduceDataOptionsBuilder().calcs(['lastNotNull'])
      )
  )
  .withPanel(
    new TimeseriesBuilder()
      .title('Request Rate Over Time')
      .datasource({ type: 'prometheus', uid: 'prometheus' })
      .withTarget(
        new DataqueryBuilder()
          .expr('sum by (job)(rate(http_requests_total{job=~"$service"}[5m]))')
          .legendFormat('{{job}}')
      )
      .unit('reqps')
      .fillOpacity(15)
      .height(8)
      .span(12)
  );

// Output the dashboard JSON
console.log(JSON.stringify(dashboard.build(), null, 2));
```

## Key Patterns

### 1. Helper functions for repeated panel configurations

The biggest win from using the SDK is creating reusable helpers that encode your team's conventions:

```typescript
function promDs() {
  return { type: 'prometheus', uid: 'prometheus' } as const;
}

function lokiDs() {
  return { type: 'loki', uid: 'loki' } as const;
}

function promQuery(expr: string, legend?: string) {
  const q = new DataqueryBuilder().expr(expr);
  if (legend) q.legendFormat(legend);
  return q;
}

function statPanel(title: string, expr: string, opts?: { unit?: string; decimals?: number; color?: string }) {
  const panel = new StatBuilder()
    .title(title)
    .datasource(promDs())
    .withTarget(promQuery(expr))
    .height(4)
    .span(4)
    .colorMode(common.BigValueColorMode.Background)
    .graphMode(common.BigValueGraphMode.Area)
    .reduceOptions(new common.ReduceDataOptionsBuilder().calcs(['lastNotNull']));

  if (opts?.unit) panel.unit(opts.unit);
  if (opts?.decimals !== undefined) panel.decimals(opts.decimals);
  // Thresholds can be set via .thresholds() if needed

  return panel;
}
```

### 2. Template variables

```typescript
// Query variable - populated from Prometheus labels
new QueryVariableBuilder('service')
  .label('Service')
  .query('label_values(http_server_duration_count{namespace="x402"}, job)')
  .datasource({ type: 'prometheus', uid: 'prometheus' })
  .refresh(2)  // 1=on dashboard load, 2=on time range change
  .includeAll(true)
  .allValue('.*')
  .sort(1)  // 1=alphabetical asc

// Custom variable - static key:value pairs
new CustomVariableBuilder('level')
  .label('Log Level')
  .query('All : .+, Error : error|fatal, Warning : warn, Info : info, Debug : debug')
  .current({ text: 'All', value: '.+' })
```

Reference variables in queries with standard Grafana syntax: `$service`, `$__range`, `$__rate_interval`, `$__auto`.

### 3. Panel sizing

Panels use `height(h)` (grid rows) and `span(w)` (out of 24 columns):
- Full width: `.span(24)`
- Half width: `.span(12)`
- Third width: `.span(8)`
- Quarter width: `.span(6)`
- Typical stat panel: `.height(4).span(4)`
- Typical timeseries: `.height(8).span(12)`

### 4. Thresholds

```typescript
import { ThresholdsConfigBuilder } from '@grafana/grafana-foundation-sdk/dashboard';

// First step must have no value (it's the base)
new StatBuilder()
  .thresholds(
    new ThresholdsConfigBuilder()
      .mode(common.ThresholdsMode.Absolute)
      .steps([
        { value: null as any, color: 'green' },
        { value: 80, color: 'yellow' },
        { value: 95, color: 'red' },
      ])
  )
```

### 5. Field overrides

```typescript
new TimeseriesBuilder()
  .overrideByName('Revenue', [
    { id: 'color', value: { fixedColor: 'green', mode: 'fixed' } },
  ])
  .overrideByRegexp('.*5..', [
    { id: 'color', value: { fixedColor: 'red', mode: 'fixed' } },
  ])
```

### 6. Rows (including collapsed)

```typescript
// Regular row
.withRow(new RowBuilder('Traffic'))

// Collapsed row with nested panels
.withRow(
  new RowBuilder('Business Details')
    .collapsed()
    .withPanel(/* ... */)
    .withPanel(/* ... */)
)
```

### 7. Loki log and metric queries

```typescript
import { DataqueryBuilder as LokiQueryBuilder } from '@grafana/grafana-foundation-sdk/loki';

// Log query
new LokiQueryBuilder()
  .expr('{namespace="x402", app=~"$service", level=~"$level"}')
  .refId('A')

// Metric query from logs
new LokiQueryBuilder()
  .expr('sum by (buyer_wallet)(count_over_time({namespace="x402"} | event="request" [$__range]))')
  .legendFormat('{{buyer_wallet}}')
  .refId('A')
```

### 8. Transformations

Transformations are applied as raw objects since the SDK doesn't have typed builders for all transformation types:

```typescript
new TableBuilder()
  .withTransformation({
    id: 'reduce',
    options: {
      reducers: ['lastNotNull'],
      mode: 'seriesToRows',
      includeTimeField: false,
      labelsToFields: true,
    },
  })
  .withTransformation({
    id: 'organize',
    options: {
      excludeByName: { Field: true },
      renameByName: { buyer_wallet: 'Buyer Wallet', 'Last not null': 'Requests' },
    },
  })
  .withTransformation({
    id: 'sortBy',
    options: { sort: [{ field: 'Requests', desc: true }] },
  })
```

## Generating Output

The `.build()` call returns a plain object matching Grafana's dashboard JSON schema. Serialize it however you need:

```typescript
// Standard JSON file (for provisioning or ConfigMaps)
const fs = require('fs');
const dashboard = builder.build();
fs.writeFileSync('dashboard.json', JSON.stringify(dashboard, null, 2));

// Kubernetes resource manifest (for Grafana's k8s API)
const manifest = {
  apiVersion: 'dashboard.grafana.app/v1beta1',
  kind: 'Dashboard',
  metadata: { name: dashboard.uid },
  spec: dashboard,
};
console.log(JSON.stringify(manifest, null, 2));
```

## Known Gotchas

These are sharp edges discovered from real usage and open issues on the SDK repo:

1. **SDK is v0.0.x (public preview)** - Used by Grafana Labs in production but the API can change between releases. Pin your version explicitly. Best suited for Grafana >= 12, works with >= 10.

2. **`instant()` and `range()` are mutually exclusive in Prometheus** - Calling `.instant()` sets `instant=true` AND `range=false`. Calling `.range()` does the opposite. Use `.rangeAndInstant()` if you need both.

3. **Loki `range()`/`instant()` are deprecated** - Use `.queryType('range')` or `.queryType('instant')` instead. Similarly, `.resolution()` is deprecated in favor of `.step()`.

4. **First threshold step must have `value: null`** - This is the base/default color. Omitting it produces invalid JSON.

5. **Panel IDs are auto-assigned** - You don't set `id` on panels. Grafana assigns them at import time. Similarly, `gridPos.x/y` are computed from `height()` and `span()`.

6. **Transformations are plain objects** - The SDK has no typed builders for transformations. Pass them as raw `{ id, options }` objects via `.withTransformation()`.

7. **CustomVariable quirk** - When provisioning via Grafana's API, `CustomVariableBuilder` requires the `.query()` field with comma-separated key:value pairs (e.g., `'All : .+, Error : error'`) for options to persist, even when `.values()` is also used.

8. **Go: `cog.ToPtr()` is essential** - Many struct fields are pointer types. Use `cog.ToPtr[T](value)` for nullable fields (thresholds, datasource refs). TypeScript doesn't have this issue.

9. **Go: `Build()` returns error** - Always check it. TypeScript's `.build()` returns the object directly with compile-time type safety instead.

10. **No typed query builders for plugin datasources** - Only core datasources (Prometheus, Loki, Tempo, Elasticsearch, CloudWatch, etc.) have builders. For third-party plugins, define custom query types by implementing the `Builder<Dataquery>` interface.

11. **Dashboard schema v1 vs v2** - This skill targets the v1 dashboard (`@grafana/grafana-foundation-sdk/dashboard`, k8s apiVersion `dashboard.grafana.app/v1beta1`). A newer schema v2 ships as `dashboardv2beta1` (k8s apiVersion `dashboard.grafana.app/v2beta1`) with its own builders. v2beta1 is still stabilizing and has known sharp edges (e.g. transforms, annotation positioning, SQL expressions in Go) - prefer v1 unless you specifically need v2 layouts. Most query/panel builders are shared; some expose a `QueryV2Builder`/`VisualizationV2Builder` variant for v2.

12. **Builders are only type-checked if wired into a tsconfig** - The SDK gives compile-time safety only when the generator file is actually type-checked. A generator sitting under a non-package directory (e.g. a Helm chart dir) that no `tsconfig` includes is silently unchecked, so type errors surface only at `.build()` runtime. Also: the SDK's output targets ES2024/`bundler` module resolution, which an older global `tsc` chokes on - run the project-local compiler (`npx tsc`), not a stale global one.

13. **Regenerate JSON after every generator edit** - The deployed dashboard is the generated JSON, not the `.ts`/`.go` source. Edit the generator, re-run it, and commit the regenerated JSON together; never hand-edit the generated JSON (the next regen silently overwrites it). A repo rule ("never edit the dashboard JSON directly") is worth adding.

## Project-Specific Context

In this project, dashboards are provisioned as Kubernetes ConfigMaps via the monitoring-deps Helm chart:
- Dashboard JSON files live in `ops/helmfile-infra/charts/monitoring-deps/dashboards/`
- `templates/dashboards.yaml` wraps each JSON file into a ConfigMap with `grafana_dashboard: "1"` label
- Data sources: Prometheus (`uid: "prometheus"`) and Loki (`uid: "loki"`)
- Standard namespace filter: `namespace="x402"`
- Common template variables: `$service` (job selector), `$level` (log level)

When generating dashboards for this project, output the JSON to the dashboards directory and ensure the ConfigMap template references it.

## Reference Files

For detailed API reference and complete examples, see:
- `references/typescript-api.md` - Full TypeScript API with all panel types, query builders, and configuration options
- `references/patterns.md` - Common dashboard patterns, recipes, and a complete example converting this project's dashboard to SDK code
