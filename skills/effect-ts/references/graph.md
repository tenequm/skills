# Graph (`effect/Graph`)

`Graph` is Effect's built-in graph data structure - indexed **nodes** and **edges** that both carry your own data, in **directed** or **undirected** form. Reach for it to model dependency graphs, build/task ordering, routing and shortest paths, cycle detection, or any network of relationships without hand-rolling BFS/DFS/Dijkstra.

Import from `"effect"`:

```typescript
import { Graph } from "effect"
```

Nodes and edges are identified by `Graph.NodeIndex` / `Graph.EdgeIndex`, which are **plain numbers** - stable identifiers, not array offsets. A removed index is not reused.

## Building a Graph

Graphs are immutable. Construct one by mutating a scoped-mutable draft inside the builder callback; `addNode` returns the new node's index, which you pass to `addEdge`.

```typescript
import { Graph } from "effect"

// Directed graph of string nodes and string edge labels
const graph = Graph.directed<string, string>((mutable) => {
  const a = Graph.addNode(mutable, "A")
  const b = Graph.addNode(mutable, "B")
  const c = Graph.addNode(mutable, "C")
  Graph.addEdge(mutable, a, b, "A->B")
  Graph.addEdge(mutable, b, c, "B->C")
})

// Undirected variant: Graph.undirected<N, E>((mutable) => { ... })
```

Update an existing immutable graph with `Graph.mutate` (returns a new graph; the original is untouched):

```typescript
const withExtra = Graph.mutate(graph, (mutable) => {
  const d = Graph.addNode(mutable, "D")
  Graph.addEdge(mutable, 2, d, "C->D") // 2 = index of node "C"
})
```

Other mutations (all inside a builder/`mutate` callback): `updateNode`, `updateEdge`, `removeNode`, `removeEdge`, `mapNodes`, `mapEdges`, `filterNodes`, `filterEdges`, `filterMapNodes`, `filterMapEdges`, `reverse`.

## Reading a Graph

```typescript
import { Graph } from "effect"

Graph.nodeCount(graph)          // number of nodes
Graph.edgeCount(graph)          // number of edges
Graph.getNode(graph, 0)         // Option<N> for the node at that index
Graph.hasNode(graph, 0)         // boolean
Graph.getEdge(graph, 0)         // Option<Edge<E>>
Graph.findNode(graph, (n) => n === "B")   // Option<NodeIndex>
Graph.findEdges(graph, (e) => e.startsWith("A"))
```

`Graph.nodes(graph)` and `Graph.edges(graph)` return **walkers** you iterate with the walker helpers below. Neighbor queries: `Graph.neighbors`, `Graph.successors` (outgoing), `Graph.predecessors` (incoming). `Graph.neighborsDirected` is deprecated (beta.80) - use `successors`/`predecessors`.

## Traversal

`dfs`, `bfs`, `topo` (topological sort, Kahn's algorithm), and `dfsPostOrder` return a lazy **walker**. Turn it into values with `Graph.indices` (node indices), `Graph.values` (node data), or `Graph.entries` (`[index, data]` pairs).

```typescript
import { Graph } from "effect"

// Depth-first from a start node
for (const idx of Graph.indices(Graph.dfs(graph, { start: [0] }))) {
  console.log(idx)
}

// Breadth-first; omit start to walk all nodes
for (const data of Graph.values(Graph.bfs(graph))) {
  console.log(data)
}

// Topological order (only valid on a DAG)
const order = Array.from(Graph.indices(Graph.topo(graph)))
```

`dfs`/`bfs` accept `{ start, direction }` where `direction` is `"outgoing"` (default) or `"incoming"`; `topo` accepts `{ initials }`.

## Analysis

```typescript
import { Graph } from "effect"

Graph.isAcyclic(graph)                    // boolean - true if no cycles (a DAG)
Graph.isBipartite(graph)                  // boolean
Graph.connectedComponents(graph)          // Array<Array<NodeIndex>>
Graph.stronglyConnectedComponents(graph)  // Array<Array<NodeIndex>> (directed)
```

## Shortest Paths

`dijkstra` finds the cheapest path between two nodes; `cost` maps each edge's data to a **non-negative** weight. It returns `Option<PathResult<E>>` - `Option.none()` when the target is unreachable.

```typescript
import { Graph } from "effect"

const weighted = Graph.directed<string, number>((mutable) => {
  const a = Graph.addNode(mutable, "A")
  const b = Graph.addNode(mutable, "B")
  const c = Graph.addNode(mutable, "C")
  Graph.addEdge(mutable, a, b, 3)
  Graph.addEdge(mutable, b, c, 4)
})

const result = Graph.dijkstra(weighted, {
  source: 0,
  target: 2,
  cost: (edgeData) => edgeData
})

if (result._tag === "Some") {
  console.log(result.value.path)     // [0, 1, 2]
  console.log(result.value.distance) // 7
  console.log(result.value.costs)    // [3, 4] - edge data along the path
}
```

Related solvers: `Graph.astar` (heuristic-guided), `Graph.bellmanFord` (allows negative edge weights), `Graph.floydWarshall` (all-pairs shortest paths).

## Visualization

`Graph.toGraphViz(graph, options)` and `Graph.toMermaid(graph, options)` render the graph as DOT or Mermaid diagram source - useful for debugging or docs.

## When to Use

Prefer `Graph` when relationships between entities are the core of the problem (ordering, reachability, routing, cycle detection). For a plain adjacency you only ever look up once, a `Map`/`Record` is simpler. `Graph` is a data structure, not an `Effect` - its operations are pure and synchronous; wrap them in `Effect.sync` only if you need them inside an effectful pipeline.
