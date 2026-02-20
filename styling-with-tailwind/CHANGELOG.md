## 0.3.1 (2026-02-20)

### 🩹 Fixes

- **styling-with-tailwind:** use semantic tokens in user-valid/user-invalid example ([f7f0090](https://github.com/tenequm/claude-plugins/commit/f7f0090))
- **styling-with-tailwind:** use semantic text-success instead of text-green-500 ([92c65e8](https://github.com/tenequm/claude-plugins/commit/92c65e8))

## 0.3.0 (2026-02-20)

### 🚀 Features

- **styling-with-tailwind:** add critical rules, pitfalls, and v4-only enforcement ([6fbd4bc](https://github.com/tenequm/claude-plugins/commit/6fbd4bc))
- migrate from Changesets to Nx Release ([06aaeb3](https://github.com/tenequm/claude-plugins/commit/06aaeb3))
- add styling-with-tailwind plugin ([7e81b47](https://github.com/tenequm/claude-plugins/commit/7e81b47))

# styling-with-tailwind-skill

## 0.1.0

### Minor Changes

- 7e81b47: Initial release of Tailwind CSS and shadcn/ui styling skill

  - **Comprehensive Tailwind CSS guide**: Covers utility-first styling with modern patterns

    - CSS variables theming with OKLCH colors for better color perception
    - Component variants using class-variance-authority (CVA)
    - Responsive design patterns (mobile-first breakpoints)
    - Dark mode implementation with next-themes
    - Tailwind v4 features (@theme directive, size utilities, animations)
    - **NEW**: Tailwind v4.1 features (text-shadow, mask utilities, colored drop-shadow, overflow-wrap)

  - **shadcn/ui component patterns**: Production-ready component library patterns

    - Radix UI primitives integration
    - asChild composition pattern for polymorphic components
    - Complete form handling with React Hook Form and Zod
    - Data tables with TanStack Table
    - Toast notifications with Sonner
    - **NEW**: October 2025 components (Field, Item, Spinner, Button Group)

  - **Progressive disclosure structure**: Main SKILL.md (490 lines) with detailed reference files

    - components.md: 830 lines covering all component patterns
    - theming.md: 342 lines with complete color system reference

  - **Quality**: Validated with 10/10 score, all examples tested and working
