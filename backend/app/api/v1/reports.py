"""
Report Endpoints.

API for structured report generation.
Implements BR-030 (persona-based reports) for PM, CTO, and CEO audiences.
"""

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentOrgId, CurrentUser, CurrentUserRequired, DbSession
from app.schemas.report import (
    ReportListResponse,
    ReportRequest,
    ReportResponse,
    ReportType,
    SavedReportResponse,
    SaveReportRequest,
)
from app.schemas.report_template import GenerateReportWithTemplate
from app.services.report_service import report_service

router = APIRouter()


@router.post("", response_model=ReportResponse)
async def generate_report(
    db: DbSession,
    request: ReportRequest,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> ReportResponse:
    """
    Generate a structured report for the specified period.

    Reports are tailored to different audiences (BR-030):
    - **weekly_summary**: For Product Managers - focus on deliverables, progress
    - **technical_report**: For CTO/Tech Leads - metrics, decisions, tech debt
    - **executive_summary**: For CEO/C-Level - max 5 bullets, zero jargon

    Args:
        db: Database session.
        request: Report request with type, period, and optional repository filters.
        _current_user: Authenticated user (required).
        org_id: Current organization context.

    Returns:
        ReportResponse with structured sections, metrics, and sources.

    Example request:
    ```json
    {
        "report_type": "weekly_summary",
        "period": {
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-01-07T23:59:59Z"
        },
        "repositories": ["devbridge"]
    }
    ```
    """
    return await report_service.generate_report(
        db=db,
        request=request,
        org_id=org_id,
    )


@router.get("/types")
async def list_report_types(
    _current_user: CurrentUserRequired,
) -> dict:
    """
    List available report types and their descriptions.

    Returns:
        Dictionary with report types and their intended audiences.
    """
    return {
        "types": [
            {
                "id": "weekly_summary",
                "name": "Resumo Semanal",
                "audience": "Product Manager",
                "description": "Foco em entregas, progresso nas metas, e próximos passos.",
            },
            {
                "id": "technical_report",
                "name": "Relatório Técnico",
                "audience": "CTO / Tech Lead",
                "description": "Decisões técnicas, qualidade de código, dívida técnica.",
            },
            {
                "id": "executive_summary",
                "name": "Resumo Executivo",
                "audience": "CEO / C-Level",
                "description": "Máximo 5 bullets, linguagem de negócio, foco em ROI.",
            },
        ]
    }


# ============================================================
# History/CRUD Endpoints
# ============================================================


@router.post("/save", response_model=SavedReportResponse)
async def save_report(
    db: DbSession,
    request: SaveReportRequest,
    current_user: CurrentUser,
    org_id: CurrentOrgId,
) -> SavedReportResponse:
    """
    Save a generated report to history.

    Args:
        db: Database session.
        request: Report data to save.
        current_user: Authenticated user.
        org_id: Organization context.

    Returns:
        SavedReportResponse with the saved report including ID.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return await report_service.save_report(
        db=db,
        request=request,
        org_id=org_id,
        user_id=str(current_user.id),
    )


@router.get("/history", response_model=ReportListResponse)
async def list_reports(
    db: DbSession,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    report_type: ReportType | None = Query(None, description="Filter by report type"),
) -> ReportListResponse:
    """
    List saved reports for the organization.

    Args:
        db: Database session.
        page: Page number (1-indexed).
        page_size: Number of items per page (max 50).
        report_type: Optional filter by report type.

    Returns:
        ReportListResponse with paginated list of reports.
    """
    return await report_service.list_reports(
        db=db,
        org_id=org_id,
        page=page,
        page_size=page_size,
        report_type=report_type,
    )


@router.get("/{report_id}", response_model=SavedReportResponse)
async def get_report(
    db: DbSession,
    report_id: str,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> SavedReportResponse:
    """
    Get a specific saved report by ID.

    Args:
        db: Database session.
        report_id: Report UUID.

    Returns:
        SavedReportResponse with full report details.

    Raises:
        HTTPException 404: If report not found.
    """
    report = await report_service.get_report(
        db=db,
        report_id=report_id,
        org_id=org_id,
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}")
async def delete_report(
    db: DbSession,
    report_id: str,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> dict:
    """
    Delete a saved report from history.

    Args:
        db: Database session.
        report_id: Report UUID.

    Returns:
        Success message.

    Raises:
        HTTPException 404: If report not found.
    """
    success = await report_service.delete_report(
        db=db,
        report_id=report_id,
        org_id=org_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted successfully"}


# ============================================================
# Custom Generation
# ============================================================


@router.post("/custom", response_model=SavedReportResponse)
async def generate_custom_report(
    db: DbSession,
    request: GenerateReportWithTemplate,
    current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> SavedReportResponse:
    """
    Generate a new custom report from template configuration.

    1. Fetches data based on filters.
    2. Uses LLM to generate content based on sections config.
    3. Saves report to database (history).
    """
    try:
        # 1. Generate & Save
        report_id = await report_service.generate_custom_report(
            db=db,
            request=request,
            org_id=org_id,
            user_id=str(current_user.id),
        )

        # 2. Retrieve Saved Report
        saved = await report_service.get_report(db, report_id, org_id)
        if not saved:
            raise HTTPException(status_code=500, detail="Failed to retrieve generated report")

        return saved
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR generating custom report: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Erro interno ao gerar relatório: {str(e)}"
        ) from e


# ============================================================
# PDF Export
# ============================================================


@router.post("/export/pdf")
async def export_report_to_pdf(
    db: DbSession,
    report_id: str,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
):
    """
    Export a saved report to PDF.

    Args:
        report_id: ID of saved report to export.

    Returns:
        PDF file as binary response.

    Raises:
        HTTPException 404: If report not found.
    """
    from fastapi.responses import Response

    from app.services.pdf_export_service import pdf_export_service

    # Get the saved report
    saved_report = await report_service.get_report(
        db=db,
        report_id=report_id,
        org_id=org_id,
    )
    if not saved_report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Convert to dict for PDF generation
    report_data = {
        "title": saved_report.title,
        "subtitle": saved_report.subtitle,
        "period_description": saved_report.period_description,
        "generated_at": saved_report.generated_at.isoformat() if saved_report.generated_at else "",
        "sections": [s.model_dump() for s in saved_report.sections],
        "summary_metrics": [m.model_dump() for m in saved_report.summary_metrics]
        if saved_report.summary_metrics
        else None,
        "sources_count": saved_report.sources_count,
        "confidence_score": saved_report.confidence_score,
    }

    # Generate PDF
    pdf_bytes = await pdf_export_service.export_to_pdf(report_data)

    # Return PDF as response
    filename = f"{saved_report.title.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
