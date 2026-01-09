# Fluxo de Dados

Como os dados fluem desde um push no GitHub até uma resposta no Slack.

## Fluxo de Ingestão (Webhook → Storage)

```mermaid
sequenceDiagram
    participant GH as GitHub
    participant API as FastAPI
    participant REDIS as Redis Queue
    participant WORKER as Celery Worker
    participant AST as Tree-sitter
    participant PII as Presidio
    participant AGENT as LangGraph
    participant PG as PostgreSQL
    participant QD as Qdrant

    GH->>API: Webhook (push/PR/review/issue)
    API->>API: Valida HMAC signature
    API->>REDIS: Enfileira task
    API-->>GH: 200 OK

    REDIS->>WORKER: Dequeue task
    WORKER->>GH: Busca detalhes (diff, reviews, stats)
    WORKER->>AST: Parse código alterado
    AST-->>WORKER: Estrutura AST

    WORKER->>PII: Sanitiza conteúdo
    PII-->>WORKER: Conteúdo limpo

    WORKER->>METRICS: Calcula métricas (DORA/SPACE)
    METRICS-->>WORKER: Métricas atualizadas

    WORKER->>AGENT: Processa com contexto
    AGENT->>AGENT: Nó 1: Análise Técnica
    AGENT->>AGENT: Nó 2: Mapeamento de Negócio
    AGENT->>AGENT: Nó 3: Auditoria de Qualidade
    AGENT-->>WORKER: BusinessTranslation (JSON)

    WORKER->>PG: Salva metadados e métricas
    WORKER->>QD: Salva embeddings
```

## Detalhes por Etapa

### 1. Recebimento do Webhook

```python
@app.post("/webhooks/github")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str = Header()
):
    payload = await request.body()

    # Valida assinatura HMAC
    if not verify_signature(payload, x_hub_signature_256):
        raise HTTPException(401)

    # Enfileira para processamento async
    task_id = process_github_event.delay(payload)

    return {"status": "queued", "task_id": task_id}
```

### 2. Parsing AST (Tree-sitter)

Identifica **O QUE** mudou estruturalmente:

| Tipo de Mudança | Exemplo |
|-----------------|---------|
| Nova função | `def calculate_tax()` adicionada |
| Refactoring | `UserService` renomeado para `UserManager` |
| Mudança de modelo | Campo `email` adicionado ao `User` |
| Dependência | `requests` adicionado ao `requirements.txt` |

### 3. Sanitização (Presidio)

Remove informações sensíveis antes de enviar para a LLM:

| Tipo | Antes | Depois |
|------|-------|--------|
| Email | `pedro@email.com` | `<EMAIL>` |
| CPF | `123.456.789-00` | `<CPF>` |
| API Key | `sk-ant-api03-xxx` | `<API_KEY>` |
| URL privada | `https://internal.company.com` | `<INTERNAL_URL>` |

### 4. Processamento LangGraph

```mermaid
stateDiagram-v2
    [*] --> TechnicalAnalyst
    TechnicalAnalyst --> BusinessMapper
    BusinessMapper --> Auditor
    Auditor --> QualityCheck
    QualityCheck --> BusinessMapper : Baixa confiança
    QualityCheck --> [*] : Alta confiança
```

**Nó 1 - Technical Analyst:**
> "O que mudou tecnicamente? Quais arquivos, funções, classes?"

**Nó 2 - Business Mapper:**
> "Como isso afeta o negócio? Cruze com `.devbridge.yaml`."

**Nó 3 - Auditor:**
> "A linguagem está clara? O score de confiança é adequado?"

### 5. Saída Estruturada

```python
class BusinessTranslation(BaseModel):
    title: str
    technical_summary: str
    business_value: str
    risks_mitigated: List[str]
    aligned_pillars: List[str]
    metrics: List[ImpactMetrics]
```

---

## Fluxo de Consulta (Chat → Resposta)

```mermaid
sequenceDiagram
    participant USER as Stakeholder
    participant UI as Next.js
    participant API as FastAPI
    participant ROUTER as Query Router
    participant QD as Qdrant
    participant LLM as Claude 3.5

    USER->>UI: "O que o time fez essa semana?"
    UI->>API: POST /api/chat
    API->>ROUTER: Classifica intenção
    ROUTER-->>API: tipo: weekly_summary

    API->>QD: Busca semântica + filtro temporal
    QD-->>API: Top 20 commits/PRs

    API->>LLM: Prompt + contexto
    LLM-->>API: Streaming response

    API-->>UI: SSE chunks
    UI-->>USER: Resposta formatada
```

## Tipos de Query e Roteamento

| Query | Tipo | Ação |
|-------|------|------|
| "O que foi feito essa semana?" | `weekly_summary` | Agregação por período |
| "Por que o PR #123 demorou?" | `pr_analysis` | Busca específica por PR |
| "Estamos progredindo nos OKRs?" | `okr_progress` | Cruza commits com metas |
| "O que o João fez?" | `developer_activity` | Filtro por autor |

## Próximos Passos

- [Arquitetura Overview](overview.md)
- [ADRs](decisions/) - decisões arquiteturais
