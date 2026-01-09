# ADR-008: Sistema de Reports Estruturados

**Data:** 2026-01-06

**Status:** Implemented

**Deciders:** Time de Desenvolvimento

## Contexto

O DevBridge traduz atividades técnicas em linguagem de negócio. Porém, diferentes stakeholders precisam de **formatos diferentes** de informação:

- **Product Manager (PM)**: Foco em entregas, progresso nas metas, roadmap
- **CTO/Tech Lead**: Métricas técnicas, decisões arquiteturais, dívida técnica
- **CEO/Executive**: Máximo 5 bullets, zero jargão técnico, foco em ROI

Conforme **BR-030** (Adaptação por Persona), precisamos de um sistema de reports que:
1. Gere relatórios estruturados por tipo de audiência
2. Permita templates reutilizáveis
3. Suporte exportação em PDF
4. Mantenha histórico de reports gerados

## Decisão

### Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FLUXO DE GERAÇÃO DE REPORTS                      │
│                                                                          │
│  1. Request             2. Fetch Data           3. AI Generation         │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐          │
│  │  Frontend   │───────▶│  ChatService│───────▶│  AIService  │          │
│  │  /reports   │        │  (RAG Query)│        │  (Claude)   │          │
│  └─────────────┘        └─────────────┘        └─────────────┘          │
│                                                       │                  │
│  6. Save/Export         5. Parse JSON           4. Structured JSON      │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐          │
│  │  History +  │◀───────│  Validation │◀───────│  Sections + │          │
│  │  PDF Export │        │  (Pydantic) │        │  Metrics    │          │
│  └─────────────┘        └─────────────┘        └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tipos de Report

```python
class ReportType(str, enum.Enum):
    WEEKLY_SUMMARY = "weekly_summary"      # PM: Entregas e progresso
    TECHNICAL_REPORT = "technical_report"  # CTO: Métricas técnicas
    EXECUTIVE_SUMMARY = "executive_summary" # CEO: Máx 5 bullets
    CUSTOM = "custom"                       # Template customizado
```

### Modelo de Dados

```python
class Report(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reports"

    # Multi-tenancy (ADR-006)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))

    # Metadata
    report_type: Mapped[ReportType]
    title: Mapped[str]
    subtitle: Mapped[str]

    # Period
    period_start: Mapped[datetime]
    period_end: Mapped[datetime]
    period_description: Mapped[str]

    # Content (JSONB for flexibility)
    sections_json: Mapped[dict]           # Lista de seções
    summary_metrics_json: Mapped[dict]    # Métricas resumidas

    # Analytics
    sources_count: Mapped[int]            # Quantas atividades foram usadas
    confidence_score: Mapped[float]       # Score de confiança (0-1)
    generated_at: Mapped[datetime]
```

### Templates Reutilizáveis

```python
class ReportTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "report_templates"

    organization_id: Mapped[UUID]
    created_by_id: Mapped[UUID]
    name: Mapped[str]
    description: Mapped[str | None]

    # Configuration (JSONB)
    config_json: Mapped[dict]  # Contém:
    # - sections_config: lista de seções com type, title, detail_level
    # - language_config: tom (formal/informal), idioma (pt-BR/en)
    # - data_filters: repositórios, tipos de atividade

    is_public: Mapped[bool]  # Compartilhar com toda a org
```

### Prompts por Persona

Cada tipo de report tem um prompt específico:

| Tipo | Foco | Formato | Tom |
|------|------|---------|-----|
| **WEEKLY_SUMMARY** | Entregas, progresso, pontos de atenção | 3-4 seções | Orientado a resultados |
| **TECHNICAL_REPORT** | Decisões técnicas, qualidade, dívida | 4-5 seções | Técnico mas conciso |
| **EXECUTIVE_SUMMARY** | Bullets com emojis de status | Máx 5 bullets | Zero jargão |

### Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `POST /api/v1/reports/generate` | POST | Gera report por tipo |
| `POST /api/v1/reports/` | POST | Salva report gerado |
| `GET /api/v1/reports/` | GET | Lista histórico (paginado) |
| `GET /api/v1/reports/{id}` | GET | Busca report específico |
| `DELETE /api/v1/reports/{id}` | DELETE | Remove do histórico |
| `GET /api/v1/reports/{id}/pdf` | GET | Exporta como PDF |
| `POST /api/v1/report-templates/` | POST | Cria template |
| `GET /api/v1/report-templates/` | GET | Lista templates |

### Integração com RAG Existente

O ReportService **reutiliza** o `ChatService.get_context_activities()` para buscar atividades, garantindo:
- Mesmo pipeline de busca semântica
- Filtro multi-tenant por `organization_id`
- Cache de embeddings via Qdrant

```python
# ReportService.generate_report()
activities = await chat_service.get_context_activities(
    db,
    org_id=org_id,
    repository_name=request.repositories,
    days=days,
    limit=50,
)
```

### Export PDF

Utilizamos **WeasyPrint** para geração de PDF:

```python
# pdf_export_service.py
class PDFExportService:
    async def export_report_to_pdf(
        self, report: SavedReportResponse
    ) -> bytes:
        html = self._render_html(report)  # Jinja2 template
        return self._generate_pdf(html)    # WeasyPrint
```

## Alternativas Consideradas

| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| **Prompts por persona (escolhido)** | Flexível, extensível | Cada tipo precisa de prompt | ✅ |
| Reports estáticos em template | Simples | Pouco flexível | ❌ |
| Geração 100% estruturada (sem AI) | Previsível | Perde riqueza de análise | ❌ |

## Consequências

### Positivas

- ✅ **Personalização**: Cada stakeholder recebe formato adequado
- ✅ **Reuso**: Templates salvos economizam tempo
- ✅ **Histórico**: Reports salvos para referência futura
- ✅ **Export**: PDF para compartilhamento offline
- ✅ **Integração**: Reutiliza RAG existente (zero duplicação)

### Negativas

- ❌ **Complexidade**: Mais código para manter
- ❌ **Custo LLM**: Cada report consome tokens
- ❌ **Latência**: Geração pode demorar 5-15s

### Mitigações

1. **Cache de reports** para períodos idênticos
2. **Loading states** claros na UI
3. **Limites de uso** por plano (free/pro/enterprise)

## Arquivos Implementados

| Arquivo | Descrição |
|---------|-----------|
| `models/report.py` | Model Report |
| `models/report_template.py` | Model ReportTemplate |
| `schemas/report.py` | Schemas Pydantic |
| `schemas/report_template.py` | Schemas de templates |
| `services/report_service.py` | Lógica de geração |
| `services/pdf_export_service.py` | Export PDF |
| `api/v1/reports.py` | Endpoints REST |
| `api/v1/report_templates.py` | Endpoints templates |

## Referências

- [ADR-006: SaaS Data Model](./006-saas-data-model.md)
- [BR-030: Adaptação por Persona](../business/rules-catalog.md)
- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/)
