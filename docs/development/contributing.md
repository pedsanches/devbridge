# Guia de Contribuição

Obrigado por contribuir com o DevBridge! 🎉

## Índice

- [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
- [Workflow de Desenvolvimento](#workflow-de-desenvolvimento)
- [Padrões de Commit](#padrões-de-commit)
- [Processo de Pull Request](#processo-de-pull-request)
- [Code Review](#code-review)

---

## Ambiente de Desenvolvimento

### Pré-requisitos

- Python 3.11+
- Node.js 20+
- Docker e Docker Compose
- Poetry (Python)
- pnpm (Node.js)

### Setup

```bash
# Clone
git clone https://github.com/seu-usuario/devbridge.git
cd devbridge

# Backend
cd backend
poetry install
cp .env.example .env
poetry run pre-commit install

# Frontend
cd ../frontend
pnpm install
cp .env.example .env.local

# Infraestrutura
docker-compose --profile ai up -d postgres redis qdrant presidio-analyzer presidio-anonymizer
```

### Verificar Instalação

```bash
# Rodar testes
cd backend && poetry run pytest
cd frontend && pnpm test

# Rodar linters
cd backend && poetry run ruff check .
cd frontend && pnpm lint
```

---

## Workflow de Desenvolvimento

### 1. Escolha uma Issue

- Procure issues com label `good first issue` para começar
- Comente na issue para indicar que está trabalhando nela
- Se não houver issue, crie uma antes de começar

### 2. Crie uma Branch

```bash
# Atualizar main
git checkout main
git pull origin main

# Criar branch
git checkout -b tipo/descricao-breve

# Exemplos:
git checkout -b feat/slack-notifications
git checkout -b fix/presidio-encoding
git checkout -b docs/api-reference
```

### Tipos de Branch

| Prefixo | Uso |
|---------|-----|
| `feat/` | Nova funcionalidade |
| `fix/` | Correção de bug |
| `docs/` | Documentação |
| `refactor/` | Refactoring sem mudança de comportamento |
| `test/` | Adição de testes |
| `chore/` | Manutenção, dependências |

### 3. Desenvolva

- Escreva código seguindo os [padrões de código](code-style.md)
- Adicione testes para novas funcionalidades
- Mantenha commits pequenos e focados
- Rodar `poetry run pytest` antes de cada commit

### 4. Teste Localmente

```bash
# Backend
poetry run pytest
poetry run pytest --cov=app  # com coverage

# Frontend
pnpm test
pnpm test:e2e  # E2E tests

# Linting
poetry run ruff check .
poetry run ruff format --check .
```

---

## Padrões de Commit

Usamos [Conventional Commits](https://conventionalcommits.org).

### Formato

```
<tipo>(<escopo>): <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `feat` | Nova funcionalidade | `feat(api): adiciona endpoint de chat` |
| `fix` | Correção de bug | `fix(presidio): corrige encoding UTF-8` |
| `docs` | Documentação | `docs(readme): atualiza quick start` |
| `refactor` | Refactoring | `refactor(agents): simplifica LangGraph flow` |
| `test` | Testes | `test(api): adiciona testes para webhooks` |
| `chore` | Manutenção | `chore(deps): atualiza pydantic para 2.5` |
| `perf` | Performance | `perf(qdrant): otimiza busca vetorial` |

### Escopos Comuns

- `api`, `agents`, `parsing`, `scrubbing`, `models`
- `services`, `core`, `worker`
- `ui`, `chat`, `dashboard`
- `deps`, `ci`, `docker`

### Exemplos

```bash
# Feature
git commit -m "feat(agents): adiciona nó Auditor no LangGraph"

# Fix com referência a issue
git commit -m "fix(api): corrige rate limiting de webhooks

Closes #42"

# Breaking change
git commit -m "feat(api)!: remove endpoint legado /v1/analyze

BREAKING CHANGE: /v1/analyze foi removido, use /v2/translate"
```

---

## Processo de Pull Request

### 1. Prepare o PR

- Certifique-se que todos os testes passam
- Atualize documentação se necessário
- Rebase com main se estiver desatualizado

```bash
git fetch origin
git rebase origin/main
```

### 2. Crie o PR

- Use o template de PR (preenchido automaticamente)
- Vincule à issue relacionada
- Adicione labels apropriadas
- Solicite review de pelo menos 1 pessoa

### 3. Template de PR

```markdown
## Descrição
[Explique o que este PR faz]

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova feature
- [ ] Breaking change
- [ ] Documentação

## Checklist
- [ ] Testes foram adicionados/atualizados
- [ ] Documentação foi atualizada
- [ ] Código segue os padrões do projeto
- [ ] Self-review realizado

## Screenshots (se aplicável)
[Adicione screenshots para mudanças visuais]

## Issues Relacionadas
Closes #XXX
```

---

## Code Review

### Para Autores

- Responda a todos os comentários
- Faça force-push apenas se necessário (squash WIP commits)
- Re-request review após mudanças

### Para Revisores

- Revise em até 24h (dias úteis)
- Seja construtivo e específico
- Use sugestões do GitHub para mudanças simples
- Aprove quando satisfeito, não espere perfeição

### Checklist de Review

- [ ] Código é legível e bem organizado
- [ ] Testes cobrem casos importantes
- [ ] Sem bugs óbvios ou edge cases
- [ ] Performance é aceitável
- [ ] Segue padrões do projeto
- [ ] Documentação está atualizada

---

## Recursos Adicionais

- [Padrões de Código](code-style.md)
- [Estratégia de Testes](testing.md)
- [Arquitetura](../architecture/overview.md)
- [Regras de Negócio](../business/rules-catalog.md)
