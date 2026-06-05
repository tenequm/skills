# TypeScript API Reference

## Table of Contents
1. [Imports](#imports)
2. [Dashboard Builder](#dashboard-builder)
3. [Panel Types](#panel-types)
4. [Query Builders](#query-builders)
5. [Variable Builders](#variable-builders)
6. [Field Configuration](#field-configuration)
7. [Common Enums](#common-enums)
8. [Go Quick Reference](#go-quick-reference)

---

## Imports

Every concept lives in its own subpath export. Import only what you need:

```typescript
// Dashboard structure
import {
  DashboardBuilder,
  RowBuilder,
  QueryVariableBuilder,
  CustomVariableBuilder,
  DatasourceVariableBuilder,
  DashboardLinkBuilder,
  ThresholdsConfigBuilder,
} from '@grafana/grafana-foundation-sdk/dashboard';

// Panel types (each exports PanelBuilder)
import { PanelBuilder as TimeseriesBuilder } from '@grafana/grafana-foundation-sdk/timeseries';
import { PanelBuilder as StatBuilder } from '@grafana/grafana-foundation-sdk/stat';
import { PanelBuilder as GaugeBuilder } from '@grafana/grafana-foundation-sdk/gauge';
import { PanelBuilder as BarGaugeBuilder } from '@grafana/grafana-foundation-sdk/bargauge';
import { PanelBuilder as TableBuilder } from '@grafana/grafana-foundation-sdk/table';
import { PanelBuilder as PieChartBuilder } from '@grafana/grafana-foundation-sdk/piechart';
import { PanelBuilder as BarChartBuilder } from '@grafana/grafana-foundation-sdk/barchart';
import { PanelBuilder as HeatmapBuilder } from '@grafana/grafana-foundation-sdk/heatmap';
import { PanelBuilder as HistogramBuilder } from '@grafana/grafana-foundation-sdk/histogram';
import { PanelBuilder as LogsBuilder } from '@grafana/grafana-foundation-sdk/logs';
import { PanelBuilder as TextBuilder } from '@grafana/grafana-foundation-sdk/text';
import { PanelBuilder as StateTimelineBuilder } from '@grafana/grafana-foundation-sdk/statetimeline';
import { PanelBuilder as StatusHistoryBuilder } from '@grafana/grafana-foundation-sdk/statushistory';
import { PanelBuilder as NodeGraphBuilder } from '@grafana/grafana-foundation-sdk/nodegraph';
import { PanelBuilder as GeoMapBuilder } from '@grafana/grafana-foundation-sdk/geomap';
import { PanelBuilder as XYChartBuilder } from '@grafana/grafana-foundation-sdk/xychart';
import { PanelBuilder as TrendBuilder } from '@grafana/grafana-foundation-sdk/trend';
import { PanelBuilder as CandlestickBuilder } from '@grafana/grafana-foundation-sdk/candlestick';

// Query builders (each exports DataqueryBuilder)
import { DataqueryBuilder as PromQueryBuilder } from '@grafana/grafana-foundation-sdk/prometheus';
import { DataqueryBuilder as LokiQueryBuilder } from '@grafana/grafana-foundation-sdk/loki';
import { DataqueryBuilder as TempoQueryBuilder } from '@grafana/grafana-foundation-sdk/tempo';

// Common types and sub-builders
import * as common from '@grafana/grafana-foundation-sdk/common';
```

---

## Dashboard Builder

```typescript
new DashboardBuilder(title: string)
  // Identity
  .uid(uid: string)
  .tags(tags: string[])
  .description(desc: string)

  // Behavior
  .editable()                    // allow editing in UI
  .readonly()                    // read-only in UI
  .refresh(interval: string)     // e.g. '30s', '1m', '5m'
  .tooltip(mode: DashboardCursorSync)  // Off, Crosshair, Tooltip

  // Time
  .time({ from: string, to: string })  // e.g. { from: 'now-24h', to: 'now' }
  .timezone(tz: string)                // 'browser', 'utc', or IANA tz

  // Variables
  .withVariable(builder)         // QueryVariableBuilder, CustomVariableBuilder, etc.

  // Layout
  .withRow(rowBuilder)           // RowBuilder
  .withPanel(panelBuilder)       // any panel builder

  // Links
  .link(linkBuilder)             // DashboardLinkBuilder

  // Annotations
  .annotation(annotationBuilder)

  // Build
  .build()                       // returns the dashboard object
```

---

## Panel Types

All panel builders share these common methods:

```typescript
// Every panel type
.title(title: string)
.description(desc: string)
.transparent()                         // transparent background
.datasource({ type: string, uid: string })
.withTarget(queryBuilder)              // add a query
.height(h: number)                     // grid height in rows
.span(w: number)                       // grid width out of 24
.unit(unit: string)                    // e.g. 'reqps', 'ms', 'percent', 'currencyUSD', 'short'
.min(n: number)
.max(n: number)
.decimals(n: number)
.noValue(text: string)                 // shown when no data
.links(links: PanelLink[])
.repeat(variableName: string)          // repeat panel for each variable value
.maxPerRow(n: number)                  // max panels per row when repeating
.thresholds(thresholdsConfigBuilder)
.overrideByName(name, properties[])
.overrideByRegexp(regexp, properties[])
.withTransformation(transformation)
```

### Stat Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/stat';

new PanelBuilder()
  .colorMode(common.BigValueColorMode.Background)  // None, Value, Background, BackgroundSolid
  .graphMode(common.BigValueGraphMode.Area)         // None, Line, Area
  .textMode(common.BigValueTextMode.Auto)           // Auto, Value, ValueAndName, Name, None
  .reduceOptions(new common.ReduceDataOptionsBuilder().calcs(['lastNotNull']))
  .orientation(common.VizOrientation.Auto)          // Auto, Horizontal, Vertical
```

### Timeseries Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/timeseries';

new PanelBuilder()
  .drawStyle(common.GraphDrawStyle.Line)             // Line, Bars, Points
  .lineInterpolation(common.LineInterpolation.Linear) // Linear, Smooth, StepBefore, StepAfter
  .lineWidth(n: number)                               // 0-10
  .fillOpacity(n: number)                              // 0-100
  .showPoints(common.VisibilityMode.Auto)             // Auto, Always, Never
  .pointSize(n: number)
  .gradientMode(common.GraphGradientMode.None)        // None, Opacity, Hue, Scheme
  .spanNulls(bool | number)                           // connect null gaps (or max gap in ms)
  .axisBorderShow(bool: boolean)
  .stacking(new common.StackingConfigBuilder().mode(common.StackingMode.Normal))  // None, Normal, Percent
  .legend(
    new common.VizLegendOptionsBuilder()
      .showLegend(true)
      .placement(common.LegendPlacement.Bottom)       // Bottom, Right
      .displayMode(common.LegendDisplayMode.List)      // List, Table, Hidden
  )
  .tooltip(
    new common.VizTooltipOptionsBuilder()
      .mode(common.TooltipDisplayMode.Multi)           // Single, Multi, None
      .sort(common.SortOrder.Descending)               // Ascending, Descending, None
  )
  .thresholdsStyle(
    new common.GraphThresholdsStyleConfigBuilder()
      .mode(common.GraphThresholdsStyleMode.Off)       // Off, Line, Area, LineAndArea, Dashed, DashedAndArea
  )
```

### Table Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/table';

new PanelBuilder()
  .filterable(true)               // column filtering
  .footer(footerBuilder)          // table footer with calculations
```

### Gauge Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/gauge';

new PanelBuilder()
  .reduceOptions(new common.ReduceDataOptionsBuilder().calcs(['lastNotNull']))
  .orientation(common.VizOrientation.Auto)
  .showThresholdLabels(true)
  .showThresholdMarkers(true)
```

### BarGauge Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/bargauge';

new PanelBuilder()
  .reduceOptions(new common.ReduceDataOptionsBuilder().calcs(['lastNotNull']))
  .orientation(common.VizOrientation.Horizontal)
  .displayMode(common.BarGaugeDisplayMode.Gradient)  // Basic, Gradient, Lcd
```

### PieChart Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/piechart';

new PanelBuilder()
  .reduceOptions(new common.ReduceDataOptionsBuilder().calcs(['lastNotNull']))
  .pieType(common.PieChartType.Pie)          // Pie, Donut
  .legend(
    new common.VizLegendOptionsBuilder()
      .showLegend(true)
      .placement(common.LegendPlacement.Right)
  )
```

### BarChart Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/barchart';

new PanelBuilder()
  .orientation(common.VizOrientation.Horizontal)
```

### Logs Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/logs';

new PanelBuilder()
  .showTime(true)
  .wrapLogMessage(true)
  .enableLogDetails(true)
  .prettifyLogMessage(false)
  .showCommonLabels(false)
  .showLabels(false)
  .sortOrder(common.LogsSortOrder.Descending)  // Ascending, Descending
  .dedupStrategy(common.LogsDedupStrategy.None) // None, Exact, Numbers, Signature
```

### Text Panel

```typescript
import { PanelBuilder } from '@grafana/grafana-foundation-sdk/text';

new PanelBuilder()
  .content('# Markdown content here')
  .mode(common.TextMode.Markdown)  // Markdown, HTML, Code
```

---

## Query Builders

### Prometheus

```typescript
import { DataqueryBuilder } from '@grafana/grafana-foundation-sdk/prometheus';

new DataqueryBuilder()
  .expr('sum(rate(http_requests_total{job=~"$service"}[$__rate_interval]))')
  .legendFormat('{{job}}')
  .refId('A')
  .instant()           // instant query (single value)
  .range()             // range query (time series) - default
  .format(PromQueryFormat.Table)  // for table panels
  .datasource({ type: 'prometheus', uid: 'prometheus' })
  .hide(true)          // hide this query's results
```

### Loki

```typescript
import { DataqueryBuilder } from '@grafana/grafana-foundation-sdk/loki';

new DataqueryBuilder()
  .expr('{namespace="x402", app=~"$service"}')
  .legendFormat('{{app}}')
  .refId('A')
  .maxLines(100)
  .queryType('range')       // 'range', 'instant', or 'stream'
  .editorMode('code')       // 'code' or 'builder'
  .datasource({ type: 'loki', uid: 'loki' })
```

**Loki query types:**
- Log query: `{namespace="x402", app="my-app"}` - returns log lines
- Metric query: `count_over_time({namespace="x402"} [5m])` - returns time series
- Use `| json` for JSON parsing, `| unwrap field_name` for numeric extraction

---

## Variable Builders

### Query Variable

```typescript
import { QueryVariableBuilder } from '@grafana/grafana-foundation-sdk/dashboard';

new QueryVariableBuilder('varName')
  .label('Display Label')
  .query('label_values(metric{filter="value"}, label_name)')
  .datasource({ type: 'prometheus', uid: 'prometheus' })
  .refresh(2)              // 1=on load, 2=on time range change
  .includeAll(true)        // add "All" option
  .allValue('.*')          // regex for "All"
  .multi(true)             // allow multiple selections
  .sort(1)                 // 0=disabled, 1=alpha asc, 2=alpha desc, 3=num asc, etc.
  .hide(0)                 // 0=visible, 1=hide label, 2=hide variable
```

### Custom Variable

```typescript
import { CustomVariableBuilder } from '@grafana/grafana-foundation-sdk/dashboard';

// Simple values
new CustomVariableBuilder('env')
  .label('Environment')
  .query('prod,staging,dev')
  .current({ text: 'prod', value: 'prod' })

// Key:value pairs (display text : actual value)
new CustomVariableBuilder('level')
  .label('Log Level')
  .query('All : .+, Error : error|fatal, Warning : warn')
  .current({ text: 'All', value: '.+' })
```

### Datasource Variable

```typescript
import { DatasourceVariableBuilder } from '@grafana/grafana-foundation-sdk/dashboard';

new DatasourceVariableBuilder('datasource')
  .label('Data Source')
  .type('prometheus')      // datasource plugin type
  .regex('/^(?!.*test).*$/')  // filter datasources
  .multi(false)
```

---

## Field Configuration

### Thresholds

```typescript
import { ThresholdsConfigBuilder } from '@grafana/grafana-foundation-sdk/dashboard';

// The first step MUST have value: null (it's the base/default color)
new ThresholdsConfigBuilder()
  .mode(common.ThresholdsMode.Absolute)  // or Percentage
  .steps([
    { value: null as any, color: 'green' },
    { value: 50, color: 'yellow' },
    { value: 80, color: 'red' },
  ])
```

### Value Mappings

```typescript
// Applied directly to panel as raw fieldConfig
// The SDK doesn't have typed builders for all mapping types
.withTransformation({
  id: 'configFromData',
  options: { /* ... */ }
})
```

### Field Overrides

```typescript
// Override by field name
.overrideByName('Revenue', [
  { id: 'color', value: { fixedColor: 'green', mode: 'fixed' } },
  { id: 'custom.fillOpacity', value: 10 },
])

// Override by regex
.overrideByRegexp('.*5..', [
  { id: 'color', value: { fixedColor: 'red', mode: 'fixed' } },
])

// Common override property IDs:
// 'color'              - { fixedColor: 'green', mode: 'fixed' }
// 'unit'               - 'ms', 'reqps', 'currencyUSD', etc.
// 'decimals'           - number
// 'custom.fillOpacity' - 0-100
// 'custom.lineWidth'   - 0-10
// 'custom.drawStyle'   - 'line', 'bars', 'points'
// 'custom.lineStyle'   - { fill: 'dash', dash: [10, 10] }
// 'custom.stacking'    - { mode: 'normal' }
```

---

## Common Enums

```typescript
import * as common from '@grafana/grafana-foundation-sdk/common';

// BigValueColorMode: None, Value, Background, BackgroundSolid
// BigValueGraphMode: None, Line, Area
// BigValueTextMode: Auto, Value, ValueAndName, Name, None
// GraphDrawStyle: Line, Bars, Points
// LineInterpolation: Linear, Smooth, StepBefore, StepAfter
// VisibilityMode: Auto, Always, Never
// GraphGradientMode: None, Opacity, Hue, Scheme
// StackingMode: None, Normal, Percent
// LegendPlacement: Bottom, Right
// LegendDisplayMode: List, Table, Hidden
// TooltipDisplayMode: Single, Multi, None
// SortOrder: Ascending, Descending, None
// ThresholdsMode: Absolute, Percentage
// VizOrientation: Auto, Horizontal, Vertical
// LogsSortOrder: Ascending, Descending
// LogsDedupStrategy: None, Exact, Numbers, Signature
// BarGaugeDisplayMode: Basic, Gradient, Lcd
// PieChartType: Pie, Donut
// GraphThresholdsStyleMode: Off, Line, Area, LineAndArea, Dashed, DashedAndArea
```

---

## Common Units

Frequently used unit strings (pass to `.unit()`):

| Unit | Description |
|------|-------------|
| `'short'` | Auto-scaled number |
| `'none'` | Raw number |
| `'percent'` | 0-100 percentage |
| `'percentunit'` | 0.0-1.0 percentage |
| `'reqps'` | Requests per second |
| `'ms'` | Milliseconds |
| `'s'` | Seconds |
| `'bytes'` | Bytes (auto IEC) |
| `'decbytes'` | Bytes (auto SI) |
| `'currencyUSD'` | US Dollars |
| `'ops'` | Operations per second |

---

## Go Quick Reference

Go follows the same builder pattern but with Go conventions (uppercase methods, pointers for nullable values).

```go
import (
    "github.com/grafana/grafana-foundation-sdk/go/cog"
    "github.com/grafana/grafana-foundation-sdk/go/common"
    "github.com/grafana/grafana-foundation-sdk/go/dashboard"
    "github.com/grafana/grafana-foundation-sdk/go/prometheus"
    "github.com/grafana/grafana-foundation-sdk/go/loki"
    "github.com/grafana/grafana-foundation-sdk/go/stat"
    "github.com/grafana/grafana-foundation-sdk/go/timeseries"
)

// Dashboard
builder := dashboard.NewDashboardBuilder("Title").
    Uid("my-uid").
    Tags([]string{"tag"}).
    Editable().
    Refresh("30s").
    Time("now-24h", "now").
    Timezone(common.TimeZoneBrowser)

// Prometheus query
prometheus.NewDataqueryBuilder().
    Expr(`sum(rate(http_requests_total{job=~"$service"}[5m]))`).
    LegendFormat("{{job}}")

// Stat panel
stat.NewPanelBuilder().
    Title("Requests").
    Datasource(dashboard.DataSourceRef{
        Type: cog.ToPtr("prometheus"),
        Uid:  cog.ToPtr("prometheus"),
    }).
    WithTarget(query).
    Height(4).Span(6)

// Thresholds (note: first step Value is nil)
dashboard.NewThresholdsConfigBuilder().
    Mode(dashboard.ThresholdsModeAbsolute).
    Steps([]dashboard.Threshold{
        {Value: nil, Color: "green"},
        {Value: cog.ToPtr[float64](80), Color: "red"},
    })

// Build and serialize
dash, err := builder.Build()
jsonBytes, _ := json.MarshalIndent(dash, "", "  ")
```

**Go gotchas:**
- Use `cog.ToPtr[T](value)` for nullable pointer fields (thresholds, datasource refs)
- Some fields require wrapper types: `dashboard.StringOrMap{String: cog.ToPtr(val)}`
- `Build()` returns `(Dashboard, error)` - always check the error
- Variable `Current` uses `dashboard.VariableOption` with `dashboard.StringOrArrayOfString`
