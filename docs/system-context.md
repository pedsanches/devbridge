# Contexto do Sistema

Este arquivo fornece um mapa mental de alta densidade do projeto DevBridge para Agentes de IA e desenvolvedores humanos.

## 🗺️ Mapa do Território

| Diretório | Conteúdo | Principais Arquivos |
|-----------|----------|---------------------|
| `/` | Raiz do projeto | `README.md`, `pyproject.toml`, `docker-compose.yml` |
| `packages/` | **Monorepo** - Código compartilhado | `shared-types/` (Types TS) |
| `mcp-toolbox/` | **MCP Toolbox** - Acesso DB para IA | `AGENTS.md`, `tools-secure.yaml` |
| `docs/architecture` | Arquitetura do sistema | `overview.md`, `project-structure.md`, `data-flow.md`, `decisions/` |
| `docs/business` | Domínio do negócio | `rules-catalog.md` |
| `docs/development` | Guias de código | `code-style.md` (Linting, Types), `testing.md`, `contributing.md` |
| `docs/design` | **Design System** | `foundations.md` (Tokens), `components.md`, `brand.md` |
| `docs/operations` | Infra e Runbooks | `deployment.md`, `runbook.md`, `mcp-integration.md` |
| `docs/api` | **OpenAPI Spec** | `openapi.yaml` |

## 🏗️ Tech Stack & Ferramentas

| Categoria | Tecnologias | Detalhes |
|-----------|-------------|----------|
| **Core** | Python 3.11+ | Type hints estritos (`mypy`), `ruff` para linting |
| **Framework** | FastAPI | Async por padrão, Pydantic v2 para validação |
| **Worker** | Celery + Redis | Processamento assíncrono de eventos |
| **IA** | LangGraph, Claude 3.5 | Orquestração cíclica, Tool-calling |
| **Banco** | PostgreSQL, Qdrant | Relacional + Vetorial (Hybrid Search) |
| **Privacidade** | Microsoft Presidio | Sanitização de dados antes do prompt |
| **Frontend** | Next.js 15, Vercel AI SDK | Dashboard e Chat UI |

## 🤖 MCP Toolbox (Acesso DB para IA)

O projeto inclui **MCP Toolbox** para permitir que agentes de IA acessem o banco de dados de forma segura.

| Aspecto | Detalhes |
|---------|----------|
| **Propósito** | Acesso read-only ao PostgreSQL para agentes |
| **Usuário** | `mcp_readonly` (SELECT apenas) |
| **Porta** | `localhost:5000` |
| **Documentação** | [`mcp-toolbox/AGENTS.md`](../mcp-toolbox/AGENTS.md) |

**Tools disponíveis:**
- `query_repositories` - Listar repositórios
- `query_commits` - Buscar commits
- `query_translations` - Consultar traduções

> [!TIP]
> Para configuração detalhada, veja [`docs/operations/mcp-integration.md`](operations/mcp-integration.md)

## 🧠 Padrões Arquiteturais (Resumo)

Baseado em `docs/architecture/overview.md`:
1.  **Event-Driven RAG**: Webhooks -> Fila -> Worker -> Agente.
2.  **Privacy-First**: Dados sensíveis são removidos antes de tocar a LLM.
3.  **Structured Output**: Agentes de IA retornam JSON validado, nunca texto livre.
4.  **Zero Alucinação**: Dados financeiros somente via configuração explícita.

## ✨ Features Principais (2026-01)

| Feature | Serviços | ADR |
|---------|----------|-----|
| **Chat com RAG** | `chat_service.py`, `vector_service.py` | - |
| **Reports por Persona** | `report_service.py`, `pdf_export_service.py` | [ADR-008](architecture/decisions/008-reports-system.md) |
| **Business Updates** | `ai_service.py`, `sync_service.py` | - |
| **Value Tagging** | `ai_service.py` | - |
| **Multi-tenant** | Todas as queries filtram por `org_id` | [ADR-006](architecture/decisions/006-saas-data-model.md) |
| **Magic Link Auth** | `auth_service.py`, `email_service.py` | [ADR-007](architecture/decisions/007-auth-strategy.md) |
| **Developer Metrics** | `metrics_service.py`, `issue_service.py` | [ADR-009](architecture/decisions/009-developer-effort-tracking.md) |

### Estrutura de Services (Backend)

```
app/services/
├── ai_service.py          # Integração Claude, Business Updates, Value Tags
├── chat_service.py        # Chat com RAG, contexto de conversas
├── report_service.py      # Geração de reports estruturados
├── metrics_service.py     # [NEW] DORA, SPACE e Developer Profiles
├── issue_service.py       # [NEW] Gestão de Issues
├── code_review_service.py # [NEW] Code Review Metrics
├── pdf_export_service.py  # Export para PDF (WeasyPrint)
├── sync_service.py        # Sincronização com GitHub (agora inclui Issues/Stats)
├── vector_service.py      # Qdrant embeddings
├── auth_service.py        # Magic links, JWT
└── conversation_service.py # Persistência de conversas
```

## 🛡️ Convenções Críticas

- **Commits**: Seguir Conventional Commits.
- **Testes**: `pytest` é mandatório para nova lógica.
- **Estilo**: `ruff check .` e `mypy .` devem passar sem erros.
- **Novas Bibliotecas**: Requerem aprovação e `poetry add`.

> [!NOTE]
> Para detalhes profundos de decisão, consulte `docs/architecture/decisions/`.
