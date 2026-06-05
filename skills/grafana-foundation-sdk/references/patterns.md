# Common Dashboard Patterns

## Table of Contents
1. [Project Structure](#project-structure)
2. [RED Method Dashboard](#red-method-dashboard)
3. [Kubernetes Service Dashboard](#kubernetes-service-dashboard)
4. [Loki Log Panels](#loki-log-panels)
5. [Multi-Datasource Dashboard](#multi-datasource-dashboard)
6. [Dynamic Dashboard Generation](#dynamic-dashboard-generation)
7. [Converting Raw JSON to SDK](#converting-raw-json-to-sdk)
8. [Integration with Helm/ConfigMaps](#integration-with-helmconfigmaps)

---

## Project Structure

For a monorepo with multiple dashboards, keep dashboard generators alongside the monitoring config:

```
ops/
  dashboards/
    generate.ts          # entry point - imports and runs all generators
    helpers.ts           # shared datasource refs, query helpers, panel defaults
    overview.ts          # overview dashboard generator
    per-service.ts       # per-service dashboard generator
    package.json         # { "type": "module", "scripts": { "generate": "tsx generate.ts" } }
    tsconfig.json
  helmfile/
    charts/monitoring-deps/
      dashboards/        # generated JSON files go here
```

Or for a single dashboard, a simple standalone script works fine:

```
ops/dashboards/
  generate-overview.ts
  package.json
```

**package.json:**
```json
{
  "type": "module",
  "scripts": {
    "generate": "tsx generate.ts"
  },
  "dependencies": {
    "@grafana/grafana-foundation-sdk": "^0.0.16"
  },
  "devDependencies": {
    "tsx": "^4.0.0"
  }
}
```

---

## RED Method Dashboard

The RED method (Rate, Errors, Duration) is the standard pattern for monitoring request-driven services. Here's a complete implementation:

```typescript
import { DashboardBuilder, RowBuilder, QueryVariableBuilder, ThresholdsConfigBuilder } from '@grafana/grafana-foundation-sdk/dashboard';
import { PanelBuilder as StatBuilder } from '@grafana/grafana-foundation-sdk/stat';
import { PanelBuilder as TimeseriesBuilder } from '@grafana/grafana-foundation-sdk/timeseries';
import { DataqueryBuilder } from '@grafana/grafana-foundation-sdk/prometheus';
import * as common from '@grafana/grafana-foundation-sdk/common';

// --- Helpers ---

const PROM = { type: 'prometheus', uid: 'prometheus' } as const;

function pq(expr: string, legend?: string) {
  const q = new DataqueryBuilder().expr(expr);
  if (legend) q.legendFormat(legend);
  return q;
}

function defaultTimeseries(title: string) {
  return new TimeseriesBuilder()
    .title(title)
    .datasource(PROM)
    .height(8)
    .span(12)
    .fillOpacity(15)
    .lineWidth(1)
    .showPoints(common.VisibilityMode.Never)
    .legend(
      new common.VizLegendOptionsBuilder()
        .showLegend(true)
        .placement(common.LegendPlacement.Bottom)
        .displayMode(common.LegendDisplayMode.List)
    )
    .tooltip(
      new common.VizTooltipOptionsBuilder()
        .mode(common.TooltipDisplayMode.Multi)
        .sort(common.SortOrder.Descending)
    );
}

// --- Dashboard ---

function buildREDDashboard(namespace: string, metricPrefix: string) {
  return new DashboardBuilder(`${namespace} RED`)
    .uid(`${namespace}-red`)
    .tags([namespace, 'red'])
    .editable()
    .refresh('30s')
    .time({ from: 'now-1h', to: 'now' })
    .withVariable(
      new QueryVariableBuilder('service')
        .label('Service')
        .query(`label_values(${metricPrefix}_duration_count{namespace="${namespace}"}, job)`)
        .datasource(PROM)
        .refresh(2)
        .includeAll(true)
        .allValue('.*')
        .sort(1)
    )

    // --- Rate ---
    .withRow(new RowBuilder('Rate'))
    .withPanel(
      defaultTimeseries('Request Rate')
        .withTarget(pq(
          `sum by (job)(rate(${metricPrefix}_duration_count{namespace="${namespace}",job=~"$service"}[5m]))`,
          '{{job}}'
        ))
        .unit('reqps')
        .stacking(new common.StackingConfigBuilder().mode(common.StackingMode.Normal))
    )
    .withPanel(
      defaultTimeseries('Request Rate by Status')
        .withTarget(pq(
          `sum by (http_status_code)(rate(${metricPrefix}_duration_count{namespace="${namespace}",job=~"$service"}[5m]))`,
          '{{http_status_code}}'
        ))
        .unit('reqps')
    )

    // --- Errors ---
    .withRow(new RowBuilder('Errors'))
    .withPanel(
      defaultTimeseries('Error Rate (5xx)')
        .withTarget(pq(
          `sum by (job)(rate(${metricPrefix}_duration_count{namespace="${namespace}",job=~"$service",http_status_code=~"5.."}[5m]))`,
          '{{job}}'
        ))
        .unit('reqps')
    )
    .withPanel(
      defaultTimeseries('Error Percentage')
        .withTarget(pq(
          `sum(rate(${metricPrefix}_duration_count{namespace="${namespace}",job=~"$service",http_status_code=~"5.."}[5m])) / sum(rate(${metricPrefix}_duration_count{namespace="${namespace}",job=~"$service"}[5m])) * 100`,
          'error %'
        ))
        .unit('percent')
    )

    // --- Duration ---
    .withRow(new RowBuilder('Duration'))
    .withPanel(
      defaultTimeseries('Latency Percentiles')
        .withTarget(pq(
          `histogram_quantile(0.50, sum by (le)(rate(${metricPrefix}_duration_bucket{namespace="${namespace}",job=~"$service"}[5m])))`,
          'p50'
        ))
        .withTarget(pq(
          `histogram_quantile(0.95, sum by (le)(rate(${metricPrefix}_duration_bucket{namespace="${namespace}",job=~"$service"}[5m])))`,
          'p95'
        ))
        .withTarget(pq(
          `histogram_quantile(0.99, sum by (le)(rate(${metricPrefix}_duration_bucket{namespace="${namespace}",job=~"$service"}[5m])))`,
          'p99'
        ))
        .unit('ms')
    )
    .withPanel(
      defaultTimeseries('Latency by Service')
        .withTarget(pq(
          `histogram_quantile(0.95, sum by (job, le)(rate(${metricPrefix}_duration_bucket{namespace="${namespace}",job=~"$service"}[5m])))`,
          '{{job}} p95'
        ))
        .unit('ms')
    );
}

// Generate
const dashboard = buildREDDashboard('x402', 'http_server');
console.log(JSON.stringify(dashboard.build(), null, 2));
```

---

## Kubernetes Service Dashboard

Pattern for monitoring a specific Kubernetes service with both Prometheus metrics and Loki logs:

```typescript
import { PanelBuilder as LogsBuilder } from '@grafana/grafana-foundation-sdk/logs';
import { DataqueryBuilder as LokiQueryBuilder } from '@grafana/grafana-foundation-sdk/loki';

const LOKI = { type: 'loki', uid: 'loki' } as const;

// Log panel with filtering
new LogsBuilder()
  .title('Application Logs')
  .datasource(LOKI)
  .withTarget(
    new LokiQueryBuilder()
      .expr('{namespace="x402", app=~"$service", level=~"$level"}')
      .refId('A')
  )
  .showTime(true)
  .wrapLogMessage(true)
  .enableLogDetails(true)
  .sortOrder(common.LogsSortOrder.Descending)
  .dedupStrategy(common.LogsDedupStrategy.None)
  .height(12)
  .span(24)
```

---

## Loki Log Panels

### Metric from logs (count, sum, avg)

```typescript
// Count events over time
new LokiQueryBuilder()
  .expr('sum by (status)(count_over_time({namespace="x402", app=~"$service"} | event="request" [$__range]))')
  .legendFormat('{{status}}')

// Sum a numeric field extracted from logs
new LokiQueryBuilder()
  .expr('sum by (network)(sum_over_time({namespace="x402"} | event="settlement" | success="true" | unwrap amount_usd [$__range]))')
  .legendFormat('{{network}}')

// Average a numeric field
new LokiQueryBuilder()
  .expr('avg(avg_over_time({namespace="x402", app=~"$service"} | event="request" | status="200" | unwrap duration_ms | __error__="" [$__auto]))')
  .legendFormat('avg latency')

// Top-K from logs
new LokiQueryBuilder()
  .expr('topk(10, sum by (buyer_wallet)(count_over_time({namespace="x402"} | event="request" | buyer_wallet!="" [$__range])))')
  .legendFormat('{{buyer_wallet}}')
```

### Table panel with Loki + transformations

```typescript
import { PanelBuilder as TableBuilder } from '@grafana/grafana-foundation-sdk/table';

new TableBuilder()
  .title('Top Buyer Wallets')
  .datasource(LOKI)
  .withTarget(
    new LokiQueryBuilder()
      .expr('topk(10, sum by (buyer_wallet)(count_over_time({namespace="x402"} | event="request" | buyer_wallet!="" [$__range])))')
      .refId('A')
  )
  .withTransformation({
    id: 'reduce',
    options: { reducers: ['lastNotNull'], mode: 'seriesToRows', includeTimeField: false, labelsToFields: true },
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
  .height(8)
  .span(12)
```

---

## Multi-Datasource Dashboard

When combining Prometheus and Loki in the same dashboard, define datasource refs as constants and use them consistently:

```typescript
const DS = {
  prometheus: { type: 'prometheus', uid: 'prometheus' },
  loki: { type: 'loki', uid: 'loki' },
  tempo: { type: 'tempo', uid: 'tempo' },
} as const;

// Prometheus panel
new TimeseriesBuilder()
  .datasource(DS.prometheus)
  .withTarget(new PromQueryBuilder().expr('...'))

// Loki panel
new LogsBuilder()
  .datasource(DS.loki)
  .withTarget(new LokiQueryBuilder().expr('...'))
```

---

## Dynamic Dashboard Generation

Generate dashboards dynamically based on a list of services:

```typescript
const services = ['inference', 'twitter', 'github', 'web'];

function buildServiceDashboard(service: string) {
  return new DashboardBuilder(`${service} - Detail`)
    .uid(`${service}-detail`)
    .tags(['x402', service])
    .editable()
    .refresh('30s')
    .time({ from: 'now-1h', to: 'now' })
    .withRow(new RowBuilder('Overview'))
    .withPanel(
      new StatBuilder()
        .title('Request Rate')
        .datasource(PROM)
        .withTarget(pq(`sum(rate(http_server_duration_count{namespace="x402",job="${service}"}[5m]))`))
        .unit('reqps')
        .height(4).span(6)
    )
    // ... more panels
    ;
}

// Generate all dashboards
for (const service of services) {
  const dash = buildServiceDashboard(service);
  fs.writeFileSync(`dashboards/${service}.json`, JSON.stringify(dash.build(), null, 2));
}
```

---

## Converting Raw JSON to SDK

When converting existing hand-written dashboard JSON to SDK code, follow this mapping:

| JSON Field | SDK Method |
|---|---|
| `"uid": "x"` | `.uid('x')` |
| `"title": "x"` | `.title('x')` |
| `"tags": [...]` | `.tags([...])` |
| `"editable": true` | `.editable()` |
| `"refresh": "30s"` | `.refresh('30s')` |
| `"time": { "from": "now-24h", "to": "now" }` | `.time({ from: 'now-24h', to: 'now' })` |
| `"timezone": "browser"` | `.timezone('browser')` |
| `"graphTooltip": 1` | `.tooltip(DashboardCursorSync.Crosshair)` |
| `"type": "row"` | `.withRow(new RowBuilder('title'))` |
| `"type": "stat"` | `new StatBuilder()` |
| `"type": "timeseries"` | `new TimeseriesBuilder()` |
| `"type": "logs"` | `new LogsBuilder()` |
| `"type": "piechart"` | `new PieChartBuilder()` |
| `"type": "bargauge"` | `new BarGaugeBuilder()` |
| `"type": "barchart"` | `new BarChartBuilder()` |
| `"type": "table"` | `new TableBuilder()` |
| `"gridPos": { "h": 8, "w": 12 }` | `.height(8).span(12)` |
| `"datasource": { "type": "prometheus", "uid": "prometheus" }` | `.datasource({ type: 'prometheus', uid: 'prometheus' })` |
| `"targets": [{ "expr": "..." }]` | `.withTarget(new DataqueryBuilder().expr('...'))` |
| `"fieldConfig.defaults.unit": "ms"` | `.unit('ms')` |
| `"fieldConfig.defaults.decimals": 2` | `.decimals(2)` |
| `"fieldConfig.defaults.noValue": "N/A"` | `.noValue('N/A')` |
| `"fieldConfig.defaults.custom.fillOpacity": 15` | `.fillOpacity(15)` |
| `"fieldConfig.defaults.custom.stacking.mode": "normal"` | `.stacking(new StackingConfigBuilder().mode(StackingMode.Normal))` |
| `"options.reduceOptions.calcs": ["lastNotNull"]` | `.reduceOptions(new ReduceDataOptionsBuilder().calcs(['lastNotNull']))` |
| `"options.colorMode": "background"` | `.colorMode(BigValueColorMode.Background)` |
| `"options.graphMode": "area"` | `.graphMode(BigValueGraphMode.Area)` |
| `"collapsed": true` | `.collapsed()` |

**Tips for conversion:**
1. Start with the dashboard-level config (uid, tags, time, refresh)
2. Convert variables next (they're referenced by panels)
3. Convert panels row by row, creating helper functions for repeated patterns
4. Panel IDs are auto-assigned by Grafana - you don't need to set them
5. `gridPos.x` and `gridPos.y` are computed automatically from `height()` and `span()` - you only need to specify width and height

---

## Integration with Helm/ConfigMaps

In this project, generated dashboard JSON files are provisioned via ConfigMaps:

**Template (`templates/dashboards.yaml`):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dashboard-overview
  labels:
    grafana_dashboard: "1"
data:
  overview.json: |-
{{ .Files.Get "dashboards/overview.json" | indent 4 }}
```

**Workflow:**
1. Edit the TypeScript generator in `ops/dashboards/`
2. Run `pnpm generate` (or `tsx generate.ts`) to produce JSON in `dashboards/`
3. Commit the generated JSON alongside the generator code
4. Deploy with `helmfile sync` - the ConfigMap picks up the new JSON

The `grafana_dashboard: "1"` label tells the Grafana sidecar to load the ConfigMap as a dashboard automatically.
