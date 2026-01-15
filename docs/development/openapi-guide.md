# Guia OpenAPI

Este documento descreve como usar e manter a documentação OpenAPI do DevBridge.

---

## Visão Geral

O DevBridge utiliza **OpenAPI 3.1** para documentar sua API REST. O arquivo principal está em [`docs/api/openapi.yaml`](../api/openapi.yaml).

## Acessando a Documentação

### Swagger UI (Desenvolvimento)

Quando o backend está rodando, acesse:

```
http://localhost:8001/api/v1/docs
```

O FastAPI gera automaticamente a UI do Swagger a partir do código.

### ReDoc (Alternativo)

```
http://localhost:8001/api/v1/redoc
```

### Spec OpenAPI (JSON)

```
http://localhost:8001/api/v1/openapi.json
```

---

## Estrutura do Arquivo

```yaml
openapi.yaml
├── info                 # Metadados da API
├── servers              # URLs dos ambientes
├── tags                 # Agrupamento de endpoints
├── paths                # Definição de endpoints
│   ├── /health
│   ├── /repos
│   ├── /commits
│   ├── /translations
│   └── /chat
└── components
    ├── securitySchemes  # Autenticação
    ├── parameters       # Parâmetros reutilizáveis
    ├── responses        # Respostas padrão
    └── schemas          # Modelos de dados
```

---

## Sincronização com Código

### FastAPI → OpenAPI (Geração Automática)

FastAPI gera a spec OpenAPI automaticamente a partir do código:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Repository(BaseModel):
    id: str
    name: str
    url: str

@app.get("/repos", response_model=list[Repository])
async def list_repos():
    ...
```

### OpenAPI → TypeScript (Geração de Tipos)

Use `openapi-typescript` para gerar tipos:

```bash
# Instalar
pnpm add -D openapi-typescript

# Gerar tipos
pnpm openapi-typescript docs/api/openapi.yaml -o packages/shared-types/src/generated.ts
```

### Script de Regeneração

```bash
# No Makefile
make generate-types:
    pnpm openapi-typescript docs/api/openapi.yaml -o packages/shared-types/src/generated.ts
```

---

## Convenções

### Nomenclatura

| Item | Convenção | Exemplo |
|------|-----------|---------|
| Paths | kebab-case plural | `/repos`, `/translations` |
| Parameters | camelCase | `perPage`, `repoId` |
| Schemas | PascalCase | `Repository`, `ChatRequest` |
| Operations | camelCase verbo+recurso | `listRepositories`, `getCommit` |

### Códigos de Erro

| Código HTTP | Uso |
|-------------|-----|
| 200 | Sucesso |
| 201 | Recurso criado |
| 400 | Request inválido |
| 401 | Não autenticado |
| 403 | Não autorizado |
| 404 | Não encontrado |
| 429 | Rate limit |
| 500 | Erro interno |

### Paginação

Todos os endpoints de listagem usam:

```yaml
parameters:
  - name: page
    in: query
    schema: { type: integer, default: 1 }
  - name: perPage
    in: query
    schema: { type: integer, default: 20, maximum: 100 }
```

---

## Validação

### Verificação de Contrato

```bash
make openapi-check
make openapi-sync  # Regenera docs/api/openapi.yaml
```

### Lint com Spectral

```bash
# Instalar
npm install -g @stoplight/spectral-cli

# Validar
spectral lint docs/api/openapi.yaml
```

### Configuração Spectral

```yaml
# .spectral.yaml
extends: spectral:oas
rules:
  operation-operationId: error
  operation-tags: error
  oas3-valid-schema-example: warn
```

---

## Versionamento

| Estratégia | Implementação |
|------------|---------------|
| URL | `/api/v1/`, `/api/v2/` |
| Header | Aceito mas não recomendado |

### Deprecação

```yaml
/old-endpoint:
  get:
    deprecated: true
    x-sunset: "2026-06-01"
    description: |
      **DEPRECATED** - Use `/new-endpoint` instead.
```

---

## Referências

- [OpenAPI 3.1 Spec](https://spec.openapis.org/oas/v3.1.0)
- [FastAPI OpenAPI](https://fastapi.tiangolo.com/advanced/extending-openapi/)
- [openapi-typescript](https://github.com/drwpow/openapi-typescript)
- [Spectral](https://github.com/stoplightio/spectral)
