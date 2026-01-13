# Frontend Best Practices Guide

> **For AI Agents & Developers** — Last updated: January 2026

## 🎯 Quick Reference

| Stack | Version | Key Docs |
|-------|---------|----------|
| Next.js | 16.x | [Next.js Docs](https://nextjs.org/docs) |
| React | 19.x | Uses React 19 patterns |
| TypeScript | 5.x | **Strict mode enabled** |
| TailwindCSS | 3.4 | CSS-first approach |
| Vitest | 3.x | Unit testing |
| Playwright | - | E2E testing |

---

## 🛡️ TypeScript Strict Mode

The project uses strict TypeScript with enhanced options:

```json
{
  "noUncheckedIndexedAccess": true,
  "exactOptionalPropertyTypes": true
}
```

### Required Patterns

#### 1. Array Index Access
```typescript
// ❌ WRONG - Will error
const item = array[0];
item.property; // Error: Object is possibly 'undefined'

// ✅ CORRECT - Use nullish coalescing or type guard
const item = array[0] ?? defaultValue;
// or
const item = array[0];
if (item) { /* use item */ }
```

#### 2. Optional Props with Undefined
```typescript
// ❌ WRONG - Will error with exactOptionalPropertyTypes
interface Props {
  onClick?: () => void;
}
// When passing: <Component onClick={maybeUndefined} /> // Error!

// ✅ CORRECT - Explicitly allow undefined
interface Props {
  onClick?: (() => void) | undefined;
}
```

#### 3. Spread with Array Elements
```typescript
// ❌ WRONG
const updated = [...array];
updated[index] = { ...updated[index], enabled: true }; // Error

// ✅ CORRECT
const updated = [...array];
const item = updated[index];
if (item) {
  updated[index] = { ...item, enabled: true };
}
```

---

## 🎨 Styling Rules

### Design Tokens Only
```tsx
// ❌ NEVER hardcode colors
<div className="bg-blue-500 text-gray-900">

// ✅ ALWAYS use CSS variables
<div className="bg-[var(--primary)] text-[var(--foreground)]">
// or with Tailwind semantic classes
<div className="bg-primary text-foreground">
```

### CSS Variable Categories
| Variable | Purpose |
|----------|---------|
| `--primary`, `--secondary` | Brand colors |
| `--foreground`, `--background` | Text & backgrounds |
| `--muted`, `--muted-foreground` | Subdued elements |
| `--border`, `--ring` | Borders & focus |
| `--card`, `--popover` | Container backgrounds |

---

## ⚛️ React 19 Patterns

### Prefer `useSyncExternalStore` for External State
```tsx
// For localStorage, window events, pathname changes
import { useSyncExternalStore } from 'react';

const isHydrated = useSyncExternalStore(
  () => () => {}, // subscribe (noop for static)
  () => true,      // getSnapshot (client)
  () => false      // getServerSnapshot
);
```

### Avoid setState in useEffect
```tsx
// ❌ AVOID - Triggers lint error
useEffect(() => {
  setMounted(true); // react-hooks/set-state-in-effect
}, []);

// ✅ PREFER - Lazy initialization or refs
const [state] = useState(() => computeInitialValue());
const hasRun = useRef(false);
```

### useCallback Dependencies
Always include all dependencies to avoid stale closures:
```tsx
const handleAction = useCallback(() => {
  doSomething(dep1, dep2);
}, [dep1, dep2]); // ✅ Include all deps
```

---

## 📁 Component Structure

```
src/
├── app/                    # Next.js App Router pages
├── components/
│   ├── ui/                # shadcn/ui primitives (Button, Card, etc.)
│   ├── layout/            # Layout components (Sidebar, Header)
│   ├── chat/              # Chat feature components
│   ├── dashboard/         # Dashboard components
│   └── [feature]/         # Feature-specific components
├── hooks/                  # Custom React hooks
├── services/              # API clients
├── lib/                   # Utilities
└── stories/               # Storybook stories
```

---

## 🧪 Testing Requirements

### Before Committing
```bash
npm run typecheck   # TypeScript verification
npm run lint        # ESLint checks
npm run test        # Vitest unit tests (if applicable)
```

### E2E Testing
```bash
npx playwright test # Playwright E2E
```

---

## 🔧 ESLint Configuration

Using Next.js 16 flat config (`eslint.config.mjs`):

### Key Rules
| Rule | Level | Reason |
|------|-------|--------|
| `react-hooks/set-state-in-effect` | error | Prevents hydration issues |
| `react-hooks/exhaustive-deps` | error | Prevents stale closures |
| `@typescript-eslint/no-explicit-any` | warn | Type safety |

---

## 📦 Import Order

```typescript
// 1. External packages
import { useState } from 'react';
import { useRouter } from 'next/navigation';

// 2. Internal aliases (@/)
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/use-auth';

// 3. Relative imports
import { LocalComponent } from './LocalComponent';

// 4. Types (type-only imports)
import type { SomeType } from '@/types';
```

---

## 🚀 Performance Guidelines

### Image Optimization
```tsx
// ✅ Always use next/image
import Image from 'next/image';

<Image
  src="/image.png"
  alt="Description"
  width={400}
  height={300}
/>
```

### Dynamic Imports for Heavy Components
```tsx
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <Skeleton />,
  ssr: false
});
```

### Memoization
```tsx
// For expensive computations
const computed = useMemo(() => expensiveCalc(data), [data]);

// For stable callbacks passed to children
const handler = useCallback(() => {/*...*/}, [deps]);

// For component memoization
const MemoComponent = memo(function Component(props) {/*...*/});
```

---

## ⚠️ Common Mistakes to Avoid

| Mistake | Solution |
|---------|----------|
| Hardcoding colors | Use `var(--*)` or Tailwind semantic classes |
| Using `any` type | Use proper types or `unknown` with guards |
| Missing array bounds check | Use `??`, `?.`, or explicit `if` checks |
| setState in useEffect | Use lazy init, refs, or useSyncExternalStore |
| Skipping typecheck | Always run `npm run typecheck` before commit |

---

## 📚 Related Documentation

- [Design Tokens](docs/design/foundations.md)
- [Component Guidelines](docs/development/code-style.md)
- [ADRs](docs/architecture/decisions/)
