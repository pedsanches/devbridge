# ADR-013: Stakeholder Access & Security Boundaries

**Data:** 2026-01-28

**Status:** Proposed

**Deciders:** Pedro, DevBridge Team

## Contexto

DevBridge precisa suportar stakeholders (PMs, C-level, Produto) que:
1. **Não têm conta GitHub**
2. **Precisam consumir informações de progresso técnico**
3. **Não devem ver dados sensíveis (diffs raw, PII)**

Atualmente:
- Auth via Magic Link (email) já existe — ✅
- Modelo `Membership` com role `VIEWER` existe — ✅
- Chat não filtra por Team — ❌ **SECURITY RISK**
- Não há distinção de conteúdo por role — ❌

### Problema de Segurança (Crítico)

O `chat_service.py` atual busca **ALL activities** sem filtrar por Team. Isso significa:
- User do Team A pode perguntar sobre repositórios do Team B
- Vazamento cross-team esperando acontecer

> [!CAUTION]
> Isso é um **security boundary**, não apenas UX.

## Decisão

### 1. Team como Security Boundary Obrigatório

> Todo endpoint de chat **DEVE** exigir `team_id` e validar membership.

```python
# Antes (inseguro)
async def chat(user_id: str, message: str):
    context = await get_all_activities()  # ❌ Cross-team leak

# Depois (seguro)
async def chat(user_id: str, team_id: str, message: str):
    # Valida membership
    membership = await get_membership(user_id, team_id)
    if not membership:
        raise HTTPException(403, "Not a member of this team")

    # Context scoped por team + role
    context = await get_context_for_team(team_id, membership.role)
```

### 2. Role-Based Content Filtering (no SQL, não no LLM)

| Role | Vê | Não Vê |
|------|-----|--------|
| VIEWER | BusinessUpdates, Cards sanitizados, métricas agregadas | Diffs raw, commits individuais detalhados |
| MEMBER | Tudo acima + diffs sanitizados, detalhes técnicos | - |
| ADMIN/OWNER | Tudo | - |

**Regra crítica:** Filtering acontece no SQL/repository layer, **antes** de montar contexto para LLM.

```python
async def get_context_for_team(team_id: str, role: MemberRole) -> list[dict]:
    if role == MemberRole.VIEWER:
        # Apenas BusinessUpdates agregados
        return await get_business_updates_for_team(team_id)
    else:
        # Activities completas (ainda sanitizadas por Presidio)
        return await get_activities_for_team(team_id)
```

### 3. Public References Registry (Smart References)

Em vez de tabela paralela `smart_references`, um registry unificado:

```sql
CREATE TABLE public_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) NOT NULL,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    external_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_ref_code UNIQUE (code),
    CONSTRAINT uq_ref_entity UNIQUE (team_id, entity_type, entity_id)
);

CREATE INDEX idx_ref_team_code ON public_references(team_id, code);
CREATE INDEX idx_ref_entity ON public_references(entity_type, entity_id);

-- Sequence para códigos sequenciais
CREATE SEQUENCE ref_code_seq START 1;
```

**Formato do código:** `R-{TEAM_SLUG}-{SEQ:06d}` (ex: `R-BACKEND-000123`)

**Geração race-safe:**
```python
async def generate_ref_code(team_id: str, team_slug: str) -> str:
    result = await db.execute(text("SELECT nextval('ref_code_seq')"))
    seq = result.scalar()
    return f"R-{team_slug.upper()}-{seq:06d}"
```

### 4. UI Cards para Stakeholders

VIEWER vê cards com:
- Título do PR/Commit
- Autor (nome, não username técnico)
- Tags de valor (VELOCITY_ENABLER, RISK_MITIGATION)
- Impacto (LOW/MEDIUM/HIGH)
- Smart Reference (R#)

**Não vê:**
- SHA do commit
- Diff inline
- Linhas de código específicas

## Alternativas Consideradas

### Alt A: Filtering no prompt do LLM
- **Prós:** Mais flexível
- **Contras:** LLM pode "vazar" info se prompt mal feito, mais tokens, menos seguro
- **Descartada:** Security deve ser enforced antes do LLM

### Alt B: Project vs Team (dois conceitos)
- **Prós:** Mais granularidade
- **Contras:** Confusão conceitual, mais complexity
- **Descartada:** Um boundary (Team) é suficiente. Nome não importa, enforcement sim.

### Alt C: Hash-based references (R#abc123)
- **Prós:** Sem race condition, simples
- **Contras:** Ilegível para humanos, ruim em Slack/conversas
- **Descartada:** UX de stakeholder é prioridade

## Consequências

### Positivas
- Zero vazamento cross-team
- Stakeholders têm experiência otimizada (sem ruído técnico)
- Referências auditáveis e legíveis
- Compliance com privacy-by-design

### Negativas
- Refactor significativo no chat_service.py
- Testes existentes precisam ser atualizados
- Migration de dados para popular team_id em conversas existentes

### Neutras
- VIEWER que quer "mais detalhes" pede upgrade de role

## Notas de Implementação

### Endpoints Afetados

```python
# TODOS precisam de team_id
POST /api/v1/chat          # + team_id obrigatório
GET  /api/v1/activities    # já tem team_id opcional → tornar obrigatório
GET  /api/v1/reports       # já scoped por team
```

### Middleware de Validação

```python
async def validate_team_access(
    user_id: str,
    team_id: str,
    required_role: MemberRole = MemberRole.VIEWER
) -> Membership:
    membership = await get_membership(user_id, team_id)
    if not membership:
        raise HTTPException(403, "Not a member of this team")
    if membership.role.value < required_role.value:
        raise HTTPException(403, "Insufficient permissions")
    return membership
```

### Migration Plan

1. Adicionar `team_id` a `conversations` (nullable inicialmente)
2. Backfill team_id baseado em repositórios mencionados
3. Tornar `team_id` NOT NULL após backfill
4. Atualizar testes

## Links Relacionados

- [ADR-007: Auth Strategy](./007-auth-strategy.md)
- [ADR-010: Data Sources Organization](./010-data-sources-organization.md)
- [membership.py](file:///home/pedro/desenvolvimento/devbridge/backend/app/models/membership.py)
