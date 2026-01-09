# ADR-006: Modelo de Dados Multi-Tenant (SaaS)

**Data:** 2026-01-03

**Status:** Accepted

**Deciders:** Time de Arquitetura

## Contexto

Conforme decisão em [ADR-005](./005-product-strategy.md), o DevBridge adotará modelo **Multi-tenant SaaS**. Isso requer:

1. Isolamento de dados por organização (tenant)
2. Hierarquia `Organization > Team > Repository`
3. Controle de acesso baseado em roles (RBAC)
4. Suporte futuro a billing por organização

O modelo atual é single-tenant: `Repository > Activity > BusinessUpdate`. Precisamos expandir para suportar múltiplas organizações.

## Decisão

### Diagrama ER (Entity-Relationship)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              ORGANIZATION                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ id: UUID (PK)                                                    │    │
│  │ name: VARCHAR(255) NOT NULL                                      │    │
│  │ slug: VARCHAR(100) UNIQUE NOT NULL  -- para URLs               │    │
│  │ plan: ENUM('free', 'pro', 'enterprise') DEFAULT 'free'          │    │
│  │ created_at: TIMESTAMP                                            │    │
│  │ updated_at: TIMESTAMP                                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                    ┌───────────────┼───────────────┐                    │
│                    │               │               │                    │
│                    ▼               ▼               ▼                    │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐    │
│  │      TEAM        │   │    MEMBERSHIP    │   │   ORG_SETTINGS   │    │
│  ├──────────────────┤   ├──────────────────┤   ├──────────────────┤    │
│  │ id: UUID (PK)    │   │ id: UUID (PK)    │   │ id: UUID (PK)    │    │
│  │ organization_id  │◄──│ organization_id  │   │ organization_id  │    │
│  │ name: VARCHAR    │   │ user_id (FK)     │   │ devbridge_config │    │
│  │ slug: VARCHAR    │   │ team_id (FK)?    │   │ slack_webhook    │    │
│  │ created_at       │   │ role: ENUM       │   │ github_app_id    │    │
│  └──────────────────┘   │ created_at       │   └──────────────────┘    │
│           │             └──────────────────┘                            │
│           │                      │                                      │
│           ▼                      ▼                                      │
│  ┌──────────────────┐   ┌──────────────────┐                           │
│  │   REPOSITORY     │   │      USER        │                           │
│  ├──────────────────┤   ├──────────────────┤                           │
│  │ id: UUID (PK)    │   │ id: UUID (PK)    │                           │
│  │ organization_id  │   │ email: UNIQUE    │                           │
│  │ team_id (FK)?    │   │ name: VARCHAR    │                           │
│  │ name: VARCHAR    │   │ avatar_url       │                           │
│  │ owner: VARCHAR   │   │ created_at       │                           │
│  │ url: VARCHAR     │   └──────────────────┘                           │
│  │ is_active: BOOL  │                                                   │
│  └──────────────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────┐                                                   │
│  │    ACTIVITY      │                                                   │
│  ├──────────────────┤                                                   │
│  │ id: UUID (PK)    │                                                   │
│  │ repository_id    │                                                   │
│  │ external_id      │                                                   │
│  │ type: ENUM       │                                                   │
│  │ title, content   │                                                   │
│  │ author           │                                                   │
│  │ diff_content     │  -- NEW: stores code diff                        │
│  └──────────────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌──────────────────┐                                                   │
│  │  BUSINESS_UPDATE │                                                   │
│  ├──────────────────┤                                                   │
│  │ id: UUID (PK)    │                                                   │
│  │ activity_id      │                                                   │
│  │ summary: TEXT    │                                                   │
│  │ impact_level     │                                                   │
│  │ category         │                                                   │
│  │ embedding_id     │  -- NEW: Qdrant point ID                         │
│  └──────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Novas Entidades

#### 1. Organization (Tenant)

```python
class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(
        Enum("free", "pro", "enterprise", name="plan_type"),
        default="free",
        nullable=False,
    )

    # Relationships
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="organization", cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    settings = relationship("OrganizationSettings", uselist=False, back_populates="organization")
```

#### 2. Team

```python
class Team(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "teams"

    organization_id = Column(Uuid, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_team_org_slug"),
    )

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    repositories = relationship("Repository", back_populates="team")
    memberships = relationship("Membership", back_populates="team")
```

#### 3. User

```python
class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    email_verified_at = Column(DateTime, nullable=True)

    # Relationships
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
```

#### 4. Membership (User ↔ Org/Team)

```python
class MemberRole(str, enum.Enum):
    OWNER = "owner"      # Full control, billing
    ADMIN = "admin"      # Manage org/team settings
    MEMBER = "member"    # Full access to repos
    VIEWER = "viewer"    # Read-only, business summaries

class Membership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "memberships"

    organization_id = Column(Uuid, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    team_id = Column(Uuid, ForeignKey("teams.id"), nullable=True, index=True)  # NULL = org-level
    role = Column(Enum(MemberRole), nullable=False, default=MemberRole.MEMBER)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", "team_id", name="uq_membership"),
    )

    # Relationships
    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")
    team = relationship("Team", back_populates="memberships")
```

#### 5. OrganizationSettings

```python
class OrganizationSettings(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organization_settings"

    organization_id = Column(Uuid, ForeignKey("organizations.id"), unique=True, nullable=False)
    devbridge_config = Column(JSONB, nullable=True)  # .devbridge.yaml content
    slack_webhook_url = Column(String(500), nullable=True)
    github_app_installation_id = Column(BigInteger, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="settings")
```

#### 6. Issue
Rastreamento de tarefas e bugs.

```python
class IssueState(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"

class Issue(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "issues"

    repository_id = Column(UUID, ForeignKey("repositories.id"), nullable=False, index=True)
    issue_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(Enum(IssueState), nullable=False)
    author = Column(String(255), nullable=False)
    assignees = Column(ARRAY(String), nullable=True)
    labels = Column(ARRAY(String), nullable=True)
    milestone = Column(String(255), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String(255), nullable=True)

    # Metrics
    time_to_close_hours = Column(Float, nullable=True)
    linked_pr_numbers = Column(ARRAY(Integer), nullable=True)

    __table_args__ = (
        UniqueConstraint("repository_id", "issue_number", name="uq_issue_repo_number"),
    )
```

#### 7. CodeReview
Rastreamento de qualidade de revisão de código.

```python
class ReviewState(str, enum.Enum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    PENDING = "PENDING"
    DISMISSED = "DISMISSED"

class CodeReview(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "code_reviews"

    activity_id = Column(UUID, ForeignKey("activities.id"), nullable=False, index=True)
    reviewer = Column(String(255), nullable=False)
    state = Column(Enum(ReviewState), nullable=False)
    body = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False)

    # Metrics
    comments_count = Column(Integer, default=0)
```

#### 8. DeveloperProfile
Métricas agregadas por desenvolvedor.

```python
class DeveloperProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "developer_profiles"

    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    github_username = Column(String(255), nullable=False)

    # Aggregated Metrics
    total_commits = Column(Integer, default=0)
    total_prs_created = Column(Integer, default=0)
    total_prs_merged = Column(Integer, default=0)
    total_reviews_given = Column(Integer, default=0)
    total_issues_closed = Column(Integer, default=0)
    total_lines_added = Column(BigInteger, default=0)
    total_lines_deleted = Column(BigInteger, default=0)

    # Averages
    avg_review_time_hours = Column(Float, nullable=True)
    avg_pr_merge_time_hours = Column(Float, nullable=True)

    # AI Insights
    strength_tags = Column(ARRAY(String), nullable=True)
    collaboration_score = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "github_username", name="uq_dev_org_username"),
    )
```

#### 9. TeamMetrics (DORA)
Métricas de time agregadas por período.

```python
class TeamMetrics(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "team_metrics"

    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    team_id = Column(UUID, ForeignKey("teams.id"), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # DORA Metrics
    deployment_frequency = Column(Float, nullable=True)
    lead_time_hours = Column(Float, nullable=True)
    change_failure_rate = Column(Float, nullable=True)
    mttr_hours = Column(Float, nullable=True)
    dora_level = Column(String(20), nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "team_id", "period_start", name="uq_team_metrics"),
    )
```

### Alterações em Entidades Existentes

#### Repository (adicionar FK para Organization)

```python
class Repository(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "repositories"

    # NEW: Tenant isolation
    organization_id = Column(Uuid, ForeignKey("organizations.id"), nullable=False, index=True)
    team_id = Column(Uuid, ForeignKey("teams.id"), nullable=True, index=True)

    name = Column(String, unique=False, index=True, nullable=False)  # Remove UNIQUE
    owner = Column(String, index=True, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_repo_org_name"),  # Unique per org
    )

    # Relationships
    organization = relationship("Organization", back_populates="repositories")
    team = relationship("Team", back_populates="repositories")
    activities = relationship("Activity", back_populates="repository", cascade="all, delete-orphan")
```

#### Activity (adicionar diff_content)

```python
class Activity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "activities"

    repository_id = Column(Uuid, ForeignKey("repositories.id"), nullable=False)
    external_id = Column(String, index=True, nullable=False)
    type = Column(Enum(ActivityType), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    author = Column(String, nullable=False)
    diff_content = Column(Text, nullable=True)  # NEW: Code diff for RAG

    # Relationships
    repository = relationship("Repository", back_populates="activities")
    business_update = relationship("BusinessUpdate", uselist=False, back_populates="activity")
```

#### BusinessUpdate (adicionar embedding_id)

```python
class BusinessUpdate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "business_updates"

    activity_id = Column(Uuid, ForeignKey("activities.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=False)
    impact_level = Column(Enum(ImpactLevel), default=ImpactLevel.LOW)
    category = Column(String, nullable=True)
    embedding_id = Column(String(100), nullable=True, index=True)  # NEW: Qdrant point ID

    # Relationships
    activity = relationship("Activity", back_populates="business_update")
```

## Regras de Isolamento (Row-Level Security)

### Padrão de Query

**TODAS** as queries de dados devem filtrar por `organization_id`:

```python
# ✅ CORRETO
async def get_repositories(db: AsyncSession, org_id: UUID) -> list[Repository]:
    query = select(Repository).where(Repository.organization_id == org_id)
    return (await db.execute(query)).scalars().all()

# ❌ INCORRETO - Vazamento de dados
async def get_repositories(db: AsyncSession) -> list[Repository]:
    query = select(Repository)  # Retorna repos de TODAS as orgs!
    return (await db.execute(query)).scalars().all()
```

### Middleware de Contexto

```python
from contextvars import ContextVar

current_org_id: ContextVar[UUID | None] = ContextVar("current_org_id", default=None)

# Middleware extrai org_id do JWT/session e injeta no contexto
async def org_context_middleware(request: Request, call_next):
    org_id = extract_org_id_from_token(request)
    token = current_org_id.set(org_id)
    try:
        return await call_next(request)
    finally:
        current_org_id.reset(token)
```

## Plano de Migração

### Fase 1: Adicionar Tabelas (Non-Breaking)

```sql
-- Migration: 001_add_organization_tables.py
CREATE TABLE organizations (...);
CREATE TABLE teams (...);
CREATE TABLE users (...);
CREATE TABLE memberships (...);
CREATE TABLE organization_settings (...);
```

### Fase 2: Adicionar FKs como Nullable

```sql
-- Migration: 002_add_org_fk_to_repositories.py
ALTER TABLE repositories ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE repositories ADD COLUMN team_id UUID REFERENCES teams(id);
```

### Fase 3: Backfill (Script de Migração de Dados)

```python
# Script: backfill_org_for_existing_repos.py
# Cria uma "Default Organization" e associa todos os repos existentes
default_org = Organization(name="Default", slug="default")
db.add(default_org)

await db.execute(
    update(Repository).values(organization_id=default_org.id)
)
```

### Fase 4: Tornar FK NOT NULL

```sql
-- Migration: 003_make_org_id_not_null.py
ALTER TABLE repositories ALTER COLUMN organization_id SET NOT NULL;
```

## Consequências

### Positivas

- ✅ **Isolamento garantido**: Dados de uma org nunca vazam para outra
- ✅ **Escalável**: Suporta orgs com múltiplos times
- ✅ **Preparado para billing**: `plan` na org permite precificação
- ✅ **RBAC flexível**: Roles por org e por team

### Negativas

- ❌ **Complexidade**: Toda query precisa de `organization_id`
- ❌ **Migration risk**: Backfill de dados existentes requer cuidado
- ❌ **Index overhead**: Mais índices = mais storage

### Mitigações

1. **Middleware obrigatório** garante injection de `org_id`
2. **Testes de integração** verificam isolamento
3. **PostgreSQL RLS** (Row-Level Security) como camada extra

## Referências

- [ADR-005: Product Strategy](./005-product-strategy.md)
- [Multi-Tenancy Patterns](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/)
- [SQLAlchemy Multi-Tenancy](https://docs.sqlalchemy.org/en/20/orm/extensions/horizontal_shard.html)
