"""
Report Service.

Business logic for structured report generation.
Implements BR-030 (persona-based reports) using existing RAG infrastructure.
"""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.report import (
    ReportListResponse,
    ReportMetric,
    ReportPeriod,
    ReportRequest,
    ReportResponse,
    ReportSection,
    ReportSource,
    ReportType,
    SavedReportResponse,
    SaveReportRequest,
)
from app.schemas.report_template import (
    GenerateReportWithTemplate,
    LanguageConfig,
    SectionConfig,
)
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service

# Prompts for each report type (BR-030)
REPORT_PROMPTS: dict[ReportType, str] = {
    ReportType.WEEKLY_SUMMARY: """Você é um analista de produto gerando um RESUMO SEMANAL para um Product Manager.

FORMATO OBRIGATÓRIO:
Retorne um JSON com a seguinte estrutura:
{
    "sections": [
        {"title": "Principais Entregas", "content": "...", "metrics": null},
        {"title": "Progresso nas Metas", "content": "...", "metrics": null},
        {"title": "Pontos de Atenção", "content": "...", "metrics": null}
    ],
    "summary_metrics": [
        {"name": "Commits", "value": N, "change": "+X%", "trend": "up|down|stable"},
        {"name": "PRs Mergeados", "value": N, "change": "-X%", "trend": "up|down|stable"}
    ]
}

REGRAS:
- Foco em O QUE foi entregue e IMPACTO no produto
- Tom claro, orientado a resultados
- Use bullets curtos e objetivos
- Inclua métricas quantitativas quando disponíveis
- Máximo 3-4 seções""",
    ReportType.TECHNICAL_REPORT: """Você é um arquiteto de software gerando um RELATÓRIO TÉCNICO para um CTO/Tech Lead.

FORMATO OBRIGATÓRIO:
Retorne um JSON com a seguinte estrutura:
{
    "sections": [
        {"title": "Decisões Técnicas", "content": "...", "metrics": null},
        {"title": "Qualidade de Código", "content": "...", "metrics": [...]},
        {"title": "Dívida Técnica", "content": "...", "metrics": null},
        {"title": "Infraestrutura e DevOps", "content": "...", "metrics": null}
    ],
    "summary_metrics": [
        {"name": "Arquivos Modificados", "value": N, "change": null, "trend": null},
        {"name": "Autores Ativos", "value": N, "change": null, "trend": null}
    ]
}

REGRAS:
- Foco em decisões técnicas, padrões arquiteturais, e qualidade
- Tom técnico mas conciso, com números
- Mencione arquivos/componentes específicos quando relevante
- Destaque refactorings e melhorias de performance
- Máximo 4-5 seções""",
    ReportType.EXECUTIVE_SUMMARY: """Você é um consultor executivo gerando um RESUMO EXECUTIVO para CEO/C-Level.

FORMATO OBRIGATÓRIO:
Retorne um JSON com a seguinte estrutura:
{
    "sections": [
        {"title": "Resumo Executivo", "content": "• ✅ Ponto positivo 1\\n• ⚠️ Ponto de atenção\\n• 📊 Métrica principal", "metrics": null}
    ],
    "summary_metrics": [
        {"name": "Produtividade", "value": "Alta", "change": "+15%", "trend": "up"}
    ]
}

REGRAS CRÍTICAS:
- MÁXIMO 5 BULLETS no total
- ZERO jargão técnico - linguagem 100% de negócios
- Cada bullet DEVE começar com emoji de status (✅, ⚠️, 🚨, 📊, 📈)
- Foco em ROI, riscos, e impacto no negócio
- Resposta em NO MÁXIMO 10 linhas""",
}


class ReportService:
    """
    Service for generating structured reports.

    Orchestrates report generation using existing RAG infrastructure.
    Follows BR-030 (audience adaptation) and BR-010 (zero hallucination).
    """

    def _calculate_days(self, period: ReportPeriod) -> int:
        """Calculate number of days in the report period."""
        delta = period.end - period.start
        return max(delta.days + 1, 1)  # At least 1 day

    def _format_period(self, period: ReportPeriod) -> str:
        """Format period as human-readable string."""
        start_str = period.start.strftime("%d %b")
        end_str = period.end.strftime("%d %b %Y")
        return f"{start_str} - {end_str}"

    def _get_report_title(self, report_type: ReportType) -> str:
        """Get report title based on type."""
        titles = {
            ReportType.WEEKLY_SUMMARY: "Resumo Semanal",
            ReportType.TECHNICAL_REPORT: "Relatório Técnico",
            ReportType.EXECUTIVE_SUMMARY: "Resumo Executivo",
        }
        return titles.get(report_type, "Relatório")

    def _extract_metrics_from_activities(
        self, activities: list[dict[str, Any]]
    ) -> list[ReportMetric]:
        """Extract basic metrics from activities."""
        if not activities:
            return []

        # Count by type
        commits = sum(1 for a in activities if a.get("type") == "commit")
        prs = sum(1 for a in activities if a.get("type") == "pull_request")
        issues = sum(1 for a in activities if a.get("type") == "issue")

        # Count unique authors
        authors = {a.get("author") for a in activities if a.get("author")}

        # Count unique repos
        repos = {a.get("repository") for a in activities if a.get("repository")}

        metrics = [
            ReportMetric(
                name="Total de Atividades", value=len(activities), change=None, trend=None
            ),
        ]

        if commits:
            metrics.append(ReportMetric(name="Commits", value=commits, change=None, trend=None))
        if prs:
            metrics.append(ReportMetric(name="Pull Requests", value=prs, change=None, trend=None))
        if issues:
            metrics.append(ReportMetric(name="Issues", value=issues, change=None, trend=None))
        if authors:
            metrics.append(
                ReportMetric(
                    name="Desenvolvedores Ativos", value=len(authors), change=None, trend=None
                )
            )
        if repos:
            metrics.append(
                ReportMetric(name="Repositórios", value=len(repos), change=None, trend=None)
            )

        return metrics

    def _build_sources(
        self, activities: list[dict[str, Any]], max_sources: int = 10
    ) -> list[ReportSource]:
        """Build sources list from activities."""
        sources = []
        for act in activities[:max_sources]:
            sources.append(
                ReportSource(
                    title=act.get("title", "Untitled"),
                    repository=act.get("repository", "unknown"),
                    type=act.get("type", "unknown"),
                    url=act.get("url"),
                )
            )
        return sources

    async def generate_report(
        self,
        db: AsyncSession,
        request: ReportRequest,
        org_id: str,
    ) -> ReportResponse:
        """
        Generate a structured report for the specified period.

        Args:
            db: Database session.
            request: Report request with type, period, and filters.
            org_id: Organization ID for multi-tenant filtering.

        Returns:
            ReportResponse with structured sections and metrics.
        """
        # 1. Fetch activities using existing ChatService RAG
        days = self._calculate_days(request.period)
        activities = await chat_service.get_context_activities(
            db,
            org_id=org_id,
            repository_name=request.repositories,
            days=days,
            limit=50,  # More context for reports
        )

        # 2. Get prompt for report type
        prompt = REPORT_PROMPTS.get(request.report_type, REPORT_PROMPTS[ReportType.WEEKLY_SUMMARY])

        # 3. Format activities for AI context
        activities_context = self._format_activities_for_report(activities, request.period)

        # 4. Generate report content via AI
        report_content = await self._generate_report_content(
            activities_context=activities_context,
            prompt=prompt,
            _report_type=request.report_type,
        )

        # 5. Build response
        return ReportResponse(
            title=self._get_report_title(request.report_type),
            subtitle=f"Período: {self._format_period(request.period)}",
            generated_at=datetime.utcnow(),
            period_description=self._format_period(request.period),
            report_type=request.report_type,
            sections=report_content.get("sections", []),
            summary_metrics=report_content.get("summary_metrics")
            or self._extract_metrics_from_activities(activities),
            confidence_score=0.85 if activities else 0.3,
            sources_count=len(activities),
            sources=self._build_sources(activities),
            format="markdown",
        )

    def _format_activities_for_report(
        self, activities: list[dict[str, Any]], period: ReportPeriod
    ) -> str:
        """Format activities list into context string for report generation."""
        if not activities:
            return "Nenhuma atividade encontrada no período especificado."

        # Group by type
        by_type: dict[str, list[dict[str, Any]]] = {}
        for act in activities:
            act_type = act.get("type", "other")
            if act_type not in by_type:
                by_type[act_type] = []
            by_type[act_type].append(act)

        lines = [
            "# Atividades de Desenvolvimento",
            f"## Período: {self._format_period(period)}",
            f"## Total: {len(activities)} atividades",
            "",
        ]

        for act_type, type_activities in by_type.items():
            lines.append(f"### {act_type.upper()} ({len(type_activities)})")
            for act in type_activities[:15]:  # Limit per type
                title = act.get("title", "Untitled")[:100]
                author = act.get("author", "unknown")
                repo = act.get("repository", "unknown")
                date = act.get("date", "")[:10] if act.get("date") else ""
                lines.append(f"- [{date}] {title} (by {author} in {repo})")
            lines.append("")

        return "\n".join(lines)

    async def _generate_report_content(
        self,
        activities_context: str,
        prompt: str,
        _report_type: ReportType,
    ) -> dict[str, Any]:
        """Generate report sections via AI service."""
        import json

        full_prompt = f"""{prompt}

DADOS DE ATIVIDADES:
{activities_context}

Responda APENAS com o JSON no formato especificado, sem texto adicional."""

        try:
            response = await ai_service.generate_response(
                user_message=full_prompt,
                context="",
                max_tokens=2048,
            )

            # Try to parse JSON from response
            # Remove potential markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]

            parsed = json.loads(clean_response.strip())

            # Convert to proper types
            sections = []
            for s in parsed.get("sections", []):
                sections.append(
                    ReportSection(
                        title=s.get("title", "Seção"),
                        content=s.get("content", ""),
                        metrics=[ReportMetric(**m) for m in (s.get("metrics") or [])]
                        if s.get("metrics")
                        else None,
                    )
                )

            summary_metrics = None
            if parsed.get("summary_metrics"):
                summary_metrics = [ReportMetric(**m) for m in parsed["summary_metrics"]]

            return {
                "sections": sections,
                "summary_metrics": summary_metrics,
            }

        except (json.JSONDecodeError, Exception):
            # Fallback: create a simple section with raw response
            return {
                "sections": [
                    ReportSection(
                        title="Resumo",
                        content=response
                        if "response" in dir()
                        else "Não foi possível gerar o relatório.",
                        metrics=None,
                    )
                ],
                "summary_metrics": None,
            }

    # ============================================================
    # CRUD Methods for Report History
    # ============================================================

    async def save_report(
        self,
        db: AsyncSession,
        request: "SaveReportRequest",
        org_id: str,
        user_id: str,
    ) -> "SavedReportResponse":
        """
        Save a generated report to the database.

        Args:
            db: Database session.
            request: Report data to save.
            org_id: Organization ID.
            user_id: User ID.

        Returns:
            SavedReportResponse with the saved report data.
        """
        from app.models.report import Report as ReportModel
        from app.models.report import ReportType as ReportTypeEnum

        # Convert schema type to DB enum
        db_report_type = ReportTypeEnum(request.report_type.value)

        # Create report instance
        report = ReportModel(
            organization_id=org_id,
            user_id=user_id,
            report_type=db_report_type,
            title=request.title,
            subtitle=request.subtitle,
            period_start=request.period_start,
            period_end=request.period_end,
            period_description=request.period_description,
            sections_json=[s.model_dump() for s in request.sections],
            summary_metrics_json=[m.model_dump() for m in request.summary_metrics]
            if request.summary_metrics
            else None,
            sources_count=request.sources_count,
            confidence_score=request.confidence_score,
            generated_at=request.generated_at,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return self._to_saved_report_response(report)

    async def list_reports(
        self,
        db: AsyncSession,
        org_id: str,
        page: int = 1,
        page_size: int = 10,
        report_type: ReportType | None = None,
    ) -> "ReportListResponse":
        """
        List saved reports for an organization.

        Args:
            db: Database session.
            org_id: Organization ID.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            report_type: Optional filter by report type.

        Returns:
            ReportListResponse with paginated list.
        """
        from sqlalchemy import func, select

        from app.models.report import Report as ReportModel
        from app.schemas.report import ReportListItem, ReportListResponse

        # Build query
        query = select(ReportModel).where(ReportModel.organization_id == org_id)

        if report_type:
            from app.models.report import ReportType as ReportTypeEnum

            query = query.where(ReportModel.report_type == ReportTypeEnum(report_type.value))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(ReportModel.generated_at.desc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        reports = result.scalars().all()

        items = [
            ReportListItem(
                id=str(r.id),
                report_type=ReportType(r.report_type.value),
                title=r.title,
                period_description=r.period_description,
                generated_at=r.generated_at,
                sources_count=r.sources_count,
                confidence_score=r.confidence_score,
            )
            for r in reports
        ]

        return ReportListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(items)) < total,
        )

    async def get_report(
        self,
        db: AsyncSession,
        report_id: str,
        org_id: str,
    ) -> "SavedReportResponse | None":
        """
        Get a specific saved report by ID.

        Args:
            db: Database session.
            report_id: Report UUID.
            org_id: Organization ID for access control.

        Returns:
            SavedReportResponse if found, None otherwise.
        """
        from sqlalchemy import select

        from app.models.report import Report as ReportModel

        query = select(ReportModel).where(
            ReportModel.id == report_id,
            ReportModel.organization_id == org_id,
        )
        result = await db.execute(query)
        report = result.scalar_one_or_none()

        if not report:
            return None

        return self._to_saved_report_response(report)

    async def delete_report(
        self,
        db: AsyncSession,
        report_id: str,
        org_id: str,
    ) -> bool:
        """
        Delete a saved report.

        Args:
            db: Database session.
            report_id: Report UUID.
            org_id: Organization ID for access control.

        Returns:
            True if deleted, False if not found.
        """
        from sqlalchemy import delete, select

        from app.models.report import Report as ReportModel

        # Verify report exists and belongs to org
        query = select(ReportModel.id).where(
            ReportModel.id == report_id,
            ReportModel.organization_id == org_id,
        )
        result = await db.execute(query)
        if not result.scalar_one_or_none():
            return False

        # Delete
        delete_query = delete(ReportModel).where(ReportModel.id == report_id)
        await db.execute(delete_query)
        await db.commit()
        return True

    def _to_saved_report_response(self, report: Any) -> "SavedReportResponse":
        """Convert a Report model to SavedReportResponse schema."""
        from app.schemas.report import ReportMetric, ReportSection, SavedReportResponse

        sections = [ReportSection(**s) for s in (report.sections_json or [])]
        summary_metrics = (
            [ReportMetric(**m) for m in (report.summary_metrics_json or [])]
            if report.summary_metrics_json
            else None
        )

        return SavedReportResponse(
            id=str(report.id),
            title=report.title,
            subtitle=report.subtitle,
            report_type=ReportType(report.report_type.value),
            period_start=report.period_start,
            period_end=report.period_end,
            period_description=report.period_description,
            sections=sections,
            summary_metrics=summary_metrics,
            sources_count=report.sources_count,
            confidence_score=report.confidence_score,
            generated_at=report.generated_at,
            created_at=report.created_at,
        )

    async def generate_custom_report(
        self,
        db: AsyncSession,
        request: GenerateReportWithTemplate,
        org_id: str,
        user_id: str,
    ) -> str:
        """
        Generate a fully custom report based on template configuration.
        """
        from app.models.report import Report as ReportModel

        # 1. Fetch activities
        delta = request.period_end - request.period_start
        days = max(1, delta.days)

        # Get Repositories Filter
        repositories = None
        if request.data_filters and request.data_filters.repositories:
            repositories = request.data_filters.repositories

        activities = await chat_service.get_context_activities(
            db,
            org_id=org_id,
            repository_name=repositories,
            days=days,
            limit=100,
        )

        # 2. Build Context
        activities_context = self._format_activities_custom(
            activities, request.period_start, request.period_end
        )

        # 3. Build Prompt
        config_sections = request.sections_config or []
        lang = request.language_config

        prompt = self._build_custom_prompt(config_sections, lang)

        # 4. Generate Content (JSON)
        report_content = await self._generate_report_content(
            activities_context=activities_context,
            prompt=prompt,
            _report_type=ReportType.CUSTOM,
        )

        # 5. Save Report
        title = "Relatório Customizado"

        sections_data = report_content.get("sections", [])
        # Ensure we have serializable dicts, not Pydantic models
        sections_json = [s.model_dump() for s in sections_data] if sections_data else []

        summary_data = report_content.get("summary_metrics")
        summary_metrics_json = [m.model_dump() for m in summary_data] if summary_data else None

        report = ReportModel(
            organization_id=org_id,
            user_id=user_id,
            report_type=ReportType.CUSTOM,
            title=title,
            subtitle=f"{request.period_start.strftime('%d/%m/%Y')} - {request.period_end.strftime('%d/%m/%Y')}",
            period_start=request.period_start,
            period_end=request.period_end,
            period_description=f"{days} dias",
            sections_json=sections_json,
            summary_metrics_json=summary_metrics_json,
            sources_count=len(activities),
            confidence_score=0.9,
            generated_at=datetime.utcnow(),
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return str(report.id)

    def _format_activities_custom(
        self, activities: list[dict], start: datetime, end: datetime
    ) -> str:
        if not activities:
            return "Nenhuma atividade encontrada no período."

        lines = [
            "# Atividades de Desenvolvimento",
            f"## Período: {start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}",
            f"## Total: {len(activities)} atividades",
            "",
        ]

        by_type: dict[str, list[dict[str, Any]]] = {}
        for act in activities:
            t = act.get("type", "other")
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(act)

        for t, acts in by_type.items():
            lines.append(f"### {t.upper()} ({len(acts)})")
            for a in acts:
                content = a.get("content", "") or ""
                lines.append(
                    f"- [{a.get('repository')}] {a.get('title')}\n  Detalhes: {content[:300]}..."
                )
            lines.append("")

        return "\n".join(lines)

    def _build_custom_prompt(
        self, sections: list[SectionConfig], lang: LanguageConfig | None
    ) -> str:
        tone = "neutro"
        lang_code = "pt-BR"
        if lang:
            tone = lang.tone.value if hasattr(lang.tone, "value") else lang.tone
            lang_code = lang.language.value if hasattr(lang.language, "value") else lang.language

        enabled_sections = [s for s in sections if s.enabled]
        sections_str = []
        for s in enabled_sections:
            detail = s.detail_level.value if hasattr(s.detail_level, "value") else s.detail_level
            prompt_extra = f"(Prompt customizado: {s.custom_prompt})" if s.custom_prompt else ""
            sections_str.append(
                f"- Título: '{s.title}' (Tipo: {s.type.value if hasattr(s.type, 'value') else s.type}, Detalhe: {detail}) {prompt_extra}"
            )

        sections_block = "\n".join(sections_str)

        prompt = f"""Você é um assistente especialista em gerar relatórios de desenvolvimento de software.

IDIOMA DE SAIDA: {lang_code}
TOM: {tone}

CONTEXTO:
Abaixo estão as atividades de desenvolvimento (commits, PRs) do período e instruções precisas sobre quais seções gerar.

TAREFA:
Gere um relatório JSON contendo EXATAMENTE as seções solicitadas abaixo.

SEÇÕES SOLICITADAS:
{sections_block}

FORMATO DE RESPOSTA (JSON):
{{
    "sections": [
        {{ "title": "Título da Seção", "content": "Texto formatado em markdown...", "metrics": null }},
        ...
    ],
    "summary_metrics": [
         {{ "name": "Métrica", "value": "Valor", "change": null, "trend": null }}
    ]
}}

REGRAS:
- Use Markdown no campo 'content'.
- Ignore seções desabilitadas.
- Baseie-se apenas nas atividades fornecidas.
"""
        return prompt


# Singleton instance
report_service = ReportService()
