# OneClass Platform Architecture

## 🏗️ System Architecture Overview

The OneClass Platform is built on a modern, scalable, multi-tenant architecture designed to serve educational institutions across Zimbabwe. This document provides a comprehensive overview of the system architecture, design patterns, and architectural decisions.

## 🎯 Architecture Goals

### Primary Objectives
1. **Multi-tenancy**: Isolated school environments with shared infrastructure
2. **Scalability**: Horizontal scaling to support growing user base
3. **Security**: Zero-trust architecture with comprehensive security controls
4. **Performance**: Sub-200ms API response times with 99.9% uptime
5. **Maintainability**: Clean, modular code with comprehensive documentation

### Non-Functional Requirements
- **Availability**: 99.9% uptime SLA
- **Performance**: <200ms API response time (95th percentile)
- **Scalability**: Support 10,000+ concurrent users
- **Security**: SOC 2 Type II compliance ready
- **Reliability**: Zero data loss, automatic failover

## 🌐 High-Level Architecture

```
                                    ┌─────────────────┐
                                    │   Load Balancer │
                                    │   (Nginx/HAProxy)│
                                    └─────────┬───────┘
                                              │
                            ┌─────────────────┼─────────────────┐
                            │                 │                 │
                    ┌───────▼────────┐ ┌──────▼──────┐ ┌──────▼──────┐
                    │  Frontend      │ │  API Gateway│ │  Admin Panel│
                    │  (Next.js)     │ │  (FastAPI)  │ │  (React)    │
                    └───────┬────────┘ └──────┬──────┘ └──────┬──────┘
                            │                 │                 │
                    ┌───────▼────────┐ ┌──────▼──────┐ ┌──────▼──────┐
                    │  CDN           │ │  Auth Service│ │  Monitoring │
                    │  (CloudFlare)  │ │  (Clerk)     │ │  (Grafana)  │
                    └────────────────┘ └──────┬──────┘ └─────────────┘
                                              │
                            ┌─────────────────┼─────────────────┐
                            │                 │                 │
                    ┌───────▼────────┐ ┌──────▼──────┐ ┌──────▼──────┐
                    │  Core Services │ │  Background │ │  File Storage│
                    │  (FastAPI)     │ │  Jobs       │ │  (S3/MinIO)  │
                    └───────┬────────┘ │  (Celery)   │ └─────────────┘
                            │          └──────┬──────┘
                    ┌───────▼────────┐ ┌──────▼──────┐
                    │  Database      │ │  Cache      │
                    │  (PostgreSQL)  │ │  (Redis)    │
                    └────────────────┘ └─────────────┘
```

## 🔧 Technology Stack

### Backend Services
- **API Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with Row Level Security
- **Authentication**: Clerk with custom multi-tenant routing
- **Caching**: Redis 7+ for sessions and application cache
- **Message Queue**: Celery with Redis broker
- **Background Jobs**: Celery workers for async processing

### Frontend Applications
- **Web Application**: Next.js 14+ with App Router
- **Admin Panel**: React 18+ with TypeScript
- **Mobile API**: RESTful APIs with mobile-specific endpoints
- **UI Components**: shadcn/ui with Tailwind CSS
- **State Management**: React Context with custom hooks

### Infrastructure & DevOps
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes with Helm charts
- **CI/CD**: GitHub Actions with automated testing
- **Monitoring**: Prometheus + Grafana + custom observability
- **Logging**: Structured logging with ELK stack
- **File Storage**: S3-compatible object storage

## 🏢 Multi-Tenant Architecture

### Tenant Isolation Strategy
The platform uses a **hybrid multi-tenancy** approach combining:

1. **Database Level**: Row Level Security (RLS) for data isolation
2. **Application Level**: Tenant context propagation
3. **Network Level**: Subdomain-based routing
4. **Resource Level**: Tenant-specific resource allocation

### Tenant Resolution Flow
```
Request: https://harare-primary.oneclass.ac.zw/api/v1/students
    │
    ├── DNS Resolution → Load Balancer
    │
    ├── Subdomain Extraction → "harare-primary"
    │
    ├── Tenant Lookup → Database query
    │
    ├── Context Injection → Request.state.tenant
    │
    └── RLS Enforcement → Filtered queries
```

### Data Isolation Mechanisms

#### 1. Row Level Security (RLS)
```sql
-- Enable RLS on all tenant tables
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY tenant_isolation_policy ON students
    FOR ALL USING (school_id = current_setting('app.current_school_id')::UUID);
```

#### 2. Application Context
```python
# Tenant context middleware
async def tenant_context_middleware(request: Request, call_next):
    subdomain = extract_subdomain(request.url.host)
    tenant = await get_tenant_by_subdomain(subdomain)
    request.state.tenant = tenant
    request.state.school_id = tenant.school_id
    
    # Set database context
    async with get_db_session() as session:
        await session.execute(
            text("SET app.current_school_id = :school_id"),
            {"school_id": str(tenant.school_id)}
        )
```

#### 3. API Route Protection
```python
@router.get("/students")
async def get_students(
    request: Request,
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(get_current_tenant)
):
    # All queries automatically filtered by RLS
    return await get_students_for_school(tenant.school_id)
```

## 🔐 Security Architecture

### Zero Trust Principles
1. **Never Trust, Always Verify**: Every request is authenticated and authorized
2. **Least Privilege Access**: Minimal permissions for each role
3. **Micro-segmentation**: Network and application-level isolation
4. **Continuous Monitoring**: Real-time threat detection

### Authentication Flow
```
User Login → Clerk Authentication → JWT Token → API Gateway → Service Authorization
    │              │                    │            │              │
    │              │                    │            │              └── Role Check
    │              │                    │            └── Tenant Validation
    │              │                    └── Token Verification
    │              └── MFA (if enabled)
    └── Device Registration (mobile)
```

### Authorization Model
```python
class RoleHierarchy:
    SUPER_ADMIN = "super_admin"      # Platform level
    SCHOOL_ADMIN = "school_admin"    # School level
    TEACHER = "teacher"              # Class level
    STUDENT = "student"              # Individual level
    PARENT = "parent"                # Child level
    STAFF = "staff"                  # Department level

class PermissionMatrix:
    ROLES_PERMISSIONS = {
        SUPER_ADMIN: ["*"],  # All permissions
        SCHOOL_ADMIN: ["school.*", "users.*", "reports.*"],
        TEACHER: ["classes.*", "students.read", "grades.*"],
        STUDENT: ["profile.*", "grades.read", "attendance.read"],
        PARENT: ["child.read", "fees.read", "communication.read"],
        STAFF: ["department.*", "reports.read"]
    }
```

## 💾 Database Architecture

### Schema Design Principles
1. **Normalization**: 3NF normalized tables for data integrity
2. **Indexing**: Strategic indexing for query performance
3. **Partitioning**: Time-based partitioning for large tables
4. **Archiving**: Automated data archiving for compliance

### Core Database Schema
```sql
-- Tenant management
CREATE TABLE schools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    domain VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User management with tenant isolation
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    email VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(school_id, email)
);

-- Enable RLS on all tenant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON users
    FOR ALL USING (school_id = current_setting('app.current_school_id')::UUID);
```

### Database Performance Optimization
1. **Query Optimization**: Explain plans and index tuning
2. **Connection Pooling**: PgBouncer for connection management
3. **Read Replicas**: Separate read and write workloads
4. **Caching Strategy**: Multi-level caching architecture

## 📊 Caching Strategy

### Multi-Level Cache Architecture
```
Application Cache (Redis)
    ├── Session Cache (30 min TTL)
    ├── User Profile Cache (1 hour TTL)
    ├── School Config Cache (24 hour TTL)
    └── Query Result Cache (15 min TTL)

Database Cache (PostgreSQL)
    ├── Shared Buffers (25% of RAM)
    ├── Query Plan Cache
    └── Index Cache

CDN Cache (CloudFlare)
    ├── Static Assets (1 year TTL)
    ├── API Responses (5 min TTL)
    └── Images (1 month TTL)
```

### Cache Invalidation Strategy
```python
class CacheManager:
    async def invalidate_user_cache(self, user_id: str):
        await self.redis.delete(f"user:{user_id}")
        await self.redis.delete(f"user_permissions:{user_id}")
    
    async def invalidate_school_cache(self, school_id: str):
        pattern = f"school:{school_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

## 🔄 API Architecture

### RESTful API Design
```
Base URL: https://api.oneclass.ac.zw/api/v1
Authentication: Bearer Token (JWT)
Content-Type: application/json

Endpoints:
├── /auth/
│   ├── POST /login
│   ├── POST /logout
│   └── POST /refresh
├── /schools/
│   ├── GET /schools
│   ├── POST /schools
│   └── GET /schools/{id}
├── /users/
│   ├── GET /users
│   ├── POST /users
│   └── GET /users/{id}
└── /students/
    ├── GET /students
    ├── POST /students
    └── GET /students/{id}
```

### API Response Format
```json
{
    "success": true,
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "John Doe",
        "email": "john@harare-primary.oneclass.ac.zw"
    },
    "meta": {
        "total": 1,
        "page": 1,
        "per_page": 10
    },
    "timestamp": "2024-01-18T10:30:00Z"
}
```

### Error Handling
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": {
            "field": "email",
            "issue": "Invalid email format"
        }
    },
    "timestamp": "2024-01-18T10:30:00Z",
    "request_id": "req_123456789"
}
```

## 🚀 Performance Architecture

### Performance Targets
- **API Response Time**: <200ms (95th percentile)
- **Database Query Time**: <100ms (95th percentile)
- **Frontend Load Time**: <3s (initial load)
- **Concurrent Users**: 10,000+ simultaneous users

### Optimization Strategies
1. **Database Optimization**
   - Index optimization for common queries
   - Query result caching
   - Connection pooling
   - Read replicas for read-heavy workloads

2. **Application Optimization**
   - Async/await for non-blocking operations
   - Background job processing
   - API response caching
   - Lazy loading for large datasets

3. **Frontend Optimization**
   - Code splitting and lazy loading
   - Image optimization and CDN
   - Progressive loading
   - Service worker caching

## 📈 Monitoring Architecture

### Observability Stack
```
Metrics Collection (Prometheus)
    ├── Application Metrics
    ├── System Metrics
    ├── Database Metrics
    └── Custom Business Metrics

Monitoring Dashboard (Grafana)
    ├── System Health Dashboard
    ├── Application Performance Dashboard
    ├── Business Metrics Dashboard
    └── Alert Manager Dashboard

Logging (ELK Stack)
    ├── Application Logs
    ├── Access Logs
    ├── Error Logs
    └── Audit Logs

Distributed Tracing (Jaeger)
    ├── Request Tracing
    ├── Database Query Tracing
    ├── External Service Tracing
    └── Performance Profiling
```

### Health Checks
```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "checks": {
            "database": await check_database_health(),
            "cache": await check_cache_health(),
            "external_services": await check_external_services()
        }
    }
```

## 🛡️ Disaster Recovery

### Backup Strategy
1. **Database Backups**: Daily full backups, continuous WAL archiving
2. **File Storage**: Cross-region replication
3. **Configuration**: Version-controlled infrastructure as code
4. **Monitoring**: Backup verification and alerting

### Recovery Procedures
1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour
3. **Automated Failover**: Database and application tier
4. **Manual Procedures**: Documented step-by-step recovery

## 📋 Architectural Decision Records (ADRs)

### ADR-001: Multi-Tenant Database Strategy
**Decision**: Use Row Level Security (RLS) with shared database
**Rationale**: Balance between isolation and cost efficiency
**Alternatives**: Separate databases per tenant, schema-based isolation

### ADR-002: Authentication Provider
**Decision**: Use Clerk for authentication management
**Rationale**: Reduces complexity, provides multi-tenant support
**Alternatives**: Custom auth, Auth0, Firebase Auth

### ADR-003: API Framework
**Decision**: Use FastAPI for backend services
**Rationale**: High performance, automatic API documentation, type safety
**Alternatives**: Django REST Framework, Flask, Express.js

### ADR-004: Frontend Framework
**Decision**: Use Next.js with App Router
**Rationale**: SSR/SSG support, excellent developer experience
**Alternatives**: React SPA, Vue.js, Angular

## 🔮 Future Architecture Considerations

### Scalability Roadmap
1. **Microservices**: Decompose monolith into domain services
2. **Event-Driven Architecture**: Implement event sourcing
3. **Global Distribution**: Multi-region deployment
4. **Edge Computing**: Move logic closer to users

### Technology Evolution
1. **Database**: Consider distributed databases (CockroachDB)
2. **Caching**: Implement distributed caching (Redis Cluster)
3. **Search**: Add full-text search capabilities (Elasticsearch)
4. **Analytics**: Real-time analytics pipeline (Apache Kafka)

---

**Last Updated**: 2024-01-18
**Version**: 1.0.0
**Status**: Production Ready
**Reviewed By**: Architecture Team