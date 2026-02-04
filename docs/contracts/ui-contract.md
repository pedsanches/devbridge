# UI Contract & Compatibility Map

> **Single Source of Truth**: O código do Backend (`backend/app/schemas/ui_contract.py`) e a **fonte da verdade**. Este documento é derivado dele e serve de referência humana.
> **Verificação**: O teste `backend/tests/test_ui_contract.py` deve garantir que os Enums aqui listados batem com a implementação.
> **Version**: 1.1.0
> **Last Updated**: 2026-02-02

## 1. Mapeamento de Estados (Backend -> Frontend)

| Entidade | Backend State (Enum/Field) | Frontend Component | Icon (Lucide) | Visual Token (Tailwind) |
|----------|----------------------------|-------------------|---------------|-------------------------|
| **Severity** | `info` | `InsightCard` | `Info` | `text-info` / `bg-info/10` |
| | `success` | | `CheckCircle` | `text-success` / `bg-success/10` |
| | `warning` | | `AlertTriangle` | `text-warning` / `bg-warning/10` |
| | `error` | | `AlertCircle` | `text-error` / `bg-error/10` |
| **Confidence** | `high` (>= 0.8) | `ConfidenceBadge` | `Check` | `bg-success/15` text-success |
| | `medium` (>= 0.5) | | `HelpCircle` | `bg-warning/15` text-warning |
| | `low` (< 0.5) | | `AlertOctagon` | `bg-error/15` text-error |
| **JobStatus** | `queued` | `JobBadge` | `Clock` | `bg-neutral-100 text-neutral-500` |
| | `running` | | `Loader2` (spin) | `bg-primary/10 text-primary` |
| | `succeeded` | | `CheckCircle2` | `bg-success/10 text-success` |
| | `failed` | | `XCircle` | `bg-error/10 text-error` |
| | `canceled` | | `Ban` | `bg-neutral-200 text-neutral-600` |
| **Reference** | `pull_request` | `SmartReference` | `GitPullRequest` | `text-purple-500` |
| | `issue` | | `CircleDot` | `text-green-500` |
| | `commit` | | `GitCommit` | `text-blue-500` |
| | `doc` | | `FileText` | `text-orange-500` |
| | `slack` | | `MessageSquare` | `text-pink-500` |
| | `activity` (fallback) | | `Activity` | `text-neutral-500` |

## 2. Tipos Canônicos (Shared Schemas)

### 2.1. Reference & Evidence
`ReferenceType` e `EvidenceType` são unificados para simplificar a UI.

```python
# backend/app/schemas/ui_contract.py

class ReferenceType(str, Enum):
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    COMMIT = "commit"
    DOC = "doc"
    SLACK = "slack"
    METRIC = "metric"  # EvidenceType specific
    LOG = "log"        # EvidenceType specific
```

### 2.2. Shared Enums
Estes enums devem ter paridade 1:1.

```python
class Severity(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
```

## 3. Regras de Compatibilidade & Robustez

### 3.1. Tratamento de Falhas (Frontend)
O `SmartReference` e outros componentes de UI DEVEM ser resilientes:
1.  **Unknown Enum Value**: Se o backend enviar um `ReferenceType` novo (ex: "jira") que o front não conhece:
    - **NÃO** quebrar a renderização (crash).
    - **Fallback Icon**: Usar `Link` ou `File` genérico.
    - **Fallback Label**: Mostrar o valor cru da string (ex: "JIRA").
    - **Fallback Action**: Se houver URL, manter clicável.
2.  **Missing Payload**: Se faltar `title`, usar `ref_id` ou `external_id` como display text.

### 3.2. Formatação Obrigatória
- **Datas**: Backend SEMPRE em UTC (ISO8601). Frontend usa `Intl` para display local.
- **Numbers**: Backend envia raw types (`int`, `float`). Frontend aplica formatação (locale string, percentuais).
