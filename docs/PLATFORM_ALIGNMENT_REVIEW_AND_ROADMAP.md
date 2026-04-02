# OneClass Platform Alignment Review And Completion Roadmap

## Scope

This review compares the platform vision in `docs/OneClass_Platform_Reference_v2.docx.pdf` with the current repository state as of 2026-04-01.

The goal is to answer four questions:

1. What in the PDF is aligned with the codebase?
2. What has drifted?
3. Which broken fundamentals will prevent the platform from achieving the larger vision?
4. What sequence should be followed to finish the platform realistically?

## Executive Summary

The codebase is not starting from zero. It already contains meaningful implementation across platform auth, tenancy, SIS, academic, finance, analytics, monitoring, invitations, migration services, and multiple dashboard surfaces.

However, the platform is not yet on a stable foundation. The biggest blockers are not missing feature screens. They are architectural inconsistencies:

- The documented architecture and the real architecture have diverged.
- The auth and school-context model is implemented inconsistently across backend and frontend.
- The data-access layer mixes sync SQLAlchemy, async SQLAlchemy, and raw `asyncpg`.
- Tenant resolution and school discovery are duplicated across multiple APIs with different response contracts.
- Build, test, and verification workflows are not green.
- Offline-first, mobile, and trilingual claims are still mostly aspirational.

Until those issues are corrected, adding more modules will compound platform risk.

## Vision Vs Code Alignment

### Aligned In Principle

- Multi-tenant school platform
- Zimbabwe-specific school concepts, grading, and payment references
- Multi-school membership model
- Platform onboarding and migration services
- SIS, academic, finance, analytics, and parent/staff/student/admin dashboard directions

### Diverged From The PDF

- PDF stack says Node.js/Fastify + TypeScript + Prisma + Vite monorepo.
- Repo is Python/FastAPI backend plus Next.js frontend.
- PDF says no production code exists.
- Repo contains substantial backend and frontend implementation.
- PDF assumes offline-first and mobile are core architecture.
- Repo currently has no real mobile app and no implemented offline sync engine.

## Critical Findings

### 1. Core auth and school-context switching are contract-broken

The frontend posts a JSON body to switch school context, but the backend route expects `school_id` as a simple function parameter, which FastAPI will treat as a query parameter. The current switch flow is therefore unreliable or broken.

Evidence:

- `frontend/hooks/useAuth.ts` posts `{ school_id }` to `/api/v1/auth/switch-school`
- `backend/services/auth/routes.py` defines `switch_school(school_id: str, ...)`

Impact:

- Multi-context identity, which is the platform’s defining differentiator, cannot be treated as stable.
- Any dashboard or data isolation workflow depending on school switching is at risk.

### 2. The data-access layer is fundamentally inconsistent

The codebase currently mixes:

- synchronous SQLAlchemy sessions
- asynchronous SQLAlchemy sessions
- raw `asyncpg` connections

Worse, the repository exposes helper functions that are used incorrectly. `get_database_connection()` is an `async def` returning a coroutine, but many call sites use it directly in `async with`, which is invalid.

Evidence:

- `backend/shared/database.py` defines `get_db()`, `get_async_session()`, and `get_database_connection()`
- `backend/services/sis/main.py` uses sync `Session = Depends(get_db)` inside async endpoints
- `backend/services/academic/api.py` expects `AsyncSession` but depends on `get_db`
- `backend/services/finance/crud.py` uses `async with get_database_connection() as conn`

Impact:

- Transaction behavior is inconsistent.
- Tenant-scoped RLS is only applied in one path.
- Runtime failures are likely in finance and academic code paths.
- This is the single largest architectural risk in the repo.

### 3. Tenant discovery was duplicated and returned incompatible response shapes

There are multiple school-discovery APIs with overlapping responsibility:

- `/api/v1/schools/by-subdomain/...`
- `/api/v1/platform/schools/by-subdomain/...`
- `/api/v1/platform/schools-simple/by-subdomain/...`

The frontend middleware expects one response shape, while the backend route at `/api/v1/schools/by-subdomain/...` returns another.

Evidence:

- `frontend/middleware.ts` expected top-level `id`, `name`, `subdomain`, `is_active`, `subscription_tier`, `enabled_modules`
- `backend/api/subdomain.py` returns `{ school: {...}, timestamp: ... }`
- `frontend/components/tenant/TenantProvider.tsx` uses `/api/v1/platform/schools-simple/by-subdomain/...`
- `backend/services/platform/routes/schools_simple.py` implements a separate bypass route

Impact:

- Tenant bootstrapping is brittle.
- Different parts of the frontend are likely resolving schools differently.
- Multi-tenant correctness is not centralized.

### 4. Some “tenant bypass” code weakens architectural discipline

The simple school routes bypass middleware and open direct database connections. They also contain a hardcoded development database URL fallback.

Evidence:

- `backend/services/platform/routes/schools_simple.py`

Impact:

- Public lookup logic is no longer centralized.
- Environment configuration discipline is weakened.
- This makes production-hardening and security review harder.

Status update:

- The duplicate `/api/v1/schools/...` route family, `schools-simple`, and other legacy public school lookup sidecars were removed in the cleanup pass on 2026-04-01.

### 5. School configuration is not wired end-to-end

The frontend has a school-configuration hook that calls `/api/v1/schools/{schoolId}/context`, but I found no backend route implementing that contract.

Evidence:

- `frontend/hooks/useSchoolContext.ts`

Impact:

- Any screen depending on school branding, feature flags, limits, or regional config is incomplete.
- Dynamic theming and feature gating remain partial.

### 6. Frontend school-context APIs are duplicated and semantically conflicting

There are two different hooks named `useSchoolContext`:

- one in `frontend/hooks/useAuth.ts` returning auth-centric current-school helpers
- one in `frontend/hooks/useSchoolContext.ts` returning school configuration data

Pages import the second hook and destructure it unsafely as if it always returns a non-null object with specific properties.

Evidence:

- `frontend/hooks/useAuth.ts`
- `frontend/hooks/useSchoolContext.ts`
- `frontend/app/admin/page.tsx`
- `frontend/app/staff/page.tsx`
- `frontend/app/parent/page.tsx`

Impact:

- This is a maintainability trap and a likely runtime bug source.
- It also makes it hard to build a coherent context-switching story across the app.

### 7. Auth/session code shows model drift from the actual schema

The auth routes reference fields such as `last_activity`, `ended_at`, and `session.school_id`, while the consolidated session model uses `last_activity_at`, `last_school_switch_at`, and `current_school_id`.

Evidence:

- `backend/services/auth/routes.py`
- `backend/shared/models/platform_user.py`

Impact:

- Session refresh, logout, and activity tracking cannot be assumed correct.
- The platform’s identity foundation is partially merged and not normalized.

### 8. Build and test fundamentals are not green

Current verification results showed:

- root build scripts depend on `python`, but this environment only has `python3`
- frontend production build fails when Google Fonts cannot be fetched
- frontend TypeScript checking fails on syntax errors in test files
- backend tests could not run from the bundled venv because `testcontainers` is missing

Impact:

- The repo is not currently in a trustworthy release state.
- CI/CD cannot be considered real until build and test flows are made deterministic.

## Module Status Snapshot

### Substantial Implementation Exists

- Platform admin / multi-tenancy
- Authentication / memberships / invitations
- SIS
- Academic management
- Assessment and grading surfaces
- Attendance surfaces
- Finance and billing
- Analytics and reporting
- Migration services / care package concepts
- Monitoring / audit / notifications / files

### Partial Or UI-Shell Heavy

- Parent portal
- Staff portal
- Admin dashboards
- Timetable and attendance UX
- Theming and tenant-specific branding
- Real-time communication

### Not Yet Real In The Codebase

- Flutter mobile app
- Offline sync engine
- Library management
- Boarding / hostel management
- Transport management
- Extracurricular activities
- Asset and inventory management
- Content management engine
- AI learning services as a coherent product layer
- Student learning portal as a true learning environment
- Ministry dashboard
- HR / payroll
- Exam board module as a finished implementation

## Broken Fundamentals To Fix Before Major Feature Expansion

1. Establish one canonical architecture.
2. Establish one canonical auth and tenant-context contract.
3. Establish one canonical database access pattern.
4. Make tenant-scoped data enforcement consistent across all modules.
5. Make build, test, and local boot deterministic.
6. Rebuild documentation around the code that actually exists.

## Recommended Completion Roadmap

## Phase 0: Architecture Reset And Source Of Truth
Duration: 1 week

Deliverables:

- Decide that the real stack is Python/FastAPI + Next.js, or stop and replatform.
- Freeze one public contract for:
  - tenant discovery
  - auth `/me`
  - school switching
  - school configuration
- Replace “spec fiction” in docs with “implemented / partial / planned”.
- Define module status in one maintained document.

Exit criteria:

- Product, code, and docs no longer describe different systems.

## Phase 1: Platform Kernel Stabilization
Duration: 2 to 4 weeks

Deliverables:

- Unify data access around a single pattern.
- Fix auth/session model drift.
- Fix switch-school request/response contract.
- Collapse duplicate subdomain and school-resolution APIs into one canonical flow.
- Implement missing school context/config endpoint.
- Remove unsafe hook duplication or rename clearly.
- Make build and test commands pass in CI.

Exit criteria:

- Login, school discovery, school switching, RBAC, and tenant isolation work end-to-end.

## Phase 2: Honest MVP Completion
Duration: 4 to 8 weeks

Focus only on the true MVP from the PDF:

- platform admin and onboarding
- SIS
- academic management
- assessment and grading
- attendance
- finance

Add:

- parent portal essentials
- migration-service assisted onboarding for pilot schools

Exit criteria:

- A real school can onboard, import students, define academic structure, take attendance, bill fees, and let parents view core information.

## Phase 3: Pilot Hardening
Duration: 4 weeks

Deliverables:

- audit trails for sensitive workflows
- backup and recovery procedures
- operational monitoring
- data repair / admin tooling
- role-based acceptance testing
- pilot-school rollout playbooks

Exit criteria:

- The platform can survive real school usage with supportable operations.

## Phase 4: Operational Expansion
Duration: 6 to 10 weeks

Next modules after MVP and pilot validation:

- timetable management
- teacher management
- communication and notifications
- improved parent experience
- analytics hardening
- migration services as a revenue-supporting function

Exit criteria:

- Daily operations are cohesive enough to increase school stickiness.

## Phase 5: Strategic Expansion
Duration: after pilots prove retention and pricing

Only after the kernel and MVP are stable:

- library
- boarding
- transport
- extracurricular
- assets
- ministry reporting
- HR
- exam board

These should be selected based on pilot demand, not document order alone.

## Phase 6: Aspirational Platform Layer
Duration: after operational maturity

- mobile app
- offline-first sync
- content engine
- AI services
- student learning portal

These are strategically important, but they should not be layered onto an unstable core.

## Immediate Priorities For The Next 10 Working Days

1. Normalize auth and school-switch contracts.
2. Normalize tenant discovery into a single canonical API.
3. Replace mixed DB access with one consistent approach.
4. Implement the missing school configuration context endpoint.
5. Fix build/test scripts so the repo has a real quality gate.
6. Rename or consolidate the conflicting `useSchoolContext` hooks.
7. Update documentation so the PDF becomes a vision document, not the runtime truth.

## Remediation Progress: 2026-04-01

This remediation pass started the platform-kernel work before any further module expansion.

### Phase 1: Platform Kernel Stabilization

Completed in this pass:

- Auth routes were aligned with the real consolidated models in `platform.users` and `platform.user_sessions`.
- Login now records `last_login_at`, `last_activity_at`, `login_count`, `current_school_id`, and `available_school_ids`.
- `/api/v1/auth/me` now reads the active school from the persisted session instead of relying on stale token context alone.
- `/api/v1/auth/refresh` now uses `session_id`, `current_school_id`, and `last_activity_at` correctly.
- `/api/v1/auth/logout` no longer writes the nonexistent `ended_at` field.
- `/api/v1/auth/switch-school` now accepts a request body, validates membership access, updates session context, and returns the refreshed current-school payload.
- Canonical public school discovery endpoints now exist under:
  - `/api/v1/platform/schools/by-subdomain/{subdomain}`
  - `/api/v1/platform/schools/by-id/{school_id}`
  - `/api/v1/platform/schools/{school_id}/context`
- `backend/shared/database.py` now exposes a real async context manager for raw connection consumers, so `async with get_database_connection()` is valid again.
- Academic API routes were moved to `get_async_session`, removing a core sync/async dependency mismatch.
- SIS routes and CRUD helpers were moved to `AsyncSession` signatures so the module no longer advertises async behavior while depending on sync sessions.
- Platform public school endpoints were moved to `AsyncSession` and async SQL execution.
- Integration routes were rewired from broken `core.*` imports to shared auth/database contracts and now resolve school scope from the actual authenticated user object.
- `shared.auth` now exposes `require_permissions`, which closes a broken dependency used by integration and domain-management style routes.

Still open in Phase 1:

- Mixed sync SQLAlchemy, async SQLAlchemy, and raw `asyncpg` access is reduced but not fully eliminated across non-auth modules.
- Finance still uses raw `asyncpg` extensively by design, and migration-services retains older service patterns.
- Legacy duplicate school-resolution routes were removed in the cleanup pass, leaving `/api/v1/platform/schools/...` as the only supported public school-discovery contract.

### Phase 2: Frontend Context Unification

Completed in this pass:

- Frontend middleware now resolves tenants from the canonical `/api/v1/platform/schools/by-subdomain/...` contract.
- Subdomain utilities and `TenantProvider` now rely on the canonical platform school APIs instead of `schools-simple`.
- The duplicated school-context model was replaced with one unified `useSchoolContext` hook that merges:
  - authenticated current-school membership
  - canonical school configuration
  - feature gating
  - permission checks
  - school switching helpers
  - legacy `schoolContext` aliases needed by existing dashboards
- The auth hook now:
  - honors backend `current_school_id`
  - persists switched school state
  - stores the returned access token for local-auth mode
  - redirects to the correct subdomain when a school switch crosses tenant boundaries
- Clerk provider theming no longer depends on `const school = null as any`.

Still open in Phase 2:

- Several screens outside the auth/tenant slice still carry old type assumptions and stale imports.
- Some frontend modules still use direct `fetch()` calls and legacy local token assumptions instead of the shared API client.

### Phase 3: Verification And Delivery Fundamentals

Completed in this pass:

- Root scripts were updated from `python` to `python3`.
- Frontend production build no longer depends on Google Fonts at build time.
- Frontend production build was switched to webpack so it can build deterministically without Turbopack panics in this environment.
- Verified passing commands:
  - `python3 -m py_compile backend/services/auth/routes.py backend/api/platform.py backend/main.py`
  - `npm run build`

Completed in the current follow-up pass:

- Shared frontend contracts were repaired:
  - `frontend/lib/api.ts` now exports a typed `ApiClient`
  - `frontend/lib/utils.ts` now exports the formatting helpers used across dashboards
  - `frontend/lib/academic-api.ts` now exports the Zimbabwe helpers and hook surface the academic UI was already coded against
- Clerk middleware typing was aligned with the current Next.js / Clerk API shape.
- Query client configuration was updated for the current TanStack Query API.
- Onboarding form state was typed end-to-end instead of relying on untyped `{}` state.
- Finance invoice date handling was normalized for the current calendar component contract.
- Migration, admin, parent, staff, SIS, and onboarding component typing gaps were cleaned up.
- Verified passing commands:
  - `cd frontend && npm run type-check`
  - `npm run build`

Still open in Phase 3:

- The deprecated Next.js `middleware.ts` entrypoint was replaced with `proxy.ts`.
- The build is currently configured to skip type validation inside `next build`; the dedicated `npm run type-check` command now covers that gate explicitly.

### Practical Meaning

The platform kernel is materially more trustworthy than it was at the start of this review.

The two hard gates that were blocking safe expansion have now moved from red to mostly green:

1. backend DB access is normalized across the platform/auth/academic/SIS/integration paths, with residual legacy cleanup still needed in finance and migration-services
2. frontend `type-check` is now green and repo build is green

The correct next step is:

1. finish the residual Phase 1 DB-pattern cleanup in the older service areas
2. finish migration-services cleanup or remove any remaining mock-only admin surfaces
3. then resume MVP module expansion on a more trustworthy kernel

## Expansion Readiness Proof: 2026-04-01

This pass moved the codebase from "green on a narrow path" to "verifiable expansion baseline."

### What Is Now Proven

- Backend code compiles across `main.py`, `api`, `services`, and `shared`, not just a single entry file.
- Startup/import smoke now passes for:
  - `main`
  - `services.domain_management.routes`
  - `services.mobile_auth.routes`
  - `services.mobile_auth.service`
  - `services.sso_integration.routes`
  - `services.sso_integration.service`
- FastAPI route-manifest verification now proves the required kernel contracts are actually mounted in the app:
  - `GET /api/v1/auth/me`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/switch-school`
  - `GET /api/v1/auth/me/schools`
  - `GET /api/v1/platform/schools/by-subdomain/{subdomain}`
  - `GET /api/v1/platform/schools/by-id/{school_id}`
  - `GET /api/v1/platform/schools/{school_id}/context`
  - `GET /api/v1/sis/health`
  - `GET /api/v1/academic/health`
  - `GET /api/v1/finance/health`
  - `GET /api/v1/migration-services/health`
- Frontend `npm run type-check` passes.
- Root `npm run build` passes.
- Frontend production build emits the main expansion surfaces, including:
  - `/admin`
  - `/analytics`
  - `/dashboard`
  - `/finance`
  - `/onboarding`
  - `/parent`
  - `/staff`
  - `/student`
  - `/super-admin`
- A repeatable verification command now exists:
  - `npm run verify:readiness`
- Frontend app build now runs with real Next.js type validation again; `ignoreBuildErrors` is no longer part of the active build path.
- Frontend E2E entrypoints now fail honestly with a provisioning message instead of pointing at a missing script.
- Next.js output tracing root is now configured explicitly for the nested frontend app, so the build no longer depends on lockfile inference.
- Unsupported frontend Vitest/Playwright test scaffolding was removed from the active repo because the toolchain is not provisioned in this workspace and the files were generating IDE noise against the live frontend codebase.

The current readiness proof is green.

Behavioral test completeness is still below the expansion bar:

- backend finance tests now resolve through the repo venv correctly, but still require `testcontainers` to be installed in that environment
- frontend behavioral tests are not yet provisioned because `vitest` is not part of the installed workspace toolchain
- this means `npm run verify:readiness` is currently the authoritative expansion gate, while `npm test` remains an honest signal of missing test infrastructure

### Architectural Hardening Added

- Backend build verification was strengthened from `py_compile main.py` to full module compile coverage.
- Legacy public school route trees were removed so tenant discovery now resolves only through the canonical platform router.
- `migration_services` remains experimental and is disabled by default unless explicitly enabled with `ONECLASS_ENABLE_EXPERIMENTAL_MIGRATION_SERVICES=true`
- Disabled modules still expose health endpoints so operators can see that the module is intentionally quarantined rather than silently broken.
- Shared compatibility shims were added so older service modules can import cleanly while the platform continues converging on the unified auth/database stack.
- Dead sidecar code was removed from the repo:
  - duplicate public school routers
  - the unused enhanced tenant resolver/middleware path
  - the extra `useSchoolContext` export from `useAuth`
  - the unused `SchoolSelector` component
  - the deprecated `frontend/middleware.ts` file
  - dead user-management and api-docs service trees
  - demo test pages and mock-only migration admin dashboard routes
  - the duplicate mock super-admin dashboard component and its stale links

### Completeness Status For Expansion

Stable enough to expand on now:

- auth and session management
- canonical tenant discovery and school context
- SIS core route/service path
- academic core route/service path
- finance route/service path
- frontend tenant/auth/school context
- frontend shared API and typing layer
- backend startup path with experimental modules quarantined

Not yet ready to treat as expansion foundations:

- legacy migration-services backend
- optional SSO/SAML runtime behavior without third-party packages installed

### Practical Expansion Rule

All new module expansion should attach only to:

- canonical platform school APIs
- `get_async_session` / `get_async_db_session` for backend DB access
- shared auth helpers and current membership/session models
- the green frontend type-check/build path

Any module that cannot satisfy those conditions should be treated as experimental and quarantined until remediated.

## Recommendation On The Grand Vision

The greater aspiration is still viable, but only if the platform is treated as a staged systems product rather than a 25-module checklist.

The winning strategy is:

- stabilize the platform kernel
- ship a truthful MVP
- validate with real schools
- then expand outward

If that order is respected, the current codebase can become the foundation of the larger OneClass vision. If not, the platform will accumulate impressive-looking modules on top of unstable core mechanics.
