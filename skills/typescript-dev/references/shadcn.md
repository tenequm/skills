# shadcn/ui

Copy-in component patterns built on Tailwind v4 and a primitive library (Radix UI or Base UI). shadcn/ui is not a dependency you import - the CLI (latest `4.11.0`) writes component source into your project, which you then own and edit. For the Tailwind layer (theming, tokens) see [tailwind.md](tailwind.md).

## Component authoring pattern

The canonical shadcn component is a **plain function** with `data-slot` for styling hooks, native props via `React.ComponentProps`, and variants via CVA. No `forwardRef` (React 19 - `ref` is a prop). Recent components also expose `data-variant`/`data-size` and a wider size scale.

```tsx
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:ring-1 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: { default: "h-9 px-4 py-2", sm: "h-8 px-3", lg: "h-10 px-8", icon: "size-9" },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
)

function Button({
  className, variant, size, ...props
}: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants>) {
  return (
    <button
      data-slot="button"
      data-variant={variant}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
}
```

The `cn` helper merges class names with conflict resolution:

```ts
// src/lib/utils.ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
```

## CLI

```bash
pnpm dlx shadcn@latest init        # scaffold config + tokens + lib/utils
pnpm dlx shadcn@latest add button card form   # add components
pnpm dlx shadcn@latest add button --overwrite # update an existing component
```

`init` adds `@import "shadcn/tailwind.css"` to your global CSS (custom variants like `data-open:` / `data-closed:` and utilities like `no-scrollbar`). `shadcn eject` inlines that file if you want full control.

- **`create` is an alias of `init`** (not a separate command). `--defaults` resolves to `--template=next --preset=nova`.
- **`--base radix | base`** chooses the primitive library at init; docs are split per base.
- **`--pointer`** opts into Tailwind v4's `cursor: default` button behavior (v4 switched buttons away from `cursor: pointer`).
- **`--rtl`** / `migrate rtl` set up right-to-left support (rewrites `ml-4` -> `ms-4`, `text-left` -> `text-start`); `components.json` carries `rtl: true`.
- **`shadcn docs`** fetches component documentation/API for an agent to read; `--base` selects radix or base.

### Registries

Add from community/private registries, including any public GitHub repo as a **source registry** (no build step):

```bash
pnpm dlx shadcn@latest add @acme/button          # named registry
pnpm dlx shadcn@latest add username/repo/item     # GitHub source registry
pnpm dlx shadcn@latest registry validate          # validate before publishing
```

Discover items with `search` (aliased as `list`). The registries arg is optional - omit it to
search every registry in `components.json`:

```bash
pnpm dlx shadcn@latest search @acme -q button -t ui   # filter by type: ui, block, hook (CSV)
pnpm dlx shadcn@latest search --json                  # machine-readable output
```

`--type`/`-t` and `--json` are new in CLI 4.11; before 4.11 `search` always printed JSON, so if
you script it, pass `--json` explicitly now that the default is human-readable.

Presets are encoded codes that rewrite component code (not just colors): `shadcn preset decode <code>`, `shadcn apply <code> --only theme`.

### Visual styles

`init`/`create` offers built-in visual styles that rewrite component code (not only CSS variables): **Vega** (classic), **Nova** (compact), **Maia** (soft/rounded), **Lyra** (boxy/sharp, mono fonts), **Mira** (dense), plus newer **Luma** and **Rhea**. Available for both Radix and Base UI.

### MCP server

```bash
pnpm dlx shadcn@latest mcp init    # exposes registry/search/add to an AI client
```

## Primitives: Radix vs Base UI

Both are fully supported and selectable at init. Radix now uses the **unified `radix-ui` package** (not per-component `@radix-ui/react-*`):

```tsx
import { Slot } from "radix-ui"
```

`migrate radix` rewrites old `@radix-ui/react-*` imports to the unified package. Base UI is a co-equal rebuild of every component with the same abstraction.

## Common patterns

### Card

```tsx
<div className="rounded-xl border bg-card text-card-foreground shadow">
  <div className="flex flex-col space-y-1.5 p-6">
    <h3 className="font-semibold leading-none tracking-tight">Title</h3>
    <p className="text-sm text-muted-foreground">Description</p>
  </div>
  <div className="p-6 pt-0">Content</div>
</div>
```

### Form field (with Zod)

Pair shadcn form components with React Hook Form + Zod, or React 19 Actions + `useActionState` for server-driven validation (see [react.md](react.md) and [typescript.md](typescript.md) for the Zod v4 pattern).

### Accessibility

```tsx
<button className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
<span className="sr-only">Close dialog</span>
<button className="disabled:cursor-not-allowed disabled:opacity-50" disabled>
```

## Troubleshooting

- **Dark mode flash:** add `suppressHydrationWarning` to `<html>`; ensure the theme provider uses `attribute="class"`.
- **Component overwritten on `add`:** you own the file - re-running `add` without `--overwrite` skips existing files.

## Resources

- Docs: https://ui.shadcn.com/docs - CLI: https://ui.shadcn.com/docs/cli
- Changelog: https://ui.shadcn.com/docs/changelog - Registries: https://ui.shadcn.com/docs/registry
