"""
Report Template Endpoints.

CRUD API for customizable report templates.
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import CurrentOrgId, CurrentUser, CurrentUserRequired, DbSession
from app.models.report_template import ReportTemplate
from app.schemas.report_template import (
    DataFilters,
    LanguageConfig,
    ReportTemplateCreate,
    ReportTemplateListItem,
    ReportTemplateListResponse,
    ReportTemplateResponse,
    ReportTemplateUpdate,
    SectionConfig,
    VisualConfig,
)

router = APIRouter()


@router.post("", response_model=ReportTemplateResponse)
async def create_template(
    db: DbSession,
    request: ReportTemplateCreate,
    current_user: CurrentUser,
    org_id: CurrentOrgId,
) -> ReportTemplateResponse:
    """
    Create a new report template.

    Args:
        request: Template configuration.

    Returns:
        Created template with ID.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    template = ReportTemplate(
        organization_id=org_id,
        user_id=str(current_user.id),
        name=request.name,
        description=request.description,
        is_default=request.is_default,
        data_filters=request.data_filters.model_dump() if request.data_filters else None,
        sections_config=[s.model_dump() for s in request.sections_config],
        language_config=request.language_config.model_dump() if request.language_config else None,
        visual_config=request.visual_config.model_dump() if request.visual_config else None,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return _to_template_response(template)


@router.get("", response_model=ReportTemplateListResponse)
async def list_templates(
    db: DbSession,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> ReportTemplateListResponse:
    """
    List report templates for the organization.

    Returns both user-specific and organization-wide templates.
    """
    # Query templates for the org
    query = select(ReportTemplate).where(ReportTemplate.organization_id == org_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = (
        query.order_by(ReportTemplate.is_default.desc(), ReportTemplate.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    templates = result.scalars().all()

    items = [
        ReportTemplateListItem(
            id=str(t.id),
            name=t.name,
            description=t.description,
            is_default=t.is_default,
            created_at=t.created_at,
        )
        for t in templates
    ]

    return ReportTemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{template_id}", response_model=ReportTemplateResponse)
async def get_template(
    db: DbSession,
    template_id: str,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> ReportTemplateResponse:
    """Get a specific template by ID."""
    query = select(ReportTemplate).where(
        ReportTemplate.id == template_id,
        ReportTemplate.organization_id == org_id,
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return _to_template_response(template)


@router.put("/{template_id}", response_model=ReportTemplateResponse)
async def update_template(
    db: DbSession,
    template_id: str,
    request: ReportTemplateUpdate,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> ReportTemplateResponse:
    """Update a template."""
    query = select(ReportTemplate).where(
        ReportTemplate.id == template_id,
        ReportTemplate.organization_id == org_id,
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Update fields
    if request.name is not None:
        template.name = request.name
    if request.description is not None:
        template.description = request.description
    if request.is_default is not None:
        template.is_default = request.is_default
    if request.data_filters is not None:
        template.data_filters = request.data_filters.model_dump()
    if request.sections_config is not None:
        template.sections_config = [s.model_dump() for s in request.sections_config]
    if request.language_config is not None:
        template.language_config = request.language_config.model_dump()
    if request.visual_config is not None:
        template.visual_config = request.visual_config.model_dump()

    await db.commit()
    await db.refresh(template)

    return _to_template_response(template)


@router.delete("/{template_id}")
async def delete_template(
    db: DbSession,
    template_id: str,
    _current_user: CurrentUserRequired,
    org_id: CurrentOrgId,
) -> dict:
    """Delete a template."""
    from sqlalchemy import delete

    query = select(ReportTemplate.id).where(
        ReportTemplate.id == template_id,
        ReportTemplate.organization_id == org_id,
    )
    result = await db.execute(query)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Template not found")

    delete_query = delete(ReportTemplate).where(ReportTemplate.id == template_id)
    await db.execute(delete_query)
    await db.commit()

    return {"message": "Template deleted successfully"}


def _to_template_response(template: ReportTemplate) -> ReportTemplateResponse:
    """Convert model to response schema."""
    return ReportTemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        is_default=template.is_default,
        data_filters=DataFilters(**template.data_filters) if template.data_filters else None,
        sections_config=[SectionConfig(**s) for s in template.sections_config],
        language_config=LanguageConfig(**template.language_config)
        if template.language_config
        else None,
        visual_config=VisualConfig(**template.visual_config) if template.visual_config else None,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )
