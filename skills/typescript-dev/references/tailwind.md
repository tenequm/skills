# Tailwind CSS v4

Utility-first styling, CSS-first configuration. Tailwind **v4.3** (latest `4.3.0`) configures everything in CSS - there is no `tailwind.config.js`. In a Vite project the integration is the `@tailwindcss/vite` plugin (no PostCSS config). For shadcn/ui component authoring see [shadcn.md](shadcn.md).

## CSS-first configuration

Everything lives in your CSS entry. There is no JS/TS config file - migrate any old config into CSS:

- `theme.extend.colors` -> `@theme { --color-*: ... }`
- `plugins` -> `@plugin "..."` or `@utility`
- `content` -> `@source "..."`
- `tailwindcss-animate` -> `@import "tw-animate-css"`
- `@layer utilities` -> `@utility name { ... }`

```css
@import "tailwindcss";

@utility tab-highlight-none { -webkit-tap-highlight-color: transparent; }
@custom-variant pointer-fine (@media (pointer: fine));
@source not "./legacy";
```

The `@import "tailwindcss";` line is mandatory - the Vite plugin alone emits nothing without it. A missing import is the classic "Tailwind produces no styles" bug.

## Theming with CSS variables

shadcn/ui maps semantic CSS variables to Tailwind utilities. Define variables under `:root` / `.dark`, then bridge them with `@theme inline`:

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.97 0 0);
  --border: oklch(0.922 0 0);
  --radius: 0.5rem;
}
.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
}

@theme inline {
  --color-background: var(--background);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
}
```

**`@theme` vs `@theme inline`:** plain `@theme` defines static tokens (overridable by plugins); `@theme inline` references CSS variables so the utility *follows* dark-mode changes. Use `inline` whenever a token points at a `var(--...)` that flips between `:root` and `.dark`.

## Critical rules

### Semantic tokens, paired foreground

```tsx
<div className="bg-primary text-primary-foreground">    // respects theme + dark mode
<div className="bg-blue-500 text-white">                // breaks theming - avoid
```

Always pair `bg-*` with the matching `text-*-foreground`. Background utilities omit the `-background` suffix (`bg-muted text-muted-foreground`).

### Never build class names dynamically

```tsx
<div className={`bg-${color}-500`}>                      // scanner can't see it - no CSS emitted
const map = { red: "bg-red-500", blue: "bg-blue-500" } as const
<div className={map[color]}>                             // complete literal strings
```

### `cn()` merge order

Defaults first, consumer `className` last, so tailwind-merge's last-wins lets callers override:

```tsx
className={cn(buttonVariants({ variant, size }), className)}   // correct
```

### Transition only what changes

`transition-all` thrashes layout. Name the properties, and respect reduced motion:

```tsx
<div className="transition-colors duration-200">
<div className="motion-safe:animate-fade-in">
```

## Layout and responsiveness

Mobile-first breakpoints; container queries are first-class in v4 (no plugin):

```tsx
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
<div className="@container">
  <div className="grid gap-4 @sm:grid-cols-2 @lg:grid-cols-3">  // responds to container, not viewport
</div>
```

Dark mode: prefer semantic colors (auto-flip) over manual `dark:` overrides. Use `next-themes` for the toggle (`attribute="class"`), and add `suppressHydrationWarning` to `<html>` to avoid a flash.

## Version-specific features

### v4.1 / v4.2

```tsx
<h1 className="text-shadow-sm">                          // text shadows (4.1)
<div className="mask-linear-to-b">                       // gradient masks (4.1)
<input className="user-valid:border-success user-invalid:border-destructive" /> // (4.1)
<div className="pbs-4 pbe-8 mbs-2 border-bs-2">          // logical block props (4.2)
<div className="bg-mauve-100 text-olive-900">            // new palettes: mauve/olive/mist/taupe (4.2)
```

The positioning utilities `start-*`/`end-*` are **deprecated** in favor of `inset-s-*`/`inset-e-*` (don't confuse with logical padding `ps-*`/`pe-*`, which are fine).

### v4.3 (current)

```tsx
<div className="scrollbar-thin scrollbar-thumb-muted scrollbar-gutter-stable"> // scrollbar utils
<div className="@container-size">                        // size container for cqb/cqh units
<img className="zoom-110">                               // CSS zoom utilities
<pre className="tab-4">                                  // tab-size
```

In CSS you can now stack and group `@variant`: `@variant hover:focus { ... }` and `@variant hover, focus { ... }`, and pass `--default(...)` to `--value(...)`/`--modifier(...)` in custom functional utilities.

### Animations

```css
@import "tw-animate-css";
```

```tsx
<div className="animate-fade-in">
```

## OKLCH colors

shadcn/ui colors use `oklch(lightness chroma hue)`: lightness 0-1, chroma 0-0.4 (0 = gray), hue 0-360. OKLCH gives perceptually uniform lightness, so dark-mode variants are easy to derive by adjusting L. Base neutral palettes: Neutral, Zinc, Slate, Stone, Gray.

## Notes

- A first-class `@tailwindcss/webpack` loader exists (added v4.2) for Next.js/webpack/Turbopack projects - relevant if you're not on Vite.
- If you lint CSS with Biome, enable `css.parser.tailwindDirectives` so it understands `@theme`/`@utility`/`@apply` (see [biome.md](biome.md)).

## Troubleshooting

- **Colors not updating:** confirm the variable is in your CSS, `@theme inline` includes the mapping, then clear the build cache.
- **`tailwind.config.js` present:** delete it; run `npx @tailwindcss/upgrade` to migrate to CSS-first.
- **Classes not detected:** check `@source` covers your component paths and that no class name is constructed dynamically.

## Resources

- Docs: https://tailwindcss.com/docs - v4.3 blog: https://tailwindcss.com/blog/tailwindcss-v4-3
- Vite plugin: https://tailwindcss.com/docs/installation/using-vite
