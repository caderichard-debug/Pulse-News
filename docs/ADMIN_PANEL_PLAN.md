# Admin Panel Implementation Plan

**Project**: Pulse News Aggregator
**Feature**: Comprehensive Admin Panel
**Created**: 2025-10-14
**Status**: Planning Phase → Ready for Implementation
**Current Phase**: Awaiting approval and decision on open questions

---

## 🚀 Quick Start for New Sessions

**If you're a new Claude session starting work on this feature, read this first:**

### What This Document Is
This is a complete implementation plan for building a production-ready admin panel for Pulse. The admin panel will allow authorized administrators to:
- Manage all database tables (view, edit, delete)
- Monitor and trigger background jobs
- View logs and system metrics
- Manage users and permissions
- Access audit trails

### Current Status
✅ **Planning Complete** - Full architectural design documented below
⏳ **Awaiting Decisions** - See [Section 12: Open Questions](#12-open-questions--decisions-needed)
⏳ **Ready to Implement** - Once approved, start with [Phase 1](#phase-1-database--backend-foundation-2-3-days)

### Key Files to Create/Modify

**Backend (Create New)**
- `backend/app/routes/admin_panel.py` - Main admin API routes
- `backend/app/utils/admin_auth.py` - Admin authentication middleware
- `backend/app/utils/logging_config.py` - Logging configuration
- `backend/scripts/create_admin.py` - Script to promote users to admin

**Backend (Modify)**
- `backend/app/models.py` - Add 3 new models (see [Section 3](#3-database-schema-changes))
- `backend/app/config.py` - Add admin settings (see [Section 4.4](#44-configuration-updates))
- `backend/app/main.py` - Register admin router
- `backend/app/jobs/tasks.py` - Add job execution tracking (see [Section 7.1](#71-job-execution-tracking))

**Frontend (Create New)**
- `frontend/src/app/admin/` - Entire admin section (see [Section 5.1](#51-admin-section-structure))
- `frontend/src/components/admin/` - Reusable admin components (see [Section 5.2](#52-admin-components))

**Frontend (Modify)**
- `frontend/src/lib/api.ts` - Add admin API methods (see [Section 5.3](#53-api-client-updates))
- `frontend/src/components/Navbar.tsx` - Add admin panel link (see [Section 5.5](#55-navbar-update))

### Implementation Order (Start Here!)
1. ⭐ **Start**: [Section 10 - Implementation Timeline](#10-implementation-timeline) - 8 phases with detailed checklists
2. 📊 **Phase 1 Steps**:
   - Read [Section 3 - Database Schema Changes](#3-database-schema-changes)
   - Copy models from [Appendix B.1](#b1-database-models-add-to-backendappmodelspy)
   - Copy config from [Appendix B.2](#b2-config-updates-add-to-backendappconfigpy)
   - Run migration commands from [Appendix B.7](#b7-migration-commands)
   - Create admin user with [Appendix B.8](#b8-create-first-admin-user)
3. 🔐 **Phase 2 Steps**:
   - Create auth middleware from [Appendix B.3](#b3-admin-authentication-middleware-backendapputilsadmin_authpy)
   - Read [Section 4 - Backend Implementation](#4-backend-implementation) for API design
   - Implement endpoints from [Section 4.2](#42-admin-api-routes-structure)
4. 🖥️ **Phase 4-5 Steps**:
   - Read [Section 5 - Frontend Implementation](#5-frontend-implementation)
   - Update API client from [Appendix B.5](#b5-frontend-api-client-updates-frontendsrclibapits)
   - Build UI components following [Section 5.1](#51-admin-section-structure)
5. 🧪 **Testing**: Use [Section 8](#8-testing-strategy) and [Appendix B.9](#b9-test-admin-endpoints)

### Decision Points Required
Before implementing, the user must answer questions in [Section 12](#12-open-questions--decisions-needed):
1. Admin token rotation policy
2. Database operation restrictions
3. Job scheduling permissions
4. UI color scheme preference
5. Audit log retention period

### Testing Requirements
- Backend: 50+ tests required (see [Section 8.1](#81-backend-tests))
- Frontend: 30+ tests required (see [Section 8.2](#82-frontend-tests))
- Integration: Full workflow tests (see [Section 8.3](#83-integration-tests))

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Database Schema Changes](#3-database-schema-changes) ⭐ **Start here for implementation**
4. [Backend Implementation](#4-backend-implementation) ⭐ **Core API design**
5. [Frontend Implementation](#5-frontend-implementation) ⭐ **UI structure**
6. [Security Considerations](#6-security-considerations)
7. [Logging & Monitoring](#7-logging--monitoring)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment Checklist](#9-deployment-checklist)
10. [Implementation Timeline](#10-implementation-timeline) ⭐ **8-phase roadmap**
11. [Future Enhancements](#11-future-enhancements)
12. [Open Questions & Decisions Needed](#12-open-questions--decisions-needed) ⚠️ **User input required**
13. [Success Criteria](#13-success-criteria)
14. [Risk Mitigation](#14-risk-mitigation)
15. [Recommended Architecture Decision](#15-recommended-architecture-decision)
16. [Next Steps](#16-next-steps)
17. [Appendix A: File Structure Summary](#appendix-a-file-structure-summary)
18. [Appendix B: Complete Code Templates](#appendix-b-complete-code-templates) ⭐ **Copy-paste ready**

---

## 1. Executive Summary

This document outlines the complete implementation plan for a production-ready admin panel for Pulse. The panel will provide comprehensive administrative controls for database management, job monitoring, user administration, and system diagnostics.

### Key Requirements
- ✅ View, edit, and delete data from production database
- ✅ Trigger background jobs and maintenance tasks
- ✅ Inspect logs, metrics, and system state
- ✅ Manage users, permissions, and API tokens
- ✅ Monitor integrations and job queues
- ✅ Secure admin authentication using environment token
- ✅ Full React/Next.js UI matching existing frontend
- ✅ Production deployment ready

---

## 2. Architecture Overview

### 2.1 Technology Stack

**Backend (FastAPI)**
- New admin routes in `/backend/app/routes/admin_panel.py`
- Admin authentication middleware
- Extended database models for job history tracking
- System monitoring utilities

**Frontend (Next.js/React)**
- New admin section: `/frontend/src/app/admin/`
- Protected admin routes with token validation
- Reusable admin components
- Real-time data updates for job monitoring

**Security**
- Environment-based admin token (`ADMIN_TOKEN` in `.env`)
- `is_admin` flag added to User model
- Middleware to validate admin access on all admin endpoints
- Frontend route protection for admin pages

### 2.2 Implementation Approach

Given your existing architecture, we'll follow this approach:

1. **Backend-First Development**: Build all API endpoints first
2. **Database Extensions**: Add job history and audit logging tables
3. **Frontend Integration**: Create admin UI matching your existing design patterns
4. **Security Hardening**: Implement token validation and access controls
5. **Testing**: Comprehensive tests for all admin operations
6. **Documentation**: API docs and user guide

---

## 3. Database Schema Changes

### 3.1 User Model Extension

**File**: `backend/app/models.py`

Add to existing `User` model:
```python
class User(SQLModel, table=True):
    # ... existing fields ...

    # New admin fields
    is_admin: bool = Field(default=False)
    admin_notes: Optional[str] = Field(default=None, max_length=1000)
    last_admin_action: Optional[datetime] = Field(default=None)
```

### 3.2 New Table: JobExecutionHistory

Track all background job executions for monitoring and debugging:

```python
class JobExecutionHistory(SQLModel, table=True):
    __tablename__ = "job_execution_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(max_length=100, index=True)  # e.g., 'scrape_rss'
    job_name: str = Field(max_length=200)

    # Execution details
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)

    # Status
    status: str = Field(max_length=20)  # success, failed, running
    result_data: Optional[str] = Field(default=None)  # JSON string of result
    error_message: Optional[str] = Field(default=None, max_length=2000)

    # Metrics
    items_processed: Optional[int] = Field(default=None)
    api_calls_made: Optional[int] = Field(default=None)
    tokens_used: Optional[int] = Field(default=None)

    # Trigger info
    triggered_by: str = Field(default="scheduler")  # scheduler, admin, api
    triggered_by_user_id: Optional[int] = Field(default=None)
```

### 3.3 New Table: AdminAuditLog

Track all admin actions for security and debugging:

```python
class AdminAuditLog(SQLModel, table=True):
    __tablename__ = "admin_audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(foreign_key="users.id", index=True)
    admin_email: str = Field(max_length=255, index=True)

    # Action details
    action_type: str = Field(max_length=100, index=True)  # e.g., 'delete_article', 'trigger_job'
    resource_type: str = Field(max_length=100)  # e.g., 'article', 'user', 'source'
    resource_id: Optional[str] = Field(default=None, max_length=100)

    # Change tracking
    old_value: Optional[str] = Field(default=None)  # JSON string
    new_value: Optional[str] = Field(default=None)  # JSON string

    # Metadata
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    notes: Optional[str] = Field(default=None, max_length=500)
```

### 3.4 Migration Plan

**Create migration:**
```bash
docker-compose exec backend alembic revision --autogenerate -m "add_admin_tables"
docker cp news_backend:/app/alembic/versions/[NEW_FILE].py backend/alembic/versions/
docker-compose exec backend alembic upgrade head
```

---

## 4. Backend Implementation

### 4.1 Admin Authentication Middleware

**File**: `backend/app/utils/admin_auth.py` (new file)

```python
"""
Admin authentication utilities.
Validates admin token and user permissions.
"""
from fastapi import HTTPException, status, Depends, Header
from typing import Optional
from ..config import settings
from .auth import get_current_user
from ..models import User

def verify_admin_token(x_admin_token: Optional[str] = Header(None)) -> bool:
    """
    Verify admin token from request headers.
    Raises HTTPException if invalid.
    """
    if not settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin token not configured"
        )

    if not x_admin_token or x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token"
        )

    return True

def get_admin_user(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(verify_admin_token)
) -> User:
    """
    Get current user and verify they have admin privileges.
    Requires both valid JWT token AND admin token.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user
```

### 4.2 Admin API Routes Structure

**File**: `backend/app/routes/admin_panel.py` (new file)

Route structure:
```
/admin-panel
  # Dashboard & Stats
  GET  /dashboard              # Overview stats and system health
  GET  /system-metrics         # CPU, memory, disk usage

  # Database Management
  GET    /database/tables      # List all tables with row counts
  GET    /database/{table}     # Get paginated data from table
  POST   /database/{table}     # Create new record
  PUT    /database/{table}/{id} # Update record
  DELETE /database/{table}/{id} # Delete record
  GET    /database/query       # Execute custom SELECT query (read-only)

  # Job Management
  GET    /jobs/history         # Job execution history with filters
  GET    /jobs/active          # Currently running jobs
  POST   /jobs/trigger/{job_id} # Trigger specific job
  POST   /jobs/cancel/{job_id}  # Cancel running job
  GET    /jobs/schedule        # Current schedule configuration
  PUT    /jobs/schedule/{job_id} # Update job schedule

  # User Management
  GET    /users               # List all users with filters
  GET    /users/{id}          # Get user details
  PUT    /users/{id}          # Update user (including is_admin flag)
  DELETE /users/{id}          # Delete user (soft delete)
  POST   /users/{id}/reset-password # Send password reset
  PUT    /users/{id}/admin    # Grant/revoke admin privileges

  # Source Management
  GET    /sources             # List sources with article counts
  POST   /sources             # Add new source
  PUT    /sources/{id}        # Update source
  DELETE /sources/{id}        # Delete source
  POST   /sources/{id}/test   # Test RSS feed connectivity

  # Article Management
  GET    /articles            # Search/filter articles
  DELETE /articles/{id}       # Delete article
  POST   /articles/{id}/reprocess # Reprocess article through pipeline

  # Framework Management
  GET    /frameworks          # List all frameworks
  POST   /frameworks          # Create framework
  PUT    /frameworks/{id}     # Update framework
  DELETE /frameworks/{id}     # Delete framework

  # Logs & Monitoring
  GET    /logs/application    # Application logs (last N lines)
  GET    /logs/jobs           # Job execution logs
  GET    /logs/errors         # Error logs with filters
  POST   /logs/clear          # Clear old logs

  # Audit Trail
  GET    /audit              # Admin action audit log

  # Maintenance
  POST   /maintenance/cleanup  # Run database cleanup tasks
  POST   /maintenance/reindex  # Rebuild database indexes
  GET    /maintenance/health   # Deep health check
  POST   /maintenance/backup   # Trigger database backup
```

### 4.3 Key Endpoint Implementations

#### 4.3.1 Dashboard Endpoint

```python
@router.get("/dashboard")
def get_admin_dashboard(
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard overview for admin panel.
    Includes system stats, recent jobs, recent errors, etc.
    """
    # System stats (existing from /admin/stats)
    # Recent job executions
    # Active jobs
    # Error summary
    # User activity stats
    # API usage metrics
```

#### 4.3.2 Database Table Access

```python
@router.get("/database/{table_name}")
def get_table_data(
    table_name: str,
    page: int = 1,
    page_size: int = 50,
    sort_by: Optional[str] = None,
    filters: Optional[str] = None,  # JSON string
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get paginated data from any database table.
    Supports sorting, filtering, and pagination.
    """
    # Validate table name against allowed tables
    # Build dynamic query with SQLModel
    # Apply filters and sorting
    # Return paginated results with metadata
```

#### 4.3.3 Job Trigger with Tracking

```python
@router.post("/jobs/trigger/{job_id}")
def trigger_job_with_tracking(
    job_id: str,
    background_tasks: BackgroundTasks,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Trigger a background job and create execution history record.
    """
    # Create JobExecutionHistory record with status='running'
    # Trigger job with wrapped task that updates history on completion
    # Create AdminAuditLog entry
    # Return tracking ID
```

### 4.4 Configuration Updates

**File**: `backend/app/config.py`

Add:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Admin Configuration
    admin_token: Optional[str] = None
    admin_panel_enabled: bool = True
    max_audit_log_days: int = 90  # Keep audit logs for 90 days
    max_job_history_days: int = 30  # Keep job history for 30 days
```

---

## 5. Frontend Implementation

### 5.1 Admin Section Structure

```
/frontend/src/app/admin/
  layout.tsx                    # Admin layout with sidebar
  page.tsx                      # Dashboard home

  database/
    page.tsx                    # Database browser main
    [table]/
      page.tsx                  # Table view with CRUD

  jobs/
    page.tsx                    # Job management main
    history/
      page.tsx                  # Job execution history
    schedule/
      page.tsx                  # Schedule configuration

  users/
    page.tsx                    # User management
    [id]/
      page.tsx                  # User detail/edit

  sources/
    page.tsx                    # Source management

  articles/
    page.tsx                    # Article search/management

  frameworks/
    page.tsx                    # Framework management

  logs/
    page.tsx                    # Log viewer

  audit/
    page.tsx                    # Audit trail

  maintenance/
    page.tsx                    # Maintenance tools
```

### 5.2 Admin Components

**Location**: `/frontend/src/components/admin/`

Key components:
- `AdminSidebar.tsx` - Navigation sidebar
- `AdminHeader.tsx` - Header with admin badge
- `DataTable.tsx` - Generic table with sort/filter/pagination
- `RecordEditor.tsx` - Generic CRUD form
- `JobCard.tsx` - Job status card
- `LogViewer.tsx` - Log display with filtering
- `MetricCard.tsx` - System metric display
- `ConfirmDialog.tsx` - Delete confirmation modal

### 5.3 API Client Updates

**File**: `frontend/src/lib/api.ts`

Add admin section:
```typescript
class ApiClient {
  // ... existing methods ...

  // Admin endpoints
  async getAdminDashboard() {
    return this.adminRequest('/admin-panel/dashboard');
  }

  async getTableData(table: string, params: TableParams) {
    // Implementation
  }

  async triggerJob(jobId: string) {
    // Implementation
  }

  // ... etc

  private async adminRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Add X-Admin-Token header from localStorage
    const adminToken = localStorage.getItem('admin_token');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Admin-Token': adminToken || '',
      ...(options.headers as Record<string, string>),
    };

    // Use existing request method
    return this.request(endpoint, { ...options, headers });
  }
}
```

### 5.4 Admin Authentication Flow

**File**: `frontend/src/app/admin/page.tsx`

```typescript
'use client';

export default function AdminDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [adminToken, setAdminToken] = useState('');

  useEffect(() => {
    // Check for existing admin token
    const token = localStorage.getItem('admin_token');
    if (token) {
      // Verify token is valid
      verifyAdminAccess(token);
    }
  }, []);

  const handleLogin = async () => {
    try {
      // Verify admin token with backend
      await api.verifyAdminToken(adminToken);
      localStorage.setItem('admin_token', adminToken);
      setIsAuthenticated(true);
    } catch (error) {
      alert('Invalid admin token');
    }
  };

  if (!isAuthenticated) {
    return <AdminLogin onLogin={handleLogin} />;
  }

  return <AdminDashboardContent />;
}
```

### 5.5 Navbar Update

**File**: `frontend/src/components/Navbar.tsx`

Add admin link for admin users:
```typescript
{currentUser?.is_admin && (
  <Link
    href="/admin"
    className="admin-link"
  >
    🔧 Admin Panel
  </Link>
)}
```

---

## 6. Security Considerations

### 6.1 Token Management

- **Environment Variable**: `ADMIN_TOKEN` must be set in production
- **Rotation**: Document process for rotating admin token
- **Storage**: Frontend stores token in localStorage (encrypted in production)
- **Transmission**: Always over HTTPS in production

### 6.2 Access Control Layers

1. **Admin Token** (Header): `X-Admin-Token` must match env variable
2. **User Token** (Bearer): Valid JWT token required
3. **User Flag**: `is_admin` must be `True`
4. **Audit Logging**: All actions logged to `AdminAuditLog`

### 6.3 Rate Limiting

Add rate limiting to admin endpoints:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/database/{table}/{id}")
@limiter.limit("30/minute")  # Max 30 deletions per minute
def delete_record(...):
    pass
```

### 6.4 Dangerous Operations

Require confirmation for:
- Deleting users
- Deleting sources
- Clearing logs
- Running maintenance tasks

Implement soft deletes where appropriate.

---

## 7. Logging & Monitoring

### 7.1 Job Execution Tracking

**Update all job tasks** (`backend/app/jobs/tasks.py`):

```python
def scrape_job(session: Session = None):
    # Create execution history record
    history = JobExecutionHistory(
        job_id='scrape_rss',
        job_name='Scrape RSS Feeds',
        started_at=datetime.utcnow(),
        status='running'
    )

    try:
        # Execute job
        result = scrape_all_active_sources(session)

        # Update history
        history.status = 'success'
        history.completed_at = datetime.utcnow()
        history.result_data = json.dumps(result)

    except Exception as e:
        history.status = 'failed'
        history.error_message = str(e)

    finally:
        history.duration_seconds = (
            datetime.utcnow() - history.started_at
        ).total_seconds()

        with Session(engine) as db:
            db.add(history)
            db.commit()
```

### 7.2 Application Logging

**File**: `backend/app/utils/logging_config.py` (new file)

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure application logging with rotation"""

    # File handler with rotation
    handler = RotatingFileHandler(
        'logs/pulse.log',
        maxBytes=10_000_000,  # 10MB
        backupCount=10
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Configure root logger
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
```

### 7.3 Log Viewing Endpoint

```python
@router.get("/logs/application")
def get_application_logs(
    lines: int = 100,
    level: Optional[str] = None,
    search: Optional[str] = None,
    admin_user: User = Depends(get_admin_user)
) -> Dict[str, Any]:
    """
    Read application logs with filtering.
    """
    # Read log file
    # Filter by level and search term
    # Return most recent N lines
```

---

## 8. Testing Strategy

### 8.1 Backend Tests

**File**: `backend/tests/routes/test_admin_panel.py`

Test categories:
- ✅ Authentication (valid/invalid admin token)
- ✅ Authorization (admin flag required)
- ✅ Database CRUD operations
- ✅ Job triggering and tracking
- ✅ User management
- ✅ Audit logging
- ✅ Error handling

### 8.2 Frontend Tests

**File**: `frontend/src/app/admin/__tests__/`

Test categories:
- ✅ Admin login flow
- ✅ Dashboard rendering
- ✅ Table operations (view/edit/delete)
- ✅ Job triggering
- ✅ Navigation
- ✅ Error states

### 8.3 Integration Tests

Test full workflows:
- Admin logs in → views users → updates user → verifies audit log
- Admin triggers job → monitors execution → views completion in history
- Admin deletes article → verifies cascade deletion

---

## 9. Deployment Checklist

### 9.1 Environment Variables

Add to `.env` and production:
```bash
# Admin Configuration
ADMIN_TOKEN=your-secure-random-token-here
ADMIN_PANEL_ENABLED=true
MAX_AUDIT_LOG_DAYS=90
MAX_JOB_HISTORY_DAYS=30
```

Generate secure token:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 9.2 Database Migrations

```bash
# Local
docker-compose exec backend alembic upgrade head

# Production (Render)
# Migrations auto-run on deploy via render.yaml
```

### 9.3 Initial Admin User

Create script to promote user to admin:

**File**: `backend/scripts/create_admin.py`
```python
"""
Script to grant admin privileges to a user.
Usage: python scripts/create_admin.py user@example.com
"""
import sys
from sqlmodel import Session, select
from app.database import engine
from app.models import User

email = sys.argv[1]
with Session(engine) as session:
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        user.is_admin = True
        session.add(user)
        session.commit()
        print(f"✓ {email} is now an admin")
    else:
        print(f"✗ User {email} not found")
```

### 9.4 Security Hardening

- [ ] HTTPS enforced in production
- [ ] Admin token stored in secure secrets manager
- [ ] Rate limiting enabled
- [ ] CORS configured to allow only frontend domain
- [ ] Audit logs reviewed regularly
- [ ] Job history cleanup scheduled

---

## 10. Implementation Timeline

### Phase 1: Database & Backend Foundation (2-3 days)
- [ ] Add database models (User updates, JobExecutionHistory, AdminAuditLog)
- [ ] Create and run migrations
- [ ] Implement admin authentication middleware
- [ ] Create admin_panel.py router skeleton
- [ ] Write tests for authentication/authorization

### Phase 2: Core Admin API Endpoints (3-4 days)
- [ ] Dashboard endpoint
- [ ] Database table CRUD endpoints
- [ ] Job management endpoints
- [ ] User management endpoints
- [ ] Audit logging integration
- [ ] Write comprehensive endpoint tests

### Phase 3: Job Tracking & Monitoring (2 days)
- [ ] Update all job tasks to create history records
- [ ] Implement job execution tracking
- [ ] Log viewer endpoints
- [ ] System metrics endpoints
- [ ] Write job tracking tests

### Phase 4: Frontend Foundation (2-3 days)
- [ ] Admin layout and navigation
- [ ] Admin authentication page
- [ ] Dashboard page
- [ ] Reusable admin components (DataTable, etc.)
- [ ] API client updates

### Phase 5: Frontend CRUD Pages (3-4 days)
- [ ] Database browser
- [ ] User management UI
- [ ] Source management UI
- [ ] Article management UI
- [ ] Job management UI
- [ ] Write frontend tests

### Phase 6: Monitoring & Logs (2 days)
- [ ] Log viewer UI
- [ ] Audit trail UI
- [ ] Job history UI
- [ ] Real-time job monitoring
- [ ] System metrics dashboard

### Phase 7: Testing & Polish (2-3 days)
- [ ] Integration tests
- [ ] Security testing
- [ ] UI/UX polish
- [ ] Error handling improvements
- [ ] Performance optimization

### Phase 8: Documentation & Deployment (1-2 days)
- [ ] Admin panel user guide
- [ ] API documentation updates
- [ ] Deployment instructions
- [ ] Create admin user script
- [ ] Production deployment

**Total Estimated Time**: 17-23 days (3-4.5 weeks)

---

## 11. Future Enhancements

### 11.1 Advanced Features (Phase 2)
- Real-time dashboard updates (WebSocket)
- Custom SQL query builder UI
- Bulk operations (bulk delete, bulk update)
- Data export (CSV, JSON)
- Advanced filtering with saved filters
- Role-based access control (multiple admin levels)
- Two-factor authentication for admin

### 11.2 Analytics & Insights
- Job performance trends over time
- User growth charts
- Article processing metrics
- API usage analytics
- Cost tracking (OpenAI API usage)

### 11.3 Advanced Monitoring
- Email alerts for job failures
- Slack/Discord integration for notifications
- Health check dashboard with uptime tracking
- Performance profiling tools

---

## 12. Open Questions & Decisions Needed

1. **Admin Token Management**:
   - Should we support multiple admin tokens for different admins?
   - How often should the token rotate?

2. **Database Operations**:
   - Should we allow raw SQL queries or only table-level CRUD?
   - What tables should be read-only in the UI?

3. **Job Scheduling**:
   - Should admins be able to modify job schedules permanently, or just trigger one-off runs?
   - Should we add job queueing (multiple instances)?

4. **UI/UX**:
   - Should the admin panel have a different color scheme to distinguish it?
   - Should we use a third-party admin UI library (like React Admin) or build custom?

5. **Audit Retention**:
   - How long should we keep audit logs?
   - Should old logs be archived or permanently deleted?

---

## 13. Success Criteria

The admin panel is considered complete when:

- ✅ An admin can log in with the admin token
- ✅ All database tables are viewable and editable
- ✅ All background jobs can be triggered and monitored
- ✅ Users can be managed (view, edit, delete, promote to admin)
- ✅ Sources can be added, edited, and tested
- ✅ Application logs are viewable and searchable
- ✅ Job execution history is tracked and viewable
- ✅ All admin actions are logged in audit trail
- ✅ System metrics are displayed on dashboard
- ✅ All features have comprehensive test coverage
- ✅ Admin panel is deployed to production
- ✅ Documentation is complete

---

## 14. Risk Mitigation

### 14.1 Security Risks
- **Risk**: Admin token leaked
  - **Mitigation**: Token rotation process documented, rate limiting on admin endpoints

- **Risk**: Unauthorized database access
  - **Mitigation**: Multi-layer auth (token + JWT + admin flag), audit logging

### 14.2 Performance Risks
- **Risk**: Slow queries on large tables
  - **Mitigation**: Pagination, indexing, query optimization

- **Risk**: Frontend hangs with large data sets
  - **Mitigation**: Virtual scrolling, lazy loading, data limits

### 14.3 Operational Risks
- **Risk**: Accidental data deletion
  - **Mitigation**: Confirmation dialogs, soft deletes, audit trail for recovery

- **Risk**: Job execution conflicts
  - **Mitigation**: Job locking (max_instances=1), execution history tracking

---

## 15. Recommended Architecture Decision

Based on your project structure and requirements, I recommend:

### Option A: Integrated Admin Panel ✅ **RECOMMENDED**

**Pros**:
- Seamless integration with existing auth system
- Consistent UI/UX with main application
- Easier to maintain (one codebase)
- Better for production deployment
- Audit logging built-in

**Cons**:
- More development time upfront
- Need to build custom components

**Implementation**: As described in this document

### Option B: Third-Party Admin Framework (NOT recommended)

**Examples**: React Admin, AdminJS, Django Admin

**Pros**:
- Faster initial development
- Pre-built components

**Cons**:
- Additional dependencies
- Harder to customize
- Inconsistent with your design
- Complex integration with FastAPI

**Verdict**: Given your well-structured project and production requirements, **Option A** is strongly recommended.

---

## 16. Next Steps

To proceed with implementation:

1. **Review this plan** and provide feedback
2. **Answer open questions** (Section 12)
3. **Confirm timeline** and priorities
4. **Set up admin token** in local environment
5. **Begin Phase 1** (Database & Backend Foundation)

Once approved, I can begin implementation following this plan systematically.

---

## Appendix A: File Structure Summary

```
backend/
  app/
    routes/
      admin_panel.py              # NEW: Main admin API routes
    models.py                     # MODIFIED: Add admin tables
    config.py                     # MODIFIED: Add admin settings
    utils/
      admin_auth.py               # NEW: Admin authentication
      logging_config.py           # NEW: Logging configuration
  scripts/
    create_admin.py               # NEW: Admin user creation script
  tests/
    routes/
      test_admin_panel.py         # NEW: Admin endpoint tests

frontend/
  src/
    app/
      admin/                      # NEW: Entire admin section
        layout.tsx
        page.tsx
        database/
        jobs/
        users/
        sources/
        articles/
        frameworks/
        logs/
        audit/
        maintenance/
    components/
      admin/                      # NEW: Admin-specific components
        AdminSidebar.tsx
        AdminHeader.tsx
        DataTable.tsx
        JobCard.tsx
        LogViewer.tsx
        MetricCard.tsx
    lib/
      api.ts                      # MODIFIED: Add admin endpoints
```

---

## Appendix B: Complete Code Templates

**These are copy-paste ready code snippets for quick implementation.**

### B.1 Database Models (Add to `backend/app/models.py`)

```python
# Add to User model (around line 261)
class User(SQLModel, table=True):
    # ... existing fields ...

    # Admin fields (ADD THESE)
    is_admin: bool = Field(default=False)
    admin_notes: Optional[str] = Field(default=None, max_length=1000)
    last_admin_action: Optional[datetime] = Field(default=None)


# Add new models at end of file (after SourceCredibilityRating)

class JobExecutionHistory(SQLModel, table=True):
    """Track all background job executions for monitoring and debugging."""
    __tablename__ = "job_execution_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(max_length=100, index=True)
    job_name: str = Field(max_length=200)

    # Execution details
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)

    # Status
    status: str = Field(max_length=20)  # success, failed, running
    result_data: Optional[str] = Field(default=None)  # JSON string
    error_message: Optional[str] = Field(default=None, max_length=2000)

    # Metrics
    items_processed: Optional[int] = Field(default=None)
    api_calls_made: Optional[int] = Field(default=None)
    tokens_used: Optional[int] = Field(default=None)

    # Trigger info
    triggered_by: str = Field(default="scheduler")  # scheduler, admin, api
    triggered_by_user_id: Optional[int] = Field(default=None)


class AdminAuditLog(SQLModel, table=True):
    """Track all admin actions for security and debugging."""
    __tablename__ = "admin_audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(foreign_key="users.id", index=True)
    admin_email: str = Field(max_length=255, index=True)

    # Action details
    action_type: str = Field(max_length=100, index=True)
    resource_type: str = Field(max_length=100)
    resource_id: Optional[str] = Field(default=None, max_length=100)

    # Change tracking
    old_value: Optional[str] = Field(default=None)  # JSON string
    new_value: Optional[str] = Field(default=None)  # JSON string

    # Metadata
    ip_address: Optional[str] = Field(default=None, max_length=50)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    notes: Optional[str] = Field(default=None, max_length=500)
```

### B.2 Config Updates (Add to `backend/app/config.py`)

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Admin Configuration (ADD THESE)
    admin_token: Optional[str] = None
    admin_panel_enabled: bool = True
    max_audit_log_days: int = 90
    max_job_history_days: int = 30
```

### B.3 Admin Authentication Middleware (`backend/app/utils/admin_auth.py`)

**Create this new file:**

```python
"""
Admin authentication utilities.
Validates admin token and user permissions.
"""
from fastapi import HTTPException, status, Depends, Header, Request
from typing import Optional
from ..config import settings
from .auth import get_current_user
from ..models import User, AdminAuditLog
from sqlmodel import Session
from ..database import get_session
import logging

logger = logging.getLogger(__name__)


def verify_admin_token(x_admin_token: Optional[str] = Header(None)) -> bool:
    """
    Verify admin token from request headers.
    Raises HTTPException if invalid.
    """
    if not settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin token not configured on server"
        )

    if not x_admin_token or x_admin_token != settings.admin_token:
        logger.warning(f"Invalid admin token attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token"
        )

    return True


def get_admin_user(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(verify_admin_token)
) -> User:
    """
    Get current user and verify they have admin privileges.
    Requires both valid JWT token AND admin token.
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.email} attempted admin access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


def log_admin_action(
    admin_user: User,
    action_type: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    session: Session = None,
    request: Request = None
):
    """
    Create an audit log entry for an admin action.
    """
    if session is None:
        from ..database import engine
        with Session(engine) as db:
            _create_audit_log(admin_user, action_type, resource_type,
                            resource_id, old_value, new_value, db, request)
    else:
        _create_audit_log(admin_user, action_type, resource_type,
                        resource_id, old_value, new_value, session, request)


def _create_audit_log(admin_user, action_type, resource_type, resource_id,
                      old_value, new_value, session, request):
    """Helper to create audit log."""
    audit = AdminAuditLog(
        user_id=admin_user.id,
        admin_email=admin_user.email,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    session.add(audit)
    session.commit()
```

### B.4 Create Admin Script (`backend/scripts/create_admin.py`)

**Create this new file:**

```python
"""
Script to grant admin privileges to a user.

Usage:
    python -m backend.scripts.create_admin user@example.com

Run from project root directory.
"""
import sys
from sqlmodel import Session, select
from backend.app.database import engine
from backend.app.models import User


def make_admin(email: str):
    """Grant admin privileges to user."""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()

        if not user:
            print(f"✗ User '{email}' not found")
            print("\nAvailable users:")
            users = session.exec(select(User)).all()
            for u in users:
                admin_badge = " (ADMIN)" if u.is_admin else ""
                print(f"  - {u.email}{admin_badge}")
            return False

        if user.is_admin:
            print(f"✓ {email} is already an admin")
            return True

        user.is_admin = True
        session.add(user)
        session.commit()

        print(f"✓ {email} is now an admin")
        return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m backend.scripts.create_admin user@example.com")
        sys.exit(1)

    email = sys.argv[1]
    success = make_admin(email)
    sys.exit(0 if success else 1)
```

### B.5 Frontend API Client Updates (`frontend/src/lib/api.ts`)

**Add these methods to the ApiClient class:**

```typescript
// Admin endpoints (add to ApiClient class)

// Admin authentication
async verifyAdminToken(adminToken: string) {
  return this.adminRequest('/admin-panel/verify', {}, adminToken);
}

// Dashboard
async getAdminDashboard() {
  return this.adminRequest<{
    system_stats: any;
    recent_jobs: any[];
    active_jobs: any[];
    error_summary: any;
  }>('/admin-panel/dashboard');
}

// Database management
async getTableData(table: string, params: {
  page?: number;
  page_size?: number;
  sort_by?: string;
  filters?: string;
}) {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params.sort_by) queryParams.append('sort_by', params.sort_by);
  if (params.filters) queryParams.append('filters', params.filters);

  return this.adminRequest(`/admin-panel/database/${table}?${queryParams}`);
}

async deleteRecord(table: string, id: number) {
  return this.adminRequest(`/admin-panel/database/${table}/${id}`, {
    method: 'DELETE',
  });
}

// Job management
async getJobHistory(params?: {
  job_id?: string;
  status?: string;
  limit?: number;
}) {
  const queryParams = new URLSearchParams();
  if (params?.job_id) queryParams.append('job_id', params.job_id);
  if (params?.status) queryParams.append('status', params.status);
  if (params?.limit) queryParams.append('limit', params.limit.toString());

  return this.adminRequest(`/admin-panel/jobs/history?${queryParams}`);
}

async triggerJob(jobId: string) {
  return this.adminRequest(`/admin-panel/jobs/trigger/${jobId}`, {
    method: 'POST',
  });
}

// User management
async getAdminUsers(params?: {
  page?: number;
  search?: string;
  is_admin?: boolean;
}) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.search) queryParams.append('search', params.search);
  if (params?.is_admin !== undefined) queryParams.append('is_admin', params.is_admin.toString());

  return this.adminRequest(`/admin-panel/users?${queryParams}`);
}

async updateUserAdmin(userId: number, isAdmin: boolean) {
  return this.adminRequest(`/admin-panel/users/${userId}/admin`, {
    method: 'PUT',
    body: JSON.stringify({ is_admin: isAdmin }),
  });
}

// Logs
async getApplicationLogs(params?: {
  lines?: number;
  level?: string;
  search?: string;
}) {
  const queryParams = new URLSearchParams();
  if (params?.lines) queryParams.append('lines', params.lines.toString());
  if (params?.level) queryParams.append('level', params.level);
  if (params?.search) queryParams.append('search', params.search);

  return this.adminRequest(`/admin-panel/logs/application?${queryParams}`);
}

// Audit trail
async getAuditLog(params?: {
  page?: number;
  action_type?: string;
  user_id?: number;
}) {
  const queryParams = new URLSearchParams();
  if (params?.page) queryParams.append('page', params.page.toString());
  if (params?.action_type) queryParams.append('action_type', params.action_type);
  if (params?.user_id) queryParams.append('user_id', params.user_id.toString());

  return this.adminRequest(`/admin-panel/audit?${queryParams}`);
}

// Helper method for admin requests
private async adminRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  customToken?: string
): Promise<T> {
  const adminToken = customToken || (typeof window !== 'undefined'
    ? localStorage.getItem('admin_token')
    : null);

  if (!adminToken) {
    throw new Error('Admin token required');
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Admin-Token': adminToken,
    ...(options.headers as Record<string, string>),
  };

  if (this.token) {
    headers['Authorization'] = `Bearer ${this.token}`;
  }

  return this.request(endpoint, { ...options, headers });
}
```

### B.6 Environment Variables Template

**Add to `.env` file:**

```bash
# Admin Panel Configuration
ADMIN_TOKEN=your-secure-token-here-change-in-production
ADMIN_PANEL_ENABLED=true
MAX_AUDIT_LOG_DAYS=90
MAX_JOB_HISTORY_DAYS=30
```

**Generate secure token with:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### B.7 Migration Commands

```bash
# 1. Create migration
docker-compose exec backend alembic revision --autogenerate -m "add_admin_panel_tables"

# 2. Copy migration to local (CRITICAL for deployment)
docker cp news_backend:/app/alembic/versions/[NEW_FILE].py backend/alembic/versions/

# 3. Apply migration
docker-compose exec backend alembic upgrade head

# 4. Verify tables created
docker-compose exec backend python -c "
from app.database import engine
from sqlmodel import text, Session
with Session(engine) as s:
    tables = s.exec(text(\"SELECT tablename FROM pg_tables WHERE schemaname='public'\")).all()
    print([t for t in tables])
"
```

### B.8 Create First Admin User

```bash
# After migration, create your first admin user
docker-compose exec backend python -m backend.scripts.create_admin your-email@example.com
```

### B.9 Test Admin Endpoints

```bash
# 1. Get admin token from .env
ADMIN_TOKEN="your-token-here"

# 2. Login as user to get JWT
USER_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}' \
  | jq -r '.access_token')

# 3. Test admin endpoint
curl -X GET http://localhost:8000/admin-panel/dashboard \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "X-Admin-Token: $ADMIN_TOKEN"
```

---

**End of Plan Document**
