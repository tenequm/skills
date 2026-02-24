# Biome Lint Rules Reference

Biome 2.4 ships 340+ rules organized into groups. This reference covers the most impactful rules by category with examples of what each catches.

## Rule Groups

| Group | Purpose |
|-------|---------|
| `correctness` | Catches definite bugs and incorrect code |
| `suspicious` | Flags code that is likely wrong or confusing |
| `style` | Enforces consistent coding patterns |
| `complexity` | Reduces unnecessary complexity |
| `a11y` | Accessibility violations (JSX and HTML) |
| `nursery` | Experimental rules - may change between versions |

## Correctness Rules

Rules that catch definite bugs. Most are recommended by default.

### noUnusedVariables

Flags declared variables that are never read:

```ts
// ERROR
const unused = 42;
function helper() { return 1; } // never called

// VALID - prefixed with underscore
const _intentionallyUnused = 42;
```

### noUnusedImports

Removes imports that are not referenced:

```ts
// ERROR
import { useState, useEffect } from "react"; // useEffect never used

// VALID
import { useState } from "react";
```

### noUnusedFunctionParameters

**Not recommended by default** - must be explicitly enabled. Flags function parameters that are never used in the body:

```ts
// ERROR
function greet(name: string, age: number) {
  return `Hello, ${name}`;
  // age is never used
}

// VALID - prefix with underscore
function greet(name: string, _age: number) {
  return `Hello, ${name}`;
}
```

### useHookAtTopLevel

Ensures React hooks are only called at the top level of components or custom hooks:

```tsx
// ERROR - hook inside condition
function Component({ show }: { show: boolean }) {
  if (show) {
    const [value, setValue] = useState(0); // conditional hook call
  }
}

// VALID
function Component({ show }: { show: boolean }) {
  const [value, setValue] = useState(0);
  if (!show) return null;
  return <div>{value}</div>;
}
```

### useExhaustiveDependencies

Ensures effect dependencies are complete:

```tsx
// ERROR - missing dependency
function Component({ id }: { id: string }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetchData(id).then(setData);
  }, []); // id is missing from deps
}

// VALID
useEffect(() => {
  fetchData(id).then(setData);
}, [id]);
```

### noImportCycles (project domain)

Detects circular imports between modules:

```ts
// a.ts
import { b } from "./b"; // ERROR if b.ts imports from a.ts

// b.ts
import { a } from "./a"; // circular dependency
```

### noUnresolvedImports (project domain)

Reports imports that cannot be resolved:

```ts
// ERROR - module doesn't exist
import { foo } from "./nonexistent";
```

## Suspicious Rules

Rules that flag code likely to be wrong.

### noConsole

Flags `console.*` calls. Disable in logger modules, keep for production code:

```ts
// ERROR
console.log("debug");
console.warn("something");

// VALID - use a logger
import { logger } from "./logger";
logger.info("debug");
```

### noDebugger

Flags `debugger` statements left in code:

```ts
// ERROR
function process() {
  debugger; // should not be in production
  return result;
}
```

### noDoubleEquals

Enforces strict equality. By default, `== null` is exempt (`ignoreNull: true`) since it's an idiomatic shorthand for `=== null || === undefined`:

```ts
// VALID - == null is allowed by default (catches both null and undefined)
if (value == null) {}

// ERROR - non-null loose equality
if (count == 0) {}

// VALID
if (count === 0) {}
```

### noExplicitAny

Flags explicit `any` type annotations:

```ts
// ERROR
function process(data: any) {}
const items: any[] = [];

// VALID
function process(data: unknown) {}
const items: string[] = [];
```

### noImplicitAnyLet

Flags `let` declarations without type or initializer:

```ts
// ERROR - implicitly `any`
let value;

// VALID
let value: string;
let value = "";
```

### noThenProperty

Flags objects with a `then` property (accidental thenable):

```ts
// ERROR - this object is accidentally thenable
const obj = {
  then: () => {},
  data: "value",
};
```

### noFocusedTests

Catches `.only()` left in test files:

```ts
// ERROR
describe.only("suite", () => {});
it.only("test", () => {});
test.only("test", () => {});

// VALID
describe("suite", () => {});
it("test", () => {});
```

### noReactForwardRef

Flags deprecated `React.forwardRef` - use `ref` prop directly in React 19:

```tsx
// ERROR - deprecated pattern
const Input = forwardRef<HTMLInputElement, Props>((props, ref) => {
  return <input ref={ref} {...props} />;
});

// VALID - React 19 pattern
function Input({ ref, ...props }: Props & { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...props} />;
}
```

### noDuplicateDependencies

Catches duplicate entries in package.json:

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react": "^18.0.0"
  }
}
```

### noDeprecatedImports

Flags imports of deprecated symbols based on JSDoc `@deprecated` tags.

## Style Rules

Rules that enforce consistent patterns.

### useImportType

Enforces `import type` for type-only imports:

```ts
// ERROR
import { User } from "./types"; // only used as type

// VALID
import type { User } from "./types";
```

### useNodejsImportProtocol

Requires `node:` prefix for Node.js built-in imports:

```ts
// ERROR
import { readFile } from "fs";
import path from "path";

// VALID
import { readFile } from "node:fs";
import path from "node:path";
```

### useConst

Flags `let` that is never reassigned:

```ts
// ERROR
let name = "Alice"; // never reassigned

// VALID
const name = "Alice";
```

### useComponentExportOnlyModules

Ensures files with React components only export components (no mixed exports). Turn off for barrel files.

### useForOf

Prefers `for...of` over indexed `for` loops:

```ts
// ERROR
for (let i = 0; i < items.length; i++) {
  console.log(items[i]);
}

// VALID
for (const item of items) {
  console.log(item);
}
```

### noRestrictedGlobals

Bans specific global variables with custom messages:

```json
{
  "style": {
    "noRestrictedGlobals": {
      "level": "error",
      "options": {
        "deniedGlobals": {
          "Buffer": "Use Uint8Array for browser compatibility.",
          "fetch": "Use the project's HTTP client instead."
        }
      }
    }
  }
}
```

### useConsistentArrowReturn

Enforces consistent arrow function return style:

```ts
// ERROR - inconsistent
const fn1 = () => { return 1; };
const fn2 = () => 2;

// VALID - consistent concise body
const fn1 = () => 1;
const fn2 = () => 2;
```

## Complexity Rules

Rules that reduce unnecessary complexity.

### noForEach

Prefers `for...of` over `.forEach()`:

```ts
// ERROR
items.forEach((item) => {
  process(item);
});

// VALID
for (const item of items) {
  process(item);
}
```

### noUselessFragments

Removes unnecessary React fragments:

```tsx
// ERROR
return <>{child}</>;

// VALID - single child doesn't need fragment
return child;

// VALID - multiple children need fragment
return (
  <>
    {child1}
    {child2}
  </>
);
```

### noStaticOnlyClass

Flags classes with only static members - use plain objects or functions instead:

```ts
// ERROR
class Utils {
  static format(date: Date) { return date.toISOString(); }
  static parse(str: string) { return new Date(str); }
}

// VALID
function formatDate(date: Date) { return date.toISOString(); }
function parseDate(str: string) { return new Date(str); }
```

### noUselessSwitchCase

Flags switch cases that fall through with no code:

```ts
// ERROR
switch (action) {
  case "a":
  case "b":
    break;
  default:
    break; // useless - same as no default
}
```

### useMaxParams

Enforces a maximum number of function parameters (default: 3):

```ts
// ERROR - too many params
function createUser(name: string, email: string, age: number, role: string, active: boolean) {}

// VALID - use an options object
function createUser(options: CreateUserOptions) {}
```

### noUselessUndefined

Flags unnecessary `undefined`:

```ts
// ERROR
let x = undefined;
return undefined;

// VALID
let x;
return;
```

## Accessibility Rules (a11y)

### useAltText

Requires `alt` on `<img>` elements:

```tsx
// ERROR
<img src="/photo.jpg" />

// VALID
<img src="/photo.jpg" alt="Team photo" />
<img src="/decorative.svg" alt="" /> // intentionally empty for decorative
```

### useButtonType

Requires `type` attribute on buttons:

```tsx
// ERROR - defaults to "submit" which may be unintended
<button onClick={handleClick}>Click</button>

// VALID
<button type="button" onClick={handleClick}>Click</button>
<button type="submit">Submit</button>
```

### useValidAnchor

Ensures anchors have proper href:

```tsx
// ERROR
<a href="#">Link</a>
<a href="javascript:void(0)">Link</a>

// VALID
<a href="/page">Link</a>
<button type="button" onClick={handleClick}>Link</button>
```

### useHtmlLang

Requires `lang` attribute on `<html>`:

```html
<!-- ERROR -->
<html>

<!-- VALID -->
<html lang="en">
```

### noPositiveTabindex

Flags `tabindex` values greater than 0:

```tsx
// ERROR - disrupts natural tab order
<div tabIndex={5}>Content</div>

// VALID
<div tabIndex={0}>Focusable</div>
<div tabIndex={-1}>Programmatically focusable</div>
```

### useAriaPropsForRole

Ensures elements with ARIA roles have required ARIA properties.

### HTML accessibility rules (v2.4)

Biome 2.4 added 15 HTML-specific a11y rules that also work with Vue, Svelte, and Astro files: `useIframeTitle`, `noRedundantAlt`, `noSvgWithoutTitle`, `noDistractingElements`, `noAccessKey`, and more.

## Type-Aware Rules (types domain)

Require the `types` domain to be enabled. All currently in nursery.

### noFloatingPromises

```ts
// ERROR - promise not handled
async function save() {
  fetch("/api/save", { method: "POST" });
}

// VALID
async function save() {
  await fetch("/api/save", { method: "POST" });
}
```

### noMisusedPromises

```ts
// ERROR - promise in condition (always truthy)
const promise = Promise.resolve("value");
if (promise) { /* always executes */ }

// ERROR - async callback where sync expected
[1, 2, 3].filter(async (n) => {
  const result = await check(n);
  return result;
});
```

### useAwaitThenable

```ts
// ERROR - awaiting non-thenable
const value = "hello";
const result = await value; // string is not thenable

// VALID
const result = await Promise.resolve("hello");
```

### noUnnecessaryConditions

```ts
// ERROR - condition is always true
const x: string = "hello";
if (x) {} // string literal is always truthy
```

## React Domain Rules

Enabled via `"react": "recommended"` in domains.

### useExhaustiveDependencies

See Correctness section above.

### useHookAtTopLevel

See Correctness section above.

### noChildrenProp

```tsx
// ERROR
<Component children={<div />} />

// VALID
<Component><div /></Component>
```

## Test Domain Rules

Enabled via `"test": "recommended"` in domains.

### noFocusedTests

See Suspicious section above.

### noConditionalExpect (v2.4 nursery)

```ts
// ERROR - assertion may not run
test("conditional", async () => {
  if (someCondition) {
    await expect(page).toHaveTitle("Title");
  }
});

// VALID - always runs
test("unconditional", async () => {
  await expect(page).toHaveTitle("Title");
});
```

## Assist Actions

Actions without diagnostics - not lint rules but code transformations.

### organizeImports

Sorts and merges imports. See SKILL.md import organizer section.

### useSortedKeys

Sorts object literal keys alphabetically:

```ts
// Before
const config = { zebra: 1, apple: 2, mango: 3 };

// After
const config = { apple: 2, mango: 3, zebra: 1 };
```

### useSortedAttributes

Sorts JSX attributes:

```tsx
// Before
<Component zebra="z" apple="a" mango="m" />

// After
<Component apple="a" mango="m" zebra="z" />
```

### useSortedInterfaceMembers (v2.4)

Sorts TypeScript interface members:

```ts
// Before
interface User {
  z: string;
  a: number;
  m: boolean;
}

// After
interface User {
  a: number;
  m: boolean;
  z: string;
}
```

### noDuplicateClasses (v2.4)

Removes duplicate CSS classes in JSX and HTML:

```tsx
// Before
<div className="flex p-4 flex" />

// After
<div className="flex p-4" />
```

Works with `class`, `className`, and utility functions (`clsx`, `cn`, `cva`).
