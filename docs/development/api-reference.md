# Referência da API

Documentação dos endpoints da API REST do DevBridge.

---

> [!WARNING]
> **Atenção:** Este documento é mantido manualmente e pode estar desatualizado em relação à implementação atual.
>
> Para a referência mais precisa e testável em tempo real, utilize sempre o **Swagger UI** ou **Redoc**:
> - [Swagger UI (http://localhost:8000/docs)](http://localhost:8000/docs)
> - [Redoc (http://localhost:8000/redoc)](http://localhost:8000/redoc)

---

## 📚 Documentação Interativa

| Recurso | URL | Descrição |
|---------|-----|-----------|
| **Swagger UI** | [localhost:8000/docs](http://localhost:8000/docs) | Interface interativa |
| **ReDoc** | [localhost:8000/redoc](http://localhost:8000/redoc) | Documentação alternativa |
| **OpenAPI Spec** | [localhost:8000/openapi.json](http://localhost:8000/openapi.json) | Schema JSON |
| **OpenAPI YAML** | [`docs/api/openapi.yaml`](../api/openapi.yaml) | Schema versionado |

> [!TIP]
> Para detalhes sobre como usar e manter a spec OpenAPI, veja [`openapi-guide.md`](./openapi-guide.md)

---

## Base URL

```
http://localhost:8000/api
```

## Autenticação

Todos os endpoints (exceto health) requerem autenticação via Bearer token:

```bash
Authorization: Bearer <access_token>
```

---

## Health Check

### `GET /health`

Verifica status da API.

**Response 200:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-01T12:00:00Z"
}
```

---

## Autenticação

### `POST /auth/login`

Inicia fluxo OAuth com GitHub.

**Response 302:** Redirect para GitHub OAuth

---

### `GET /auth/callback`

Callback do OAuth GitHub.

**Query Parameters:**
- `code` (string): Código de autorização do GitHub

**Response 200:**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## Chat

### `POST /chat`

Envia mensagem para o assistente.

**Request Body:**
```json
{
  "message": "O que o time fez essa semana?",
  "repo_id": "uuid-do-repo",
  "audience": "pm"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `message` | string | Sim | Mensagem do usuário |
| `repo_id` | string | Não | Filtrar por repositório |
| `audience` | string | Não | Perfil: `pm`, `cto`, `ceo` |

**Response 200 (SSE Stream):**
```
data: {"type": "chunk", "content": "O time "}
data: {"type": "chunk", "content": "trabalhou em "}
data: {"type": "chunk", "content": "3 frentes..."}
data: {"type": "done", "message_id": "uuid"}
```

---

### `GET /chat/history`

Lista histórico de conversas.

**Query Parameters:**
- `limit` (int): Máximo de mensagens (default: 50)
- `before` (string): Cursor para paginação

**Response 200:**
```json
{
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "O que foi feito?",
      "created_at": "2025-01-01T12:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "O time trabalhou em...",
      "created_at": "2025-01-01T12:00:05Z"
    }
  ],
  "has_more": false,
  "next_cursor": null
}
```

---

## Repositórios

### `POST /repos`

Adiciona repositório para monitorar.

**Request Body:**
```json
{
  "url": "https://github.com/user/repo",
  "webhook_enabled": true,
  "default_branch": "main"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "url": "https://github.com/user/repo",
  "name": "repo",
  "owner": "user",
  "webhook_enabled": true,
  "webhook_secret": "generated-secret",
  "created_at": "2025-01-01T12:00:00Z"
}
```

---

### `GET /repos`

Lista repositórios monitorados.

**Response 200:**
```json
{
  "repos": [
    {
      "id": "uuid",
      "name": "repo",
      "owner": "user",
      "url": "https://github.com/user/repo",
      "last_sync": "2025-01-01T12:00:00Z",
      "commit_count": 150
    }
  ]
}
```

---

### `GET /repos/:id`

Detalhes de um repositório.

**Response 200:**
```json
{
  "id": "uuid",
  "name": "repo",
  "owner": "user",
  "url": "https://github.com/user/repo",
  "webhook_enabled": true,
  "default_branch": "main",
  "last_sync": "2025-01-01T12:00:00Z",
  "stats": {
    "total_commits": 150,
    "total_prs": 45,
    "translations_generated": 120
  }
}
```

---

### `DELETE /repos/:id`

Remove repositório do monitoramento.

**Response 204:** No content

---

## Webhooks

### `POST /webhooks/github`

Recebe eventos do GitHub.

**Headers:**
- `X-GitHub-Event`: Tipo do evento (push, pull_request, etc.)
- `X-Hub-Signature-256`: Assinatura HMAC

**Response 200:**
```json
{
  "status": "queued",
  "task_id": "uuid"
}
```

**Response 401:**
```json
{
  "error": "Invalid webhook signature"
}
```

---

## Traduções

### `GET /translations`

Lista traduções geradas.

**Query Parameters:**
- `repo_id` (string): Filtrar por repositório
- `since` (datetime): Data inicial
- `until` (datetime): Data final
- `limit` (int): Máximo de resultados

**Response 200:**
```json
{
  "translations": [
    {
      "id": "uuid",
      "commit_sha": "abc123",
      "title": "Otimização de Checkout",
      "technical_summary": "Refatorou função X",
      "business_value": "Reduz tempo em 40%",
      "confidence_score": 85,
      "aligned_pillars": ["conv_rate"],
      "created_at": "2025-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "has_more": false
}
```

---

### `GET /translations/:id`

Detalhes de uma tradução.

**Response 200:**
```json
{
  "id": "uuid",
  "commit_sha": "abc123",
  "pr_number": 42,
  "title": "Otimização de Checkout",
  "technical_summary": "Refatorou 3 funções do módulo de pagamentos...",
  "business_value": "Reduz tempo de checkout em 40%...",
  "risks_mitigated": ["Bug de timeout em conexões lentas"],
  "aligned_pillars": ["conv_rate", "tech_debt"],
  "metrics": [
    {
      "metric_name": "Response Time",
      "improvement_percentage": 40.0,
      "confidence_score": 90,
      "is_financial_estimate": false,
      "source": "PR benchmark results"
    }
  ],
  "created_at": "2025-01-01T12:00:00Z",
  "commit_url": "https://github.com/user/repo/commit/abc123"
}
```

---

## Erros

### Formato de Erro

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": [
      {
        "field": "message",
        "error": "Field is required"
      }
    ]
  }
}
```

### Códigos de Erro

| HTTP | Code | Descrição |
|------|------|-----------|
| 400 | `VALIDATION_ERROR` | Request inválido |
| 401 | `UNAUTHORIZED` | Token ausente ou inválido |
| 403 | `FORBIDDEN` | Sem permissão |
| 404 | `NOT_FOUND` | Recurso não encontrado |
| 429 | `RATE_LIMITED` | Muitas requests |
| 500 | `INTERNAL_ERROR` | Erro interno |

---

## Rate Limiting

- **Por usuário:** 1000 requests/hora
- **Por repositório (webhooks):** 100 requests/hora

Headers de resposta:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1704110400
```
