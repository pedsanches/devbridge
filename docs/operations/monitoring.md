# Monitoring e Observabilidade

Como monitorar a saúde e performance do DevBridge.

---

## Stack de Observabilidade

| Componente | Ferramenta | Uso |
|------------|------------|-----|
| **Logs** | Structured Logging | Todos os eventos |
| **Metrics** | Prometheus | Performance, throughput |
| **Traces** | Arize Phoenix | LLM calls, RAG pipeline |
| **Alerts** | Alertmanager | Notificações |

---

## Logs Estruturados

### Formato

Todos os logs são JSON estruturado:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "level": "INFO",
  "message": "Webhook processed",
  "context": {
    "request_id": "uuid",
    "repo": "user/repo",
    "commit_sha": "abc123",
    "duration_ms": 150
  }
}
```

### Níveis

| Nível | Quando Usar |
|-------|-------------|
| `DEBUG` | Informações detalhadas para troubleshooting |
| `INFO` | Eventos normais (webhook recebido, tradução gerada) |
| `WARNING` | Situações anômalas que não impedem operação |
| `ERROR` | Erros que afetam funcionalidade |
| `CRITICAL` | Falhas que requerem intervenção imediata |

### Configuração

```python
# app/core/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL),
)

log = structlog.get_logger()

# Uso
log.info("webhook_processed", repo="user/repo", duration_ms=150)
```

---

## Métricas Prometheus

### Exposição

```python
# Endpoint /metrics expõe métricas Prometheus
from prometheus_client import Counter, Histogram

WEBHOOK_COUNTER = Counter(
    "devbridge_webhooks_total",
    "Total webhooks received",
    ["repo", "event_type", "status"]
)

TRANSLATION_DURATION = Histogram(
    "devbridge_translation_duration_seconds",
    "Time to generate translation",
    buckets=[0.5, 1, 2, 5, 10, 30]
)
```

### Métricas Principais

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `devbridge_webhooks_total` | Counter | Webhooks por repo/tipo/status |
| `devbridge_translations_total` | Counter | Traduções geradas |
| `devbridge_translation_duration_seconds` | Histogram | Tempo de geração |
| `devbridge_llm_tokens_total` | Counter | Tokens consumidos |
| `devbridge_queue_size` | Gauge | Tamanho da fila Celery |
| `devbridge_db_connections` | Gauge | Conexões ativas PostgreSQL |

### Grafana Dashboards

```json
// Dashboard: DevBridge Overview
{
  "panels": [
    {
      "title": "Webhooks/min",
      "query": "rate(devbridge_webhooks_total[5m])"
    },
    {
      "title": "Translation P95 Latency",
      "query": "histogram_quantile(0.95, rate(devbridge_translation_duration_seconds_bucket[5m]))"
    },
    {
      "title": "Queue Backlog",
      "query": "devbridge_queue_size"
    },
    {
      "title": "LLM Token Usage/hour",
      "query": "increase(devbridge_llm_tokens_total[1h])"
    }
  ]
}
```

---

## Arize Phoenix (LLM Tracing)

### Por que usar

Phoenix permite visualizar exatamente o que entrou e saiu da LLM:
- Prompts enviados
- Respostas recebidas
- Tokens consumidos
- Latência por chamada

### Setup

```python
# app/core/observability.py
from phoenix.otel import register

tracer_provider = register(
    project_name="devbridge",
    endpoint="http://phoenix:6006/v1/traces"
)

# Instrumentação automática de LangChain
from openinference.instrumentation.langchain import LangChainInstrumentor
LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
```

### Acesso

```bash
# Local
http://localhost:6006

# Produção (via kubectl port-forward)
kubectl port-forward svc/phoenix 6006:6006
```

### O que monitorar

| Métrica | Alerta se |
|---------|-----------|
| Token usage | > 100k tokens/hora |
| Latência média | > 5s |
| Taxa de erro | > 5% |
| Confidence score médio | < 60 |

---

## Alertas

### Regras de Alerta

```yaml
# alerts/devbridge.yaml
groups:
  - name: devbridge
    rules:
      - alert: HighErrorRate
        expr: rate(devbridge_webhooks_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Alta taxa de erro em webhooks"
          description: "Mais de 10% dos webhooks estão falhando"

      - alert: QueueBacklog
        expr: devbridge_queue_size > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Backlog na fila de processamento"
          description: "Mais de 1000 tarefas esperando processamento"

      - alert: LLMHighLatency
        expr: histogram_quantile(0.95, rate(devbridge_translation_duration_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alta latência em traduções"
          description: "P95 de latência acima de 30s"
```

### Canais de Notificação

| Severidade | Canal |
|------------|-------|
| Critical | PagerDuty + Slack |
| Warning | Slack |
| Info | Email digest |

---

## Health Checks

### Endpoints

```
GET /health        # Básico (liveness)
GET /health/ready  # Dependências (readiness)
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Dependências Verificadas

| Dependência | Timeout | Ação se falhar |
|-------------|---------|----------------|
| PostgreSQL | 5s | Unhealthy |
| Redis | 2s | Unhealthy |
| Qdrant | 5s | Degraded |
| LLM API | 10s | Degraded |

---

## Debugging

### Logs em tempo real

```bash
# API
kubectl logs -f deployment/devbridge-api -n production

# Workers
kubectl logs -f deployment/devbridge-worker -n production

# Filtrar por request
kubectl logs deployment/devbridge-api | jq 'select(.request_id == "uuid")'
```

### Tracing de request

```bash
# Buscar traces por request_id no Phoenix
# ou via API
curl "http://phoenix:6006/v1/traces?filter=request_id=uuid"
```

### Métricas em tempo real

```bash
curl http://localhost:8001/metrics | grep devbridge
```
