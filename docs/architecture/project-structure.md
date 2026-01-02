# Estrutura do Projeto

Estrutura de diretórios recomendada para o DevBridge, baseada em boas práticas de FastAPI e Next.js 15.

---

## 📁 Visão Geral

```
devbridge/
├── backend/                 # API Python/FastAPI
├── frontend/                # Dashboard Next.js
├── packages/                # 📦 Monorepo: Código compartilhado
│   └── shared-types/        # Types TypeScript compartilhados
├── mcp-toolbox/             # 🤖 MCP Toolbox para acesso DB via IA
├── docs/                    # Documentação (você está aqui)
├── scripts/                 # Scripts de automação
├── docker-compose.yml       # Orquestração de containers
├── pnpm-workspace.yaml      # Configuração de workspaces
├── .devbridge.yaml          # Configuração do sistema
├── Makefile                 # Comandos de desenvolvimento
└── README.md
```

---

## 📦 Monorepo (pnpm Workspaces)

O projeto utiliza **pnpm workspaces** para gerenciar código compartilhado entre frontend e backend.

```yaml
# pnpm-workspace.yaml
packages:
  - "packages/*"
  - "apps/*"
```

### Packages Disponíveis

| Package | Descrição |
|---------|-----------|
| `@devbridge/shared-types` | Types TypeScript compartilhados |

### Uso no Frontend

```typescript
// frontend/package.json
{
  "dependencies": {
    "@devbridge/shared-types": "workspace:*"
  }
}

// Importando types
import type { Repository, BusinessTranslation } from "@devbridge/shared-types";
```

### Estrutura do shared-types

```
packages/shared-types/
├── package.json
├── tsconfig.json
└── src/
    ├── index.ts       # Types principais (Repository, Translation, etc.)
    └── api.ts         # Types de API (webhooks, requests, responses)
```

---

## 🐍 Backend (FastAPI)

Estrutura modular seguindo padrões de Clean Architecture e Service Layer.

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point, FastAPI app
│   │
│   ├── api/                 # Routers e endpoints
│   │   ├── __init__.py
│   │   ├── deps.py          # Dependências compartilhadas
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py    # Router principal v1
│   │       ├── webhooks.py  # GitHub webhooks
│   │       ├── repos.py     # CRUD de repositórios
│   │       ├── chat.py      # Chat/RAG endpoints
│   │       └── health.py    # Health checks
│   │
│   ├── core/                # Configurações globais
│   │   ├── __init__.py
│   │   ├── config.py        # Settings (Pydantic BaseSettings)
│   │   ├── security.py      # Auth, JWT, hashing
│   │   └── constants.py     # Constantes do sistema
│   │
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py          # Base class
│   │   ├── repository.py
│   │   ├── commit.py
│   │   ├── translation.py
│   │   └── user.py
│   │
│   ├── schemas/             # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── repository.py
│   │   ├── commit.py
│   │   ├── translation.py
│   │   └── common.py        # Schemas compartilhados
│   │
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── webhook_service.py
│   │   ├── translation_service.py
│   │   ├── github_service.py
│   │   └── slack_service.py
│   │
│   ├── agents/              # LangGraph agents
│   │   ├── __init__.py
│   │   ├── orchestrator.py  # Orquestrador principal
│   │   ├── technical.py     # Agente técnico
│   │   ├── business.py      # Agente de negócio
│   │   └── auditor.py       # Agente auditor
│   │
│   ├── db/                  # Database
│   │   ├── __init__.py
│   │   ├── session.py       # SQLAlchemy session
│   │   ├── migrations/      # Alembic migrations
│   │   └── init_db.py       # Seed data
│   │
│   ├── utils/               # Helpers
│   │   ├── __init__.py
│   │   ├── sanitizer.py     # Presidio wrapper
│   │   ├── parser.py        # Tree-sitter wrapper
│   │   └── embeddings.py    # Embedding utils
│   │
│   └── exceptions/          # Custom exceptions
│       ├── __init__.py
│       └── handlers.py
│
├── tests/                   # Testes
│   ├── __init__.py
│   ├── conftest.py          # Fixtures pytest
│   ├── unit/
│   │   └── test_services.py
│   └── integration/
│       └── test_api.py
│
├── pyproject.toml           # Poetry config
├── Dockerfile
└── .env.example
```

### Convenções Backend

| Convenção | Regra |
|-----------|-------|
| **Imports** | Ordem: stdlib → third-party → local |
| **Type Hints** | Obrigatório em todas as funções |
| **Docstrings** | Google style para funções públicas |
| **Naming** | `snake_case` para funções e variáveis |
| **Schemas** | Sufixo `Create`, `Update`, `Response` (ex: `RepoCreate`) |

---

## ⚛️ Frontend (Next.js 15)

Estrutura usando App Router com separação clara de responsabilidades.

```
frontend/
├── src/
│   ├── app/                 # App Router (pages)
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Home page
│   │   ├── globals.css      # Global styles + CSS variables
│   │   │
│   │   ├── (auth)/          # Route group - auth pages
│   │   │   ├── login/
│   │   │   └── register/
│   │   │
│   │   ├── (dashboard)/     # Route group - dashboard
│   │   │   ├── layout.tsx   # Dashboard layout (sidebar)
│   │   │   ├── page.tsx     # Dashboard home
│   │   │   ├── repos/       # Repositórios
│   │   │   ├── chat/        # Chat interface
│   │   │   └── settings/    # Configurações
│   │   │
│   │   └── api/             # API Routes (se necessário)
│   │       └── auth/
│   │
│   ├── components/          # React components
│   │   ├── ui/              # Primitivos (Button, Input, Card)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   └── index.ts     # Barrel export
│   │   │
│   │   ├── layout/          # Layout components
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── footer.tsx
│   │   │
│   │   └── features/        # Feature-specific components
│   │       ├── chat/
│   │       │   ├── chat-input.tsx
│   │       │   └── chat-message.tsx
│   │       └── repos/
│   │           └── repo-card.tsx
│   │
│   ├── lib/                 # Utilities e configs
│   │   ├── utils.ts         # Helper functions (cn, formatters)
│   │   ├── api.ts           # API client (fetch wrapper)
│   │   └── constants.ts
│   │
│   ├── hooks/               # Custom React hooks
│   │   ├── use-chat.ts
│   │   └── use-repos.ts
│   │
│   ├── types/               # TypeScript types
│   │   ├── index.ts
│   │   ├── api.ts           # API response types
│   │   └── chat.ts
│   │
│   └── styles/              # Additional styles (se necessário)
│       └── animations.css
│
├── public/                  # Static assets
│   ├── brand/
│   │   └── logo.svg
│   └── icons/
│
├── next.config.ts
├── tailwind.config.ts       # (se usar Tailwind)
├── tsconfig.json
├── package.json
└── Dockerfile
```

### Convenções Frontend

| Convenção | Regra |
|-----------|-------|
| **Components** | PascalCase (`ChatMessage.tsx`) |
| **Hooks** | Prefixo `use-` (`use-chat.ts`) |
| **Types** | Interfaces para objetos, Types para unions |
| **Imports** | Aliases `@/components`, `@/lib`, `@/hooks` |
| **Styles** | CSS Variables do Design System |

---

## 🐳 Docker & DevOps

```
devbridge/
├── docker-compose.yml       # Desenvolvimento local
├── docker-compose.prod.yml  # Produção
│
├── .github/
│   └── workflows/
│       ├── ci.yml           # Lint, test, build
│       └── deploy.yml       # Deploy automático
│
├── scripts/
│   ├── setup.sh             # Setup inicial
│   ├── seed.sh              # Seed database
│   └── backup.sh            # Backup script
│
└── Makefile                 # Comandos úteis
    # make dev    → start development
    # make test   → run all tests
    # make lint   → check code quality
    # make build  → build for production
```

---

## 📝 Convenções de Nomenclatura

| Tipo | Python | TypeScript |
|------|--------|------------|
| Arquivos | `snake_case.py` | `kebab-case.ts` ou `PascalCase.tsx` |
| Variáveis | `snake_case` | `camelCase` |
| Funções | `snake_case` | `camelCase` |
| Classes | `PascalCase` | `PascalCase` |
| Constantes | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |

---

## ✅ Checklist para Novos Arquivos

Antes de criar um novo arquivo, verifique:

- [ ] Está no diretório correto conforme esta estrutura?
- [ ] Segue a convenção de nomenclatura?
- [ ] Tem testes correspondentes (se aplicável)?
- [ ] Está exportado no `__init__.py`/`index.ts`?
- [ ] Atualizar `docs/system-context.md` se for um novo módulo?

> [!TIP]
> Para agentes de IA: use esta estrutura como referência ao criar novos arquivos. Consulte `docs/development/code-style.md` para padrões de código.
