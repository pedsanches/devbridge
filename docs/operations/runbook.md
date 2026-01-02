# Runbook Operacional

Procedimentos para operação e resolução de incidentes.

---

## Contatos de Emergência

| Papel | Contato | Quando Acionar |
|-------|---------|----------------|
| Tech Lead | @pedro | Incidentes críticos |
| On-call | PagerDuty | Fora do horário |

---

## Classificação de Incidentes

| Severidade | Descrição | SLA Resposta | SLA Resolução |
|------------|-----------|--------------|---------------|
| **P1 - Critical** | Serviço indisponível | 15 min | 4 horas |
| **P2 - High** | Degradação significativa | 1 hora | 8 horas |
| **P3 - Medium** | Funcionalidade impactada | 4 horas | 24 horas |
| **P4 - Low** | Issue menor | 24 horas | 1 semana |

---

## Procedimentos de Incidente

### INC-001: API Indisponível

**Sintomas:**
- Health check retorna 5xx
- Usuários reportam erro ao acessar

**Diagnóstico:**
```bash
# 1. Verificar pods
kubectl get pods -n production -l app=devbridge-api

# 2. Verificar logs
kubectl logs -f deployment/devbridge-api -n production

# 3. Verificar recursos
kubectl top pods -n production
```

**Resolução:**
```bash
# Opção 1: Restart pods
kubectl rollout restart deployment/devbridge-api -n production

# Opção 2: Scale up
kubectl scale deployment/devbridge-api --replicas=5 -n production

# Opção 3: Rollback
kubectl rollout undo deployment/devbridge-api -n production
```

---

### INC-002: Database Connection Exhausted

**Sintomas:**
- Logs: "too many connections"
- Novas requests falham com 500

**Diagnóstico:**
```bash
# 1. Verificar conexões ativas
kubectl exec -it deployment/devbridge-api -- \
  psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity"

# 2. Identificar queries lentas
kubectl exec -it deployment/devbridge-api -- \
  psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active'"
```

**Resolução:**
```bash
# 1. Terminar queries presas
kubectl exec -it deployment/devbridge-api -- \
  psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query_start < now() - interval '5 minutes'"

# 2. Restart API para resetar pool
kubectl rollout restart deployment/devbridge-api
```

**Prevenção:**
- Ajustar `DB_POOL_SIZE` se recorrente
- Otimizar queries lentas

---

### INC-003: Queue Backlog Alto

**Sintomas:**
- Alerta: "QueueBacklog"
- Traduções demorando mais que usual

**Diagnóstico:**
```bash
# 1. Verificar tamanho da fila
redis-cli LLEN celery

# 2. Verificar workers
kubectl get pods -l app=devbridge-worker

# 3. Verificar logs de workers
kubectl logs -f deployment/devbridge-worker --tail=100
```

**Resolução:**
```bash
# 1. Scale workers
kubectl scale deployment/devbridge-worker --replicas=10

# 2. Se workers travando, restart
kubectl rollout restart deployment/devbridge-worker
```

**Pós-incidente:**
- Analisar se foi pico de uso ou problema em worker

---

### INC-004: LLM API Timeout

**Sintomas:**
- Traduções falhando com timeout
- Logs: "anthropic.TimeoutError"

**Diagnóstico:**
```bash
# 1. Verificar status da Anthropic
curl https://status.anthropic.com/api/v2/status.json

# 2. Verificar se é específico ou geral
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

**Resolução:**
```bash
# 1. Se API da Anthropic instável, configurar circuit breaker
# (já implementado via settings)

# 2. Aumentar timeout temporariamente
kubectl set env deployment/devbridge-worker LLM_TIMEOUT=120
```

**Mitigação:**
- Tasks falhas voltam para fila automaticamente
- Retry exponencial configurado

---

### INC-005: Qdrant Indisponível

**Sintomas:**
- Busca semântica falha
- Chat retorna respostas genéricas

**Diagnóstico:**
```bash
# 1. Verificar pod Qdrant
kubectl get pods -l app=qdrant

# 2. Verificar health
kubectl exec -it deployment/qdrant -- curl localhost:6333/health

# 3. Verificar storage
kubectl exec -it deployment/qdrant -- df -h /qdrant/storage
```

**Resolução:**
```bash
# 1. Restart Qdrant
kubectl rollout restart statefulset/qdrant

# 2. Se storage cheio, expandir PVC
kubectl patch pvc qdrant-storage -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
```

---

### INC-006: Webhook Signature Failures

**Sintomas:**
- Logs: "Invalid webhook signature"
- Commits não sendo processados

**Diagnóstico:**
```bash
# 1. Verificar secret configurado
kubectl get secret devbridge-secrets -o jsonpath='{.data.github-webhook-secret}' | base64 -d

# 2. Comparar com GitHub
# (no GitHub: Settings > Webhooks > Secret)
```

**Resolução:**
```bash
# 1. Atualizar secret se incorreto
kubectl create secret generic devbridge-secrets \
  --from-literal=github-webhook-secret=NOVO_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -

# 2. Restart API
kubectl rollout restart deployment/devbridge-api
```

---

## Manutenção Programada

### Backup de Database

```bash
# Executar via CronJob configurado ou manualmente
pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz
aws s3 cp backup-$(date +%Y%m%d).sql.gz s3://devbridge-backups/
```

### Rotação de Logs

```bash
# Logs são rotacionados automaticamente pelo Kubernetes
# Retenção: 7 dias localmente, 90 dias no S3
```

### Atualização de Dependências

```bash
# 1. Rodar em staging primeiro
poetry update
pnpm update

# 2. Rodar testes
poetry run pytest

# 3. Deploy em staging e validar

# 4. Deploy em produção
```

---

## Escaladas

### Quando Escalar

- P1 não resolvido em 30 min → escalar para Tech Lead
- P1 sem progresso em 2h → escalar para On-call Backup
- Problema recorrente (3x em uma semana) → pós-mortem obrigatório

### Template de Comunicação

```
[INCIDENTE P1] DevBridge - [Título breve]

Status: Em investigação / Mitigado / Resolvido
Impacto: [Descrição do impacto para usuários]
Início: [Timestamp]
Última atualização: [Timestamp]

Próximos passos:
- [Ação 1]
- [Ação 2]

Próxima atualização em: [X minutos]
```

---

## Pós-Mortem Template

```markdown
# Pós-Mortem: [Título]

**Data do Incidente:** YYYY-MM-DD
**Duração:** X horas
**Severidade:** P1/P2/P3

## Resumo
[1-2 frases sobre o que aconteceu]

## Timeline
- HH:MM - Primeiro sintoma detectado
- HH:MM - Alerta disparado
- HH:MM - Investigação iniciada
- HH:MM - Causa raiz identificada
- HH:MM - Mitigação aplicada
- HH:MM - Incidente resolvido

## Causa Raiz
[Explicação técnica detalhada]

## Impacto
- Usuários afetados: X
- Funcionalidade impactada: [descrição]
- Dados perdidos: Nenhum / [descrição]

## Ações de Follow-up
- [ ] [Ação 1] - Owner: @pessoa - Prazo: YYYY-MM-DD
- [ ] [Ação 2] - Owner: @pessoa - Prazo: YYYY-MM-DD

## Lições Aprendidas
- O que funcionou bem
- O que poderia melhorar
```
