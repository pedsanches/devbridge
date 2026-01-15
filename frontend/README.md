# DevBridge Frontend

Frontend application for DevBridge platform, built with **Next.js 15** and **React 19**.

## 🛠️ Stack

- **Framework**: [Next.js 15](https://nextjs.org/) (App Router)
- **Language**: TypeScript
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **UI Architecture**: Component-based with utility-first CSS
- **State Management**: React Server Components (Server State) + Hooks (Client State)
- **AI Integration**: Vercel AI SDK
- **Icons**: Lucide React
- **Testing**: Vitest + React Testing Library

## 📂 Project Structure

```bash
src/
├── app/              # Next.js App Router pages and layouts
├── components/       # Reusable UI components
│   ├── ui/          # Low-level primitives (buttons, inputs)
│   └── ...          # Feature-specific components
├── hooks/            # Custom React hooks
├── lib/              # Utilities and helper functions
└── services/         # API clients and external services
```

## 🚀 Getting Started

```bash
# Install dependencies
pnpm install

# Run development server
pnpm dev -p 3001
```

Open [http://localhost:3001](http://localhost:3001) to view it in the browser.

## 🎨 Design System

We strictly follow the design tokens defined in the root documentation.

- **Colors**: Use `bg-primary`, `text-neutral-900`, etc. defined in `tailwind.config.ts`.
- **Typography**: `font-sans` for interface, `font-mono` for code.
- **Dark Mode**: Supported via `next-themes` and `darkMode: "class"`.

### Extending Styles
Do not hardcode hex values. Always use Tailwind utility classes that map to our CSS variables defined in global styles.

## 🧪 Testing

We use **Vitest** for unit and component testing.

```bash
# Run tests
pnpm test

# Run tests with UI
pnpm test:ui

# Run E2E tests
pnpm test:e2e
```

## 🤝 Contribution

1. Ensure all new components are typed strict.
2. Run `pnpm lint` before committing.
3. Follow the "Client Components only when necessary" rule to maximize performance.
