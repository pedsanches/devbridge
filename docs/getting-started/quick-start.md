# Quick Start

Levante o DevBridge em **5 minutos**.

## Pré-requisitos

- Docker e Docker Compose
- Git
- API Key da OpenAI (GPT-4o)
- Token do GitHub

## Passos

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/devbridge.git
cd devbridge
```

### 2. Configure as Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais:

```env
# AI
OPENAI_API_KEY=sk-proj-...

# GitHub
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=seu-secret-aleatorio

# Database (padrão para Docker)
DATABASE_URL=postgresql://devbridge:devbridge@localhost:5433/devbridge

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 3. Inicie a Infraestrutura

```bash
docker-compose --profile ai up -d
```

Isso levanta:
- PostgreSQL (porta 5433)
- Redis (porta 6379)
- Qdrant (porta 6333)
- Presidio (portas 5001/5002)

### 4. Inicie a API e o Worker

```bash
make dev-backend
```

Em outro terminal, rode o worker para processar webhooks:

```bash
make dev-worker
```

### 5. Verifique o Status

```bash
# Verificar se todos os containers estão rodando
docker-compose ps

# Verificar logs
docker-compose logs -f
```

### 6. Configure um Repositório

```bash
curl -X POST http://localhost:8001/api/v1/repos \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://github.com/seu-usuario/seu-repo",
    "webhook_enabled": true
  }'
```

### 7. Teste o Chat

```bash
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "O que o time fez essa semana?"}'
```

## Próximos Passos

- [Instalação detalhada](installation.md) - para desenvolvimento local
- [Configuração](configuration.md) - todas as opções disponíveis
- [Arquitetura](../architecture/overview.md) - entenda como funciona
