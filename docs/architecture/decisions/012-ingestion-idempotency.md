# ADR-012: Ingestion Idempotency & Event Ledger

**Data:** 2026-01-28

**Status:** Proposed

**Deciders:** Pedro, DevBridge Team

## Contexto

O DevBridge recebe webhooks do GitHub que podem ser:
1. **Duplicados** — GitHub reenvia por timeout/5xx
2. **Updates legítimos** — mesmo PR com novo estado (reopened, synchronize)
3. **Eventos diferentes** — closed vs merged vs edited

Atualmente:
- `get_or_create_activity` usa `external_id` (sha/pr_number) para dedup básico
- Não há verificação de `X-GitHub-Delivery` header
- Não há tracking de estado (PR open→closed→merged)
- Reprocessamento de embeddings/resumos ocorre sem controle de versão

### Problemas Identificados

| Problema | Impacto |
|----------|---------|
| Webhook duplicado reprocessado | Custo desnecessário de LLM/CPU |
| Race condition entre pods | Dois workers processam mesmo delivery |
| PR state não atualizado | Dados desatualizados no chat |
| Derivados recomputados sempre | Custo alto de embedding |

## Decisão

Implementar idempotência em **3 níveis**:

### Nível 1: Event Ledger (Webhook Delivery)

> **PostgreSQL como fonte de verdade** com `INSERT ... ON CONFLICT DO NOTHING RETURNING` para resolver race conditions.

```sql
CREATE TABLE ingest_event_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'github',
    event_type VARCHAR(50) NOT NULL,
    repo_full_name VARCHAR(255) NOT NULL,
    installation_id BIGINT,

    -- Timestamps
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_started_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'received',
    attempt_count INTEGER NOT NULL DEFAULT 1,
    error_message TEXT,
    payload_hash VARCHAR(64),

    CONSTRAINT uq_ledger_delivery UNIQUE (delivery_id)
);

CREATE INDEX idx_ledger_repo ON ingest_event_ledger(repo_full_name);
CREATE INDEX idx_ledger_status ON ingest_event_ledger(status);
```

**Status enum:** `received` → `processing` → `completed` | `failed`

### Nível 2: Entity State Machine (PR/Issue)

Adicionar a `Activity`:

```sql
ALTER TABLE activities ADD COLUMN github_node_id VARCHAR(100) UNIQUE;
ALTER TABLE activities ADD COLUMN state VARCHAR(20);
ALTER TABLE activities ADD COLUMN state_updated_at TIMESTAMPTZ;
ALTER TABLE activities ADD COLUMN last_event_at TIMESTAMPTZ;
```

**Política de merge:** último evento vence via `last_event_at`.

**Eventos que disparam refresh:**
- `pull_request.synchronize` (novo commit)
- `pull_request.edited` (título/body mudou)
- `pull_request.closed` / `reopened`
- `pull_request.labeled` / `unlabeled`

### Nível 3: Derived Artifacts (P1)

```sql
CREATE TABLE derived_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    artifact_type VARCHAR(50) NOT NULL,
    pipeline_version VARCHAR(200) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    storage_ref TEXT,
    supersedes_artifact_id UUID REFERENCES derived_artifacts(id),
    is_current BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_artifact UNIQUE (entity_type, entity_id, artifact_type, pipeline_version, content_hash)
);

CREATE INDEX idx_artifact_entity ON derived_artifacts(entity_type, entity_id);
CREATE INDEX idx_artifact_current ON derived_artifacts(entity_id, is_current) WHERE is_current = true;
```

**pipeline_version formato:** `{prompt_hash}:{model_id}:{code_version}`

**Regra de cache:**
- `content_hash` igual + `pipeline_version` igual → cache hit
- `pipeline_version` mudou → recompute
- `content_hash` mudou → recompute

## Alternativas Consideradas

### Alt A: Redis TTL Only
- **Prós:** Rápido, simples
- **Contras:** Perde histórico, sem auditabilidade, não sobrevive restart
- **Descartada:** Não atende requisito de auditabilidade do DevBridge

### Alt B: Ledger sem state machine
- **Prós:** Mais simples de implementar
- **Contras:** PR "closed" fica stuck, updates legítimos ignorados
- **Descartada:** Dados ficariam desatualizados

## Consequências

### Positivas
- Zero reprocessamento de webhooks duplicados
- Auditabilidade completa de eventos recebidos
- PRs sempre com estado atual
- Economia de custo LLM via cache de derivados

### Negativas
- +3 tabelas novas no schema
- Complexidade adicional no webhook handler
- Migração de dados existentes necessária

### Neutras
- Redis como "hot dedupe" opcional (nice-to-have)

## Notas de Implementação

### Webhook Handler (race-safe)

```python
# webhooks.py
async def github_webhook(request: Request, ...):
    delivery_id = request.headers.get("X-GitHub-Delivery")

    # Atomic insert-or-ignore
    result = await db.execute(text("""
        INSERT INTO ingest_event_ledger (delivery_id, event_type, repo_full_name, payload_hash)
        VALUES (:delivery_id, :event_type, :repo, :hash)
        ON CONFLICT (delivery_id) DO UPDATE SET
            last_seen_at = NOW(),
            attempt_count = ingest_event_ledger.attempt_count + 1
        RETURNING id, attempt_count
    """), {...})

    row = result.fetchone()
    if row.attempt_count > 1:
        return {"status": "already_received", "delivery_id": delivery_id}

    # Mark processing
    await db.execute(text("""
        UPDATE ingest_event_ledger
        SET status = 'processing', processing_started_at = NOW()
        WHERE id = :id
    """), {"id": row.id})

    # Queue for worker
    task = process_webhook.delay(event, payload, ledger_id=str(row.id))
```

### Backfill de github_node_id

```python
async def backfill_node_ids():
    # Via GitHub GraphQL API
    # Marcar como migrated_legacy no ledger
```

## Links Relacionados

- [ADR-006: SaaS Data Model](./006-saas-data-model.md)
- [data-flow.md](../data-flow.md)
- GitHub Webhook Best Practices
