# ADR-011: Feedback Schema Design

**Status**: Accepted
**Date**: 2026-01-17
**Author**: Arquiteto Principal de Dados

## Context

O DevBridge precisa coletar feedback de usuários sobre as respostas geradas pela IA para:
1. Medir qualidade das respostas
2. Alimentar mecanismos de aprendizado contínuo
3. Detectar degradação de performance

O sistema de feedback precisa garantir:
- **Idempotência**: Mesmo feedback não pode ser contabilizado múltiplas vezes
- **Rastreabilidade**: Todo feedback deve ser ligado à geração específica que o originou
- **Imutabilidade**: Dados de feedback não são editados após criação

## Decision

### 1. Idempotência via Hash

Implementar `idempotency_key` como hash SHA-256 de:
```
{user_id}:{message_id}:{feedback_type}
```

Constraint UNIQUE no banco garante que envios duplicados são rejeitados.

**Rationale**: Permite que o frontend reenvie feedback sem risco de duplicação (resiliente a erros de rede).

### 2. Lineage Obrigatório

Campos `generation_id` e `prompt_version_id` são NOT NULL:
- `generation_id`: ID único da chamada LLM que gerou a resposta
- `prompt_version_id`: Hash do commit ou tag do prompt usado

**Rationale**: Aprendizado sem rastreabilidade gera corrupção de modelo. Feedback órfão é descartado do pipeline de treino.

### 3. Scoring Separado

Três campos de score:
- `score_raw`: Valor fixo por tipo (-1.0 a +1.0)
- `weight`: Trust score do usuário/origem (0.0 a 1.0)
- `score_effective`: Calculado (raw × weight) e persistido

**Rationale**: Permite ajustar peso de usuários suspeitos sem alterar dados originais.

### 4. Imutabilidade

Feedback é append-only. Não existe endpoint de UPDATE ou DELETE para usuários.

**Rationale**: Preserva integridade para auditorias e debugging.

## Consequences

### Positivas
- Resistente a flooding/spam de feedback
- Rastreabilidade completa para debugging
- Flexibilidade para trust scoring futuro
- Auditoria facilitada

### Negativas
- Requer geração de `generation_id` em cada resposta LLM
- Requer versionamento de prompts no deploy
- Mais campos no payload de feedback

## Mapping

| Campo | Propósito |
|-------|-----------|
| `idempotency_key` | Deduplicação |
| `generation_id` | Link exato para resposta LLM |
| `prompt_version_id` | Qual prompt foi usado |
| `score_raw` | Dado puro imutável |
| `weight` | Confiança no usuário |
| `score_effective` | Usado em cálculos |
| `extra_metadata` | Contexto adicional (latency, tokens) |

## References

- [Plano de Execução v1.1](continuous-learning-execution-plan.md)
- [Estratégia de Fluxo de Dados](continuous-learning-data-strategy.md)
