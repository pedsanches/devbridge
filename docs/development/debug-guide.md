# Guia de Debug - DevBridge

Como encontrar e resolver erros rapidamente no desenvolvimento.

> **Para agentes de IA**: Este guia contém fluxos de diagnóstico estruturados. Siga os passos na ordem indicada.

---

## 🚀 Diagnóstico Rápido (Sempre Execute Primeiro)

```bash
# Diagnóstico completo - SEMPRE COMECE AQUI
make diagnose
```

Se algum serviço falhar, siga a seção correspondente abaixo.

---

## 📋 Fluxos de Debug por Tipo de Erro

### Erro HTTP 4xx/5xx na API

**Sintoma**: Request retorna erro com status 4xx ou 5xx

**Resposta de erro padrão**:
```json
{
  "error_id": "uuid-único-do-erro",
  "trace_id": "trace-id-para-logs",
  "error_code": "AUTH_001",
  "message": "Mensagem amigável",
  "path": "/api/v1/endpoint"
}
```

**Fluxo de diagnóstico**:
1. Extraia o `trace_id` da resposta
2. Busque nos logs:
   ```bash
   docker logs devbridge-backend-1 2>&1 | grep "trace_id=SEU_TRACE_ID"
   ```
3. Identifique o `error_code` e consulte a tabela abaixo
4. Se não encontrar, verifique logs completos:
   ```bash
   make diagnose-logs
   ```

---

### Erro no Frontend (Next.js)

**Sintoma**: Página não carrega, erro no console do browser

**Fluxo de diagnóstico**:
1. Abra DevTools (F12) → Console → Copie o erro
2. Vá em Network → Encontre a request que falhou
3. Copie o header `X-Trace-ID` da resposta
4. Busque no backend:
   ```bash
   docker logs devbridge-backend-1 2>&1 | grep "trace_id=SEU_TRACE_ID"
   ```

**Erros comuns**:
| Erro | Causa | Solução |
|------|-------|---------|
| `ECONNREFUSED 8001` | Backend não está rodando | `make dev-backend` |
| `401 Unauthorized` | Token expirado/inválido | Fazer novo login |
| `CORS policy` | Origem não autorizada | Verificar `CORS_ORIGINS` em `.env` |

---

### Erro no Worker (Celery)

**Sintoma**: Tasks não executam, fila crescendo

**Fluxo de diagnóstico**:
1. Verificar se worker está rodando:
   ```bash
   docker ps | grep worker
   ```
2. Ver tamanho da fila:
   ```bash
   docker exec devbridge-redis redis-cli LLEN celery
   ```
3. Ver logs do worker:
   ```bash
   make logs-worker
   ```
4. Se fila muito grande, verificar tasks travadas:
   ```bash
   docker exec devbridge-redis redis-cli LRANGE celery 0 10
   ```

**Erros comuns**:
| Erro | Causa | Solução |
|------|-------|---------|
| `ConnectionRefused Redis` | Redis não está rodando | `docker compose up -d redis` |
| `Task timeout` | Task demorada demais | Aumentar `CELERY_TASK_TIMEOUT` |
| `Exception in task` | Erro no código da task | Ver stacktrace nos logs |

---

### Erro no Banco (PostgreSQL)

**Sintoma**: Queries lentas, conexões esgotadas, erros de database

**Fluxo de diagnóstico**:
1. Verificar se Postgres está rodando:
   ```bash
   make diagnose-db
   ```
2. Ver conexões ativas:
   ```bash
   docker exec devbridge-postgres psql -U devbridge -c \
     "SELECT count(*) FROM pg_stat_activity"
   ```
3. Identificar queries lentas:
   ```bash
   docker exec devbridge-postgres psql -U devbridge -c \
     "SELECT pid, query, state, query_start FROM pg_stat_activity WHERE state = 'active'"
   ```
4. Se muitas conexões, terminar queries antigas:
   ```bash
   docker exec devbridge-postgres psql -U devbridge -c \
     "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query_start < now() - interval '5 minutes'"
   ```

**Erros comuns**:
| Erro | Causa | Solução |
|------|-------|---------|
| `too many connections` | Pool esgotado | Reiniciar backend ou aumentar pool |
| `relation does not exist` | Migration pendente | `cd backend && uv run alembic upgrade head` |
| `FATAL: password authentication failed` | Credenciais erradas | Verificar `DATABASE_URL` em `.env` |

---

### Erro de Autenticação

**Sintoma**: 401 Unauthorized, token inválido

**Fluxo de diagnóstico**:
1. Verificar se cookie `session` existe no browser
2. Testar endpoint de health autenticado:
   ```bash
   curl -v http://localhost:8001/api/v1/auth/me -H "Cookie: session=SEU_TOKEN"
   ```
3. Se token expirado, fazer novo login:
   ```bash
   # Dev login (apenas ambiente de desenvolvimento)
   curl -X POST http://localhost:8001/api/v1/auth/dev-login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com"}' \
     -c cookies.txt
   ```

---

### Erro de Serviços Externos (GitHub, OpenAI)

**Sintoma**: Erros com código `EXT_001`, `EXT_002`

**Fluxo de diagnóstico**:
1. Verificar se APIs estão configuradas:
   ```bash
   make diagnose-env
   ```
2. Testar conexão GitHub:
   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```
3. Testar conexão OpenAI:
   ```bash
   curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

**Erros comuns**:
| Erro | Causa | Solução |
|------|-------|---------|
| `EXT_001` | GitHub API falhou | Verificar `GITHUB_TOKEN` e rate limits |
| `EXT_002` | OpenAI API falhou | Verificar `OPENAI_API_KEY` e quota |
| `Rate limit exceeded` | Muitas requests | Aguardar reset do rate limit |

---

## 📊 Códigos de Erro

### Autenticação (AUTH_xxx)
| Código | Significado | Ação |
|--------|-------------|------|
| `AUTH_001` | Token inválido | Fazer novo login |
| `AUTH_002` | Token expirado | Fazer novo login |
| `AUTH_003` | Não autenticado | Incluir token na request |
| `AUTH_004` | Sem permissão | Verificar role do usuário |

### Validação (VAL_xxx)
| Código | Significado | Ação |
|--------|-------------|------|
| `VAL_001` | Validação falhou | Verificar campos obrigatórios |
| `VAL_002` | Campo faltando | Adicionar campo obrigatório |
| `VAL_003` | Formato inválido | Verificar formato esperado |

### Recursos (RES_xxx)
| Código | Significado | Ação |
|--------|-------------|------|
| `RES_001` | Recurso não encontrado | Verificar ID do recurso |
| `RES_002` | Recurso já existe | Usar recurso existente |
| `RES_003` | Conflito de recurso | Resolver conflito antes de continuar |

### Serviços Externos (EXT_xxx)
| Código | Significado | Ação |
|--------|-------------|------|
| `EXT_001` | Erro GitHub API | Verificar token e rate limits |
| `EXT_002` | Erro OpenAI/LLM | Verificar chave e quota |
| `EXT_003` | Erro Database | Verificar conexão PostgreSQL |
| `EXT_004` | Erro Redis | Verificar conexão Redis |

### Rate Limiting (RATE_xxx)
| Código | Significado | Ação |
|--------|-------------|------|
| `RATE_001` | Rate limit excedido | Aguardar `Retry-After` header |

### Interno (INT_xxx)
| Código | Significado | Ação |
|--------|-------------|------|
| `INT_001` | Erro interno | Coletar trace_id e reportar |
| `INT_002` | Timeout | Verificar logs e retry |

---

## 🧪 Checklist de 5 Minutos

Quando algo não funciona, siga este checklist na ordem:

```
1. [ ] Rodar `make diagnose`
2. [ ] Verificar se .env está configurado: `make diagnose-env`
3. [ ] Verificar se portas estão livres: `make diagnose-ports`
4. [ ] Ver últimos erros: `make diagnose-logs`
5. [ ] Se erro de banco: `make diagnose-db`
```

---

## 🔍 Observabilidade (Grafana/Loki/Jaeger)

### Iniciar Stack
```bash
make obs-up
```

### Acessar
| Ferramenta | URL | Credenciais |
|------------|-----|-------------|
| Grafana | http://localhost:3033 | admin/devbridge |
| Jaeger | http://localhost:16686 | - |
| Loki | http://localhost:3100 | - |

### Buscar Logs no Grafana (Loki)
1. Acesse Grafana → Explore → Selecione "Loki"
2. Query por trace_id:
   ```
   {container="devbridge-backend-1"} |= "trace_id=SEU_ID"
   ```
3. Query por erros:
   ```
   {container="devbridge-backend-1"} |= "error"
   ```

### Rastrear Request no Jaeger
1. Acesse http://localhost:16686
2. Selecione serviço "devbridge-backend"
3. Busque pelo trace_id

---

## 🆘 Escalação

Se não conseguir resolver em 15 minutos:

1. Colete o `trace_id` do erro
2. Exporte logs relevantes:
   ```bash
   docker logs devbridge-backend-1 > backend-logs.txt 2>&1
   docker logs devbridge-worker-1 > worker-logs.txt 2>&1
   ```
3. Documente passos para reproduzir
4. Abra issue ou peça ajuda no time

---

## 📁 Arquivos Relevantes

| Arquivo | Propósito |
|---------|-----------|
| `backend/app/core/errors.py` | Definição de códigos de erro |
| `backend/app/core/exception_handlers.py` | Handlers de exceção |
| `backend/app/core/middleware.py` | Middleware com trace_id |
| `backend/app/core/logging.py` | Configuração de logging |
| `scripts/diagnose.sh` | Script de diagnóstico |
| `docs/development/error-codes.md` | Catálogo completo de erros DVB-xxx |
