# 5. Product Strategy & Deployment Model

Date: 2026-01-03

## Status

Accepted

## Context

DevBridge solves the problem of "invisible technical work" for stakeholders. To scale this solution effectively, we need to decide on a deployment model that balances ease of adoption with the ability to serve enterprise customers with strict compliance requirements.

Key questions:
1.  **Deployment Model:** Single-tenant (Self-hosted) vs Multi-tenant (SaaS).
2.  **Data Hierarchy:** How to structure data to support growth (Org, Team, Repo).
3.  **Authentication:** How to handle user access and permissions securely across stages of growth.

## Decision

We have decided to adopt a **Multi-tenant SaaS First** approach, while architecting the system to support a potential Open-Core/Self-hosted model in the future.

### 1. Deployment Model
-   **Primary:** Multi-tenant SaaS (Cloud). This allows for faster iteration, simpler onboarding for small/medium teams, and a scalable business model (PLG).
-   **Future-proof:** The architecture will enforce strict tenant isolation, making it possible to package the application for Single-tenant (Self-hosted) deployment for Enterprise clients if needed.

### 2. Data Hierarchy
We will implement a standard B2B three-level hierarchy:

1.  **Organization (Tenant):** The billing unit and security boundary. Data is strictly isolated here.
2.  **Team:** Functional groups within an organization (e.g., "Backend", "Mobile"). Used for managing permissions and grouping repositories.
3.  **Repository:** The unit of work. Contains Activities, Code Diffs, and Business Translations.

### 3. Authentication & Persona-based UX
-   **Phased Auth:**
    -   Phase 1: Magic Link (frictionless onboarding).
    -   Phase 2: OAuth (GitHub/Google).
    -   Phase 3: SSO/SAML (Enterprise).
-   **Persona Views:** The AI response generation will be context-aware, adapting the depth and tone based on the user's role (Executive vs. Technical).

## Consequences

### Positive
-   **Speed:** Focused on one deployment artifact initially.
-   **Adoption:** Lower barrier to entry for users (no installation required).
-   **Architecture:** Enforcing Organization-level isolation early prevents technical debt related to multi-tenancy.

### Negative
-   **Complexity:** Multi-tenancy requires rigorous security logic to prevent data leaks between organizations.
-   **Trust:** SaaS requires users to trust us with their code metadata (mitigated by SOC 2 compliance in roadmap).
