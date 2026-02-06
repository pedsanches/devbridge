"""
Organization Endpoints.

CRUD operations for organizations with multi-tenant isolation.
"""

import re
import secrets

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import select

from app.api.deps import CurrentUserRequired, DbSession
from app.core.config import settings
from app.core.security import create_access_token
from app.models.membership import MemberRole, Membership
from app.models.organization import Organization, PlanType

router = APIRouter()


class OrganizationCreateRequest(BaseModel):
    """Request schema for creating an organization."""

    name: str
    slug: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Organization name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Organization name must be at most 100 characters")
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", v) and len(v) > 2:
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        if len(v) < 2:
            raise ValueError("Slug must be at least 2 characters")
        if len(v) > 50:
            raise ValueError("Slug must be at most 50 characters")
        return v


class OrganizationResponse(BaseModel):
    """Response schema for organization."""

    id: str
    name: str
    slug: str
    plan: str


class OrganizationCreateResponse(BaseModel):
    """Response schema for created organization with user info."""

    organization: OrganizationResponse
    switched: bool
    message: str


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from an organization name."""
    # Normalize: lowercase, replace spaces with hyphens, remove special chars
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    # Truncate and add random suffix for uniqueness
    slug = slug[:40]
    suffix = secrets.token_hex(4)
    return f"{slug}-{suffix}"


@router.post("", response_model=OrganizationCreateResponse, status_code=201)
async def create_organization(
    user: CurrentUserRequired,
    db: DbSession,
    request: OrganizationCreateRequest,
    response: Response,
) -> OrganizationCreateResponse:
    """
    Create a new organization.

    The current user will become the owner of the new organization.
    After creation, the user's session is switched to the new org context.
    """
    # Generate slug if not provided
    slug = request.slug if request.slug else generate_slug(request.name)

    # Check if slug already exists
    existing = await db.execute(select(Organization).where(Organization.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Organization with slug '{slug}' already exists",
        )

    # Create organization
    org = Organization(
        name=request.name,
        slug=slug,
        plan=PlanType.FREE,
    )
    db.add(org)
    await db.flush()

    # Create owner membership
    membership = Membership(
        organization_id=org.id,
        user_id=user.id,
        role=MemberRole.OWNER,
    )
    db.add(membership)
    await db.flush()

    # Issue new JWT scoped to the new organization
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "org_id": org.id,
            "role": MemberRole.OWNER.value,
        }
    )

    # Set httpOnly cookie
    response.set_cookie(
        key="session",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    await db.commit()
    await db.refresh(org)

    return OrganizationCreateResponse(
        organization=OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            plan=org.plan.value,
        ),
        switched=True,
        message=f"Organization '{org.name}' created successfully",
    )
