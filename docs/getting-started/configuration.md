# Configuração

Todas as opções de configuração disponíveis via variáveis de ambiente.

## Variáveis Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `ANTHROPIC_API_KEY` | API Key do Claude | `sk-ant-api03-...` |
| `GITHUB_TOKEN` | Personal Access Token do GitHub | `ghp_...` |
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | URL de conexão Redis | `redis://localhost:6379/0` |

> Em produção, o backend valida `SECRET_KEY`, `JWT_SECRET_KEY`, `OPENAI_API_KEY` e `GITHUB_WEBHOOK_SECRET` na inicialização.
> O frontend valida `NEXT_PUBLIC_API_URL` durante o build.

## Variáveis Opcionais

### AI & LLM

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LLM_MODEL` | `claude-3-5-sonnet-20241022` | Modelo Claude a usar |
| `LLM_MAX_TOKENS` | `4096` | Máximo de tokens na resposta |
| `LLM_TEMPERATURE` | `0.3` | Temperatura para geração (0-1) |
| `EMBEDDING_MODEL` | `jina-embeddings-v3` | Modelo de embeddings |

### GitHub

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `GITHUB_WEBHOOK_SECRET` | - | Secret para validar webhooks |
| `GITHUB_API_BASE_URL` | `https://api.github.com` | URL base (para GitHub Enterprise) |

### Banco de Dados

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `DB_POOL_SIZE` | `10` | Tamanho do pool de conexões |
| `DB_ECHO` | `false` | Logar queries SQL |

### Qdrant (Vector DB)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `QDRANT_URL` | `http://localhost:6333` | URL do Qdrant |
| `QDRANT_API_KEY` | - | API Key (se cloud) |
| `QDRANT_COLLECTION` | `devbridge` | Nome da collection |

### Celery

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `CELERY_BROKER_URL` | `$REDIS_URL` | URL do broker |
| `CELERY_RESULT_BACKEND` | `$REDIS_URL` | URL para resultados |
| `CELERY_CONCURRENCY` | `4` | Número de workers |

### Segurança

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | - | Chave para JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Expiração do access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Expiração do refresh token |
| `CORS_ORIGINS` | `["http://localhost:3001"]` | Origens permitidas (JSON array) |
| `RATE_LIMIT_PER_MINUTE` | `100` | Limite global por IP (req/min) |
| `WEBHOOK_RATE_LIMIT_PER_HOUR` | `100` | Limite de webhooks por repo/hora |

### Privacidade (Presidio)

Obrigatório para sanitização de PII antes de chamadas à IA.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PRESIDIO_ANALYZER_URL` | `http://localhost:5001` | Endpoint do Analyzer |
| `PRESIDIO_ANONYMIZER_URL` | `http://localhost:5002` | Endpoint do Anonymizer |
| `PRESIDIO_LANGUAGES` | `["pt", "en"]` | Idiomas de detecção |

### Observabilidade

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LOG_LEVEL` | `INFO` | Nível de log |
| `PHOENIX_ENABLED` | `true` | Habilitar Arize Phoenix |
| `PHOENIX_ENDPOINT` | `http://localhost:6006` | Endpoint do Phoenix |

### Frontend

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8001/api/v1` | URL base da API (obrigatória em produção) |

## Arquivo `.devbridge.yaml`

Configuração específica do repositório monitorado:

```yaml
# .devbridge.yaml (na raiz do repo monitorado)
project_name: "E-commerce Checkout"

business_metrics:
  average_cart_value: 150.00
  daily_transactions: 5000
  downtime_cost_per_hour: 15000.00

strategic_pillars:
  - id: "conv_rate"
    description: "Aumentar taxa de conversão do checkout"
    priority: "high"
  - id: "tech_debt"
    description: "Reduzir dívida técnica do módulo de pagamentos"
    priority: "medium"

audience_profiles:
  - role: "cto"
    detail_level: "technical"
  - role: "pm"
    detail_level: "outcome-focused"
  - role: "ceo"
    detail_level: "executive-summary"

ignore_patterns:
  - "*.lock"
  - "node_modules/**"
  - "dist/**"
  - ".git/**"
```

## Exemplo Completo de `.env`

```env
# ===================
# AI Configuration
# ===================
ANTHROPIC_API_KEY=sk-ant-api03-...
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.3

# ===================
# GitHub
# ===================
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=meu-secret-super-seguro

# ===================
# Database
# ===================
DATABASE_URL=postgresql://devbridge:devbridge@localhost:5432/devbridge
DB_POOL_SIZE=10

# ===================
# Redis
# ===================
REDIS_URL=redis://localhost:6379/0

# ===================
# Qdrant
# ===================
QDRANT_URL=http://localhost:6333

# ===================
# Security
# ===================
SECRET_KEY=minha-chave-secreta-muito-longa-e-aleatoria
CORS_ORIGINS=["http://localhost:3001"]

# ===================
# Observability
# ===================
LOG_LEVEL=INFO
PHOENIX_ENABLED=true
```

## Próximos Passos

- [Arquitetura](../architecture/overview.md) - entenda como funciona
- [Contribuição](../development/contributing.md) - comece a contribuir
