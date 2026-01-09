# DevBridge Backend

API Backend do DevBridge, construída com **FastAPI** e **Python 3.11+**.

## 🛠️ Stack

| Tecnologia | Propósito |
|------------|-----------|
| **FastAPI** | Framework web async |
| **SQLAlchemy 2.0** | ORM com async support |
| **PostgreSQL** | Banco de dados relacional |
| **Qdrant** | Banco vetorial para RAG |
| **Alembic** | Migrations de banco |
| **Pydantic v2** | Validação de schemas |
| **LangGraph** | Orquestração de agentes IA |
| **Anthropic Claude** | LLM para processamento |

## 📂 Estrutura de Diretórios

```
backend/
├── app/
│   ├── main.py              # Entry point FastAPI
│   ├── api/                 # Routers e endpoints
│   │   └── v1/
│   │       ├── router.py    # Router principal
│   │       ├── auth.py      # Autenticação
│   │       ├── repos.py     # Repositórios
│   │       ├── activities.py    # Atividades
│   │       ├── chat.py      # Chat/RAG
│   │       ├── reports.py   # Geração de reports
│   │       └── report_templates.py  # Templates
│   ├── core/                # Configurações
│   │   ├── config.py        # Settings (env vars)
│   │   └── security.py      # JWT, auth utils
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   │   ├── ai_service.py        # Integração IA
│   │   ├── chat_service.py      # Chat com RAG
│   │   ├── report_service.py    # Geração reports
│   │   ├── sync_service.py      # Sync GitHub
│   │   └── ...
│   ├── db/                  # Database
│   │   ├── session.py       # Async session
│   │   └── migrations/      # Alembic migrations
│   └── agents/              # LangGraph agents
├── tests/                   # Testes pytest
├── scripts/                 # Scripts utilitários
├── pyproject.toml           # Poetry config
└── Dockerfile
```

## 🚀 Desenvolvimento

### Pré-requisitos

- Python 3.11+
- Poetry
- Docker (para PostgreSQL, Qdrant, Redis)

### Setup

```bash
# Instalar dependências
cd backend
poetry install

# Ativar ambiente virtual
poetry shell

# Copiar variáveis de ambiente
cp ../.env.example ../.env
```

### Executar

```bash
# Iniciar infraestrutura (da raiz do projeto)
docker-compose up -d postgres qdrant redis

# Rodar migrations
alembic upgrade head

# Iniciar servidor de desenvolvimento
uvicorn app.main:app --reload --port 8000
```

### Variáveis de Ambiente Essenciais

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | PostgreSQL connection string |
| `QDRANT_URL` | URL do Qdrant (default: `http://localhost:6333`) |
| `JWT_SECRET_KEY` | Chave secreta para JWT |
| `ANTHROPIC_API_KEY` | API key do Claude |
| `OPENAI_API_KEY` | API key para embeddings |
| `RESEND_API_KEY` | API key para envio de emails |
| `GITHUB_TOKEN` | Token para acesso ao GitHub |

## 🧪 Testes

```bash
# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Apenas testes de integração
pytest tests/integration/

# Apenas testes unitários
pytest tests/unit/
```

## 📡 API Endpoints Principais

| Caminho | Método | Descrição |
|---------|--------|-----------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/auth/magic` | POST | Solicitar magic link |
| `/api/v1/auth/verify` | GET | Verificar token |
| `/api/v1/repos/` | GET/POST | CRUD repositórios |
| `/api/v1/activities/` | GET | Listar atividades |
| `/api/v1/chat/` | POST | Enviar mensagem |
| `/api/v1/conversations/` | GET | Histórico de conversas |
| `/api/v1/reports/` | GET/POST | Geração de reports |
| `/api/v1/report-templates/` | GET/POST | Templates |
| `/api/v1/sync/` | POST | Sincronizar repositório |

## 📋 Convenções

- **Type Hints**: Obrigatório em todas as funções
- **Docstrings**: Google style
- **Linting**: `ruff check .` deve passar
- **Types**: `mypy .` deve passar
- **Commits**: Conventional Commits

## 📚 Documentação Adicional

- [Arquitetura do Sistema](../docs/architecture/overview.md)
- [Guia de Contribuição](../docs/development/contributing.md)
- [Padrões de Código](../docs/development/code-style.md)
- [Estratégia de Testes](../docs/development/testing.md)
- [ADRs](../docs/architecture/decisions/)
