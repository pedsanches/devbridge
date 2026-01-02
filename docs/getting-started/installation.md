# Instalação para Desenvolvimento

Guia completo para configurar o ambiente de desenvolvimento local.

## Pré-requisitos

### Obrigatórios

| Ferramenta | Versão Mínima | Verificar |
|------------|---------------|-----------|
| Python | 3.11+ | `python --version` |
| Node.js | 20+ | `node --version` |
| Docker | 24+ | `docker --version` |
| Poetry | 1.7+ | `poetry --version` |

### Recomendados

- VS Code com extensões Python e Ruff
- pnpm para gerenciar frontend
- httpie ou curl para testes de API

## Backend

### 1. Clone e Entre no Diretório

```bash
git clone https://github.com/seu-usuario/devbridge.git
cd devbridge/backend
```

### 2. Instale Dependências

```bash
poetry install
```

### 3. Configure Variáveis de Ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

### 4. Inicie Serviços de Suporte

```bash
docker-compose up -d postgres redis qdrant
```

### 5. Execute Migrações

```bash
poetry run alembic upgrade head
```

### 6. Inicie a API

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

### 7. Inicie o Worker (outro terminal)

```bash
poetry run celery -A worker worker --loglevel=info
```

## Frontend

### 1. Entre no Diretório

```bash
cd devbridge/frontend
```

### 2. Instale Dependências

```bash
pnpm install
```

### 3. Configure Variáveis

```bash
cp .env.example .env.local
```

### 4. Inicie o Servidor de Desenvolvimento

```bash
pnpm dev
```

Acesse [http://localhost:3000](http://localhost:3000)

## Verificação da Instalação

Execute os testes para verificar se tudo está funcionando:

```bash
# Backend
cd backend
poetry run pytest

# Frontend
cd frontend
pnpm test
```

## Problemas Comuns

### Erro de conexão com PostgreSQL

```
psycopg2.OperationalError: could not connect to server
```

**Solução:** Verifique se o container está rodando:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### Erro de API Key

```
anthropic.AuthenticationError: Invalid API Key
```

**Solução:** Verifique se `ANTHROPIC_API_KEY` está corretamente configurada no `.env`.

### Worker não processa tarefas

**Solução:** Verifique se Redis está acessível:
```bash
redis-cli ping
# Deve retornar: PONG
```

## Próximos Passos

- [Configuração](configuration.md) - opções avançadas
- [Contribuição](../development/contributing.md) - como contribuir
