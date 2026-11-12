# React with WXT

Verified against `wxt@0.21.5`, `@wxt-dev/module-react@1.2.2`, React 19, Tailwind CSS 4 and zustand 5.

## Setup

New project: `npx wxt@latest init my-extension -t react`.

Existing WXT project:

```bash
npm i react react-dom
npm i -D @wxt-dev/module-react @types/react @types/react-dom
```

```ts
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  modules: ['@wxt-dev/module-react'],
});
```

```json
{
  "extends": "./.wxt/tsconfig.json",
  "compilerOptions": {
    "allowImportingTsExtensions": true,
    "jsx": "react-jsx"
  }
}
```

The module adds the Vite React plugin and auto-imports React's APIs (`useState`, `useEffect`, ...), so components need no React import. Files in `hooks/` and `components/` are auto-imported too.

## Popup, options and side panel pages

Each page is a folder in `entrypoints/` with an `index.html` that loads a module script (see the HTML example in `SKILL.md`).

```tsx
// entrypoints/popup/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './style.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

```tsx
// entrypoints/popup/App.tsx
export default function App() {
  const [url, setUrl] = useState<string>();

  useEffect(() => {
    void browser.tabs
      .query({ active: true, currentWindow: true })
      .then(([tab]) => setUrl(tab?.url));
  }, []);

  return <p>{url ?? 'No active tab'}</p>;
}
```

Reading `tab.url` needs the `activeTab` or `tabs` permission. A popup is destroyed every time it closes, so keep anything that must survive in `storage`.

Use hash-based routing (`createHashRouter`) inside extension pages; the page URL is `chrome-extension://{id}/popup.html` and there is no server to resolve other paths.

## Storage hook

```ts
// hooks/useStorageItem.ts
import type { WxtStorageItem } from '#imports';

export function useStorageItem<T>(item: WxtStorageItem<T, Record<string, unknown>>) {
  const [value, setValue] = useState<T>(item.fallback);

  useEffect(() => {
    void item.getValue().then(setValue);
    return item.watch((newValue) => setValue(newValue));
  }, [item]);

  return [value, (next: T) => item.setValue(next)] as const;
}
```

```tsx
// with `theme` defined via storage.defineItem in utils/storage.ts
const [currentTheme, setTheme] = useStorageItem(theme);
```

`item.watch` fires for writes from any context, so the popup, options page and content scripts stay in sync without extra messaging.

## Content script UI

Put the component next to the content script, inside its folder. A loose `.tsx` file directly in `entrypoints/` would be built as its own entrypoint.

```
entrypoints/
  overlay.content/
    index.tsx
    App.tsx
    style.css
```

```tsx
// entrypoints/overlay.content/index.tsx
import './style.css';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';

export default defineContentScript({
  matches: ['*://*.example.com/*'],
  cssInjectionMode: 'ui',

  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'example-overlay',
      position: 'inline',
      anchor: 'body',
      onMount: (container) => {
        const wrapper = document.createElement('div');
        container.append(wrapper);
        const root = ReactDOM.createRoot(wrapper);
        root.render(<App />);
        return root;
      },
      onRemove: (root) => {
        root?.unmount();
      },
    });

    ui.mount();
  },
});
```

Shadow-root UIs do not hot-reload; WXT reloads the content script instead. Use `createIframeUi` with an unlisted HTML page when HMR matters more than access to the page's DOM.

## Tailwind CSS 4

```bash
npm i tailwindcss @tailwindcss/vite
```

```ts
// wxt.config.ts
import { defineConfig } from 'wxt';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  modules: ['@wxt-dev/module-react'],
  vite: () => ({
    plugins: [tailwindcss()],
  }),
});
```

```css
/* assets/tailwind.css */
@import "tailwindcss";
```

Import that file from each page's `main.tsx` and from each content script that renders UI (`import '~/assets/tailwind.css'`, with `cssInjectionMode: 'ui'`). There is no `tailwind.config.js`, no `tailwindcss init` and no `@tailwind base` directive in v4.

**`rem` in injected UI.** Tailwind sizes are in `rem`, which follow the host page's `<html>` font size, so a shadow-root UI changes scale between sites. Convert to `px` at build time:

```bash
npm i -D postcss-rem-to-responsive-pixel
```

```js
// postcss.config.mjs
import remToPx from 'postcss-rem-to-responsive-pixel';

export default {
  plugins: [
    remToPx({
      rootValue: 16,
      propList: ['*'],
      transformUnit: 'px',
    }),
  ],
};
```

## shadcn/ui

After Tailwind is set up, run `wxt prepare` so `.wxt/tsconfig.json` (which defines the `@/*` alias) exists, then `npx shadcn@latest init` and `npx shadcn@latest add button`. Components are copied into `components/ui/` and import from `@/lib/utils`, which resolves through WXT's built-in `@` alias. Do not add `paths` to `tsconfig.json` for it. If `init` cannot detect the project, write `components.json` by hand following shadcn's manual installation guide.

Components that render through a portal (dialogs, popovers, tooltips) mount on `document.body` by default, outside the shadow root and its styles. In a content script, pass the shadow-root container to the component's portal `container` prop.

## Shared state with zustand 5

Each extension context (popup, options page, content script, background) has its own JavaScript heap, so a store is per context. Persisting to extension storage shares the data, not the live store:

```ts
// utils/settings-store.ts
import { create } from 'zustand';
import { createJSONStorage, persist, type StateStorage } from 'zustand/middleware';

const extensionStorage: StateStorage = {
  getItem: async (name) => (await storage.getItem<string>(`local:${name}`)) ?? null,
  setItem: async (name, value) => {
    await storage.setItem(`local:${name}`, value);
  },
  removeItem: async (name) => {
    await storage.removeItem(`local:${name}`);
  },
};

interface SettingsState {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useSettings = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'settings',
      storage: createJSONStorage(() => extensionStorage),
    },
  ),
);
```

zustand 5 removed the `getStorage` option; `storage: createJSONStorage(...)` is the only form. For state that must update live across contexts, prefer `storage.defineItem` with the `useStorageItem` hook above.

## Types

Extension API types live on the `Browser` namespace:

```ts
import type { Browser } from 'wxt/browser';

function describeSender(sender: Browser.runtime.MessageSender): string {
  return sender.tab?.url ?? 'extension';
}

function titles(tabs: Browser.tabs.Tab[]): string[] {
  return tabs.map((tab) => tab.title ?? '');
}
```

The polyfill-era names (`browser.Runtime.MessageSender`, `Tabs.Tab`) no longer exist.

## Links

- [WXT frontend frameworks](https://wxt.dev/guide/essentials/frontend-frameworks)
- [WXT content script UI](https://wxt.dev/guide/essentials/content-scripts#ui)
- [WXT examples: react-content-script-ui, tailwindcss](https://github.com/wxt-dev/examples/tree/main/examples)
- [Tailwind CSS with Vite](https://tailwindcss.com/docs/installation/using-vite)
- [shadcn/ui with Vite](https://ui.shadcn.com/docs/installation/vite)
