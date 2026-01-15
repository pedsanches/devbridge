# Códigos de Erro

Catálogo padronizado de códigos de erro do DevBridge.

---

## Formato

Todos os erros seguem o padrão:

```json
{
  "code": "DVB-XXX",
  "message": "Human readable message",
  "details": { /* optional context */ }
}
```

---

## Catálogo de Erros

### Autenticação (DVB-0xx)

| Código | HTTP | Mensagem | Causa | Ação |
|--------|------|----------|-------|------|
| DVB-001 | 401 | Invalid or expired token | Token JWT inválido ou expirado | Renovar token via refresh |
| DVB-002 | 401 | Missing authorization header | Header Authorization ausente | Incluir Bearer token |
| DVB-003 | 403 | Insufficient permissions | Usuário sem permissão para ação | Verificar role do usuário |
| DVB-004 | 401 | GitHub OAuth failed | Falha na autenticação OAuth | Tentar login novamente |

### Repositórios (DVB-1xx)

| Código | HTTP | Mensagem | Causa | Ação |
|--------|------|----------|-------|------|
| DVB-100 | 404 | Repository not found | Repositório não existe no sistema | Verificar ID ou adicionar repo |
| DVB-101 | 400 | Invalid repository URL | URL do GitHub inválida | Usar formato `https://github.com/owner/repo` |
| DVB-102 | 409 | Repository already exists | Repositório já cadastrado | Usar repositório existente |
| DVB-103 | 403 | No access to repository | Sem acesso ao repo no GitHub | Verificar permissões do GitHub App |
| DVB-104 | 422 | Missing .devbridge.yaml | Arquivo de config não encontrado | Adicionar `.devbridge.yaml` ao repo |

### Webhooks (DVB-2xx)

| Código | HTTP | Mensagem | Causa | Ação |
|--------|------|----------|-------|------|
| DVB-200 | 400 | Invalid webhook signature | Assinatura HMAC inválida | Verificar GITHUB_WEBHOOK_SECRET |
| DVB-201 | 400 | Unsupported event type | Tipo de evento não suportado | Verificar eventos configurados |
| DVB-202 | 422 | Webhook payload malformed | Payload JSON inválido | Verificar formato do webhook |
| DVB-203 | 503 | Webhook processing failed | Falha no processamento | Verificar logs do worker |

### Tradução (DVB-3xx)

| Código | HTTP | Mensagem | Causa | Ação |
|--------|------|----------|-------|------|
| DVB-300 | 404 | Translation not found | Tradução não existe | Verificar commit_sha |
| DVB-301 | 422 | Unable to analyze commit | Commit não analisável | Verificar se tem arquivos válidos |
| DVB-302 | 503 | LLM service unavailable | Claude API indisponível | Retry em alguns segundos |
| DVB-303 | 422 | Low confidence translation | Score de confiança muito baixo | Revisar manualmente |

### Chat (DVB-4xx)

| Código | HTTP | Mensagem | Causa | Ação |
|--------|------|----------|-------|------|
| DVB-400 | 400 | Empty message | Mensagem vazia enviada | Enviar mensagem com conteúdo |
| DVB-401 | 404 | Conversation not found | Conversa não existe | Iniciar nova conversa |
| DVB-402 | 429 | Chat rate limit exceeded | Muitas mensagens por minuto | Aguardar 60 segundos |
| DVB-403 | 503 | Chat service unavailable | Serviço de chat indisponível | Retry em alguns segundos |

### Rate Limiting (DVB-5xx)

| Código | HTTP | Mensagem | Causa | Ação |
|--------|------|----------|-------|------|
| DVB-500 | 429 | API rate limit exceeded | Limite de requests atingido | Aguardar conforme `Retry-After` header |
| DVB-501 | 429 | GitHub API rate limit | Limite do GitHub atingido | Aguardar reset do rate limit |

### Interno (DVB-9xx)

| Código | HTTP | Mensagem | Causa | Ação |
|--------|------|----------|-------|------|
| DVB-900 | 500 | Internal server error | Erro não esperado | Reportar com request ID |
| DVB-901 | 503 | Database unavailable | PostgreSQL indisponível | Verificar conectividade |
| DVB-902 | 503 | Redis unavailable | Redis indisponível | Verificar conectividade |
| DVB-903 | 503 | Vector DB unavailable | Qdrant indisponível | Verificar conectividade |

---

## Códigos Semânticos (Novo Sistema)

O novo sistema de erros usa códigos semânticos por categoria. Estes são usados na resposta padronizada:

```json
{
  "error_id": "uuid-único",
  "trace_id": "trace-para-logs",
  "error_code": "AUTH_001",
  "message": "Mensagem amigável",
  "path": "/api/v1/endpoint"
}
```

### Autenticação (AUTH_xxx)

| Código | HTTP | Descrição | Ação |
|--------|------|-----------|------|
| `AUTH_001` | 401 | Token inválido | Fazer novo login |
| `AUTH_002` | 401 | Token expirado | Fazer novo login |
| `AUTH_003` | 401 | Não autenticado | Incluir token na request |
| `AUTH_004` | 403 | Sem permissão | Verificar role do usuário |

### Validação (VAL_xxx)

| Código | HTTP | Descrição | Ação |
|--------|------|-----------|------|
| `VAL_001` | 422 | Validação falhou | Ver campo `details.validation_errors` |
| `VAL_002` | 422 | Campo obrigatório faltando | Adicionar campo |
| `VAL_003` | 422 | Formato inválido | Verificar formato esperado |

### Recursos (RES_xxx)

| Código | HTTP | Descrição | Ação |
|--------|------|-----------|------|
| `RES_001` | 404 | Recurso não encontrado | Verificar ID do recurso |
| `RES_002` | 409 | Recurso já existe | Usar recurso existente |
| `RES_003` | 409 | Conflito de recurso | Resolver conflito |

### Serviços Externos (EXT_xxx)

| Código | HTTP | Descrição | Ação |
|--------|------|-----------|------|
| `EXT_001` | 502 | Erro GitHub API | Verificar `GITHUB_TOKEN` |
| `EXT_002` | 502 | Erro OpenAI/LLM | Verificar `OPENAI_API_KEY` |
| `EXT_003` | 502 | Erro Database | Verificar conexão PostgreSQL |
| `EXT_004` | 502 | Erro Redis | Verificar conexão Redis |

### Rate Limiting (RATE_xxx)

| Código | HTTP | Descrição | Ação |
|--------|------|-----------|------|
| `RATE_001` | 429 | Rate limit excedido | Aguardar `Retry-After` header |

### Interno (INT_xxx)

| Código | HTTP | Descrição | Ação |
|--------|------|-----------|------|
| `INT_001` | 500 | Erro interno | Coletar `trace_id` e reportar |
| `INT_002` | 504 | Timeout | Verificar logs e retry |

---

## Mapeamento DVB ↔ Semântico

| Código DVB | Código Semântico |
|------------|------------------|
| DVB-001 | AUTH_001 |
| DVB-002 | AUTH_003 |
| DVB-003 | AUTH_004 |
| DVB-100 | RES_001 |
| DVB-200 | VAL_001 |
| DVB-500 | RATE_001 |
| DVB-900 | INT_001 |

---

## Implementação

### Python (Backend)

```python
from enum import Enum
from pydantic import BaseModel


class ErrorCode(str, Enum):
    INVALID_TOKEN = "DVB-001"
    REPO_NOT_FOUND = "DVB-100"
    WEBHOOK_INVALID_SIGNATURE = "DVB-200"
    # ...


class ApiError(BaseModel):
    code: ErrorCode
    message: str
    details: dict | None = None


class DevBridgeException(Exception):
    def __init__(self, code: ErrorCode, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)
```

### TypeScript (Frontend)

```typescript
// Importar do @devbridge/shared-types
import type { ApiError } from "@devbridge/shared-types";

function handleApiError(error: ApiError): void {
  switch (error.code) {
    case "DVB-001":
      // Token expirado - redirect para login
      redirectToLogin();
      break;
    case "DVB-500":
      // Rate limit - mostrar toast
      showToast("Muitas requisições. Aguarde um momento.");
      break;
    default:
      showToast(error.message);
  }
}
```

---

## Headers de Erro

Erros de rate limit incluem headers adicionais:

| Header | Descrição |
|--------|-----------|
| `X-RateLimit-Limit` | Limite de requests |
| `X-RateLimit-Remaining` | Requests restantes |
| `X-RateLimit-Reset` | Timestamp do reset |
| `Retry-After` | Segundos para retry |
