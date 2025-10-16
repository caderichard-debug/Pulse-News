# Admin Panel Documentation

> **Complete guide to Pulse Admin Panel: Architecture, Features, and Access**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication & Authorization](#authentication--authorization)
4. [Accessing the Admin Panel](#accessing-the-admin-panel)
5. [Features & Capabilities](#features--capabilities)
6. [Security Model](#security-model)
7. [API Endpoints](#api-endpoints)
8. [Development Guide](#development-guide)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Pulse Admin Panel is a comprehensive administrative interface for managing the news aggregation platform. It provides system monitoring, database management, job control, and user administration capabilities.

### Key Features

- 📊 **Dashboard** - Real-time system statistics and monitoring
- 🗄️ **Database Management** - Direct access to all database tables
- ⚙️ **Job Control** - Monitor and trigger background jobs
- 👥 **User Management** - Manage user accounts and permissions
- 📰 **Source Management** - Configure RSS feeds and news sources
- 📄 **Article Management** - Browse, search, and manage articles
- 📋 **Audit Log** - Complete history of all admin actions
- 🔒 **Secure Access** - Role-based access control with audit trails

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Admin Layout │  │ Admin Pages  │  │   API Client │      │
│  │   (Auth)     │──│ (Dashboard,  │──│  (api.ts)    │      │
│  │              │  │  Database,   │  │              │      │
│  │              │  │  Jobs, etc.) │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
                             │ Authorization: Bearer <JWT>
┌────────────────────────────┴────────────────────────────────┐
│                     Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Auth       │  │ Admin Routes │  │ Admin Auth   │      │
│  │  Middleware  │──│   (admin_    │──│   Utils      │      │
│  │              │  │   panel.py)  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │ SQLModel ORM
┌────────────────────────────┴────────────────────────────────┐
│                   Database (PostgreSQL)                      │
├─────────────────────────────────────────────────────────────┤
│  Users (is_admin flag) │ Articles │ Sources │ Jobs │ Logs   │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

#### Backend
```
backend/app/
├── routes/
│   ├── auth.py                    # Authentication endpoints (includes is_admin)
│   └── admin_panel.py             # Admin panel API endpoints
├── utils/
│   └── admin_auth.py              # Admin authorization utilities
└── models.py                      # Database models (User.is_admin field)
```

#### Frontend
```
frontend/src/
├── app/
│   └── admin/
│       ├── layout.tsx             # Admin layout with auth check
│       ├── page.tsx               # Dashboard
│       ├── database/page.tsx      # Database management
│       ├── jobs/page.tsx          # Job monitoring
│       ├── users/page.tsx         # User management
│       ├── sources/page.tsx       # Source management
│       ├── articles/page.tsx      # Article management
│       └── audit/page.tsx         # Audit log viewer
├── components/
│   └── Navbar.tsx                 # Main nav (shows Admin tab for admins)
└── lib/
    └── api.ts                     # API client with admin methods
```

---

## Authentication & Authorization

### How It Works

The admin panel uses a **role-based access control (RBAC)** system integrated with the main user authentication:

1. **User Authentication**
   - Users log in with email/password
   - Backend issues JWT token
   - Token contains user's email (sub claim)

2. **Admin Authorization**
   - Each user has an `is_admin` boolean field in the database
   - Admin panel checks `user.is_admin === true`
   - All admin API endpoints verify the user's admin status

3. **Token Flow**
   ```
   User Login → JWT Token → API Request → Token Validation
                    ↓                           ↓
              localStorage               Decode JWT → Get User
                                              ↓
                                         Check is_admin
                                              ↓
                                    Allow/Deny Admin Access
   ```

### Database Schema

#### User Model (relevant fields)
```python
class User(SQLModel, table=True):
    id: int
    email: str
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False        # ← Admin flag
    admin_notes: Optional[str]     # Notes about admin privileges
    last_admin_action: Optional[datetime]  # Last admin action timestamp
```

### Backend Authentication

**File:** `backend/app/utils/admin_auth.py`

```python
def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency for protecting admin endpoints.

    - Verifies JWT token (via get_current_user)
    - Checks user.is_admin == True
    - Raises 403 if not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
```

**Usage in routes:**
```python
@router.get("/admin-panel/dashboard")
def get_admin_dashboard(
    admin_user: User = Depends(get_admin_user),  # ← Admin check
    session: Session = Depends(get_session)
):
    # This endpoint only runs if user is admin
    return dashboard_data
```

### Frontend Authentication

**File:** `frontend/src/app/admin/layout.tsx`

```typescript
useEffect(() => {
  const checkAdminAuth = async () => {
    // 1. Check if logged in
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    // 2. Load token into API client
    api.setToken(token);

    // 3. Get user info and check is_admin
    const user = await api.getCurrentUser();
    if (user.is_admin) {
      setIsAuthenticated(true);
    } else {
      router.push('/feed');  // Redirect non-admins
    }
  };

  checkAdminAuth();
}, []);
```

---

## Accessing the Admin Panel

### Prerequisites

1. **Have an admin account**
   - Your user account must have `is_admin = true` in the database
   - Contact a system administrator to set this flag

2. **Be logged in**
   - Log in through the normal login page
   - Your JWT token will be used for admin access

### Access Methods

#### Method 1: Admin Tab (Recommended)

1. Log in to Pulse at `http://localhost:3000/login`
2. Look for the **⚡ Admin** tab in the navigation bar (far right)
3. Click the Admin tab to access the admin panel

**Note:** The Admin tab only appears if your account has admin privileges.

```
Navigation Bar (Admin User):
┌──────────────────────────────────────────────────────────┐
│ Pulse | Feed | Sources | Analytics | Preferences |       │
│       | How It Works | ⚡ Admin |   [Your Name] Logout   │
└──────────────────────────────────────────────────────────┘
                            ↑
                    Click here to access
```

#### Method 2: Direct URL

Navigate directly to: `http://localhost:3000/admin`

- If logged in as admin → Shows admin dashboard
- If logged in as regular user → Redirects to feed
- If not logged in → Redirects to login

### First-Time Admin Setup

If you're setting up the system for the first time, you need to manually set a user as admin:

#### Option 1: Using Python Script (Recommended)

```bash
docker-compose exec -T backend python -c "
from app.database import engine
from sqlmodel import Session, select
from app.models import User

with Session(engine) as session:
    user = session.exec(
        select(User).where(User.email == 'your-email@example.com')
    ).first()

    if user:
        user.is_admin = True
        session.add(user)
        session.commit()
        print(f'{user.email} is now an admin!')
    else:
        print('User not found')
"
```

#### Option 2: Using SQL

```bash
docker-compose exec -T db psql -U postgres -d news_db -c "
UPDATE users
SET is_admin = true
WHERE email = 'your-email@example.com';
"
```

#### Option 3: Create Admin User from Scratch

```bash
docker-compose exec -T backend python -c "
from app.database import engine
from sqlmodel import Session
from app.models import User
from app.utils.auth import hash_password

with Session(engine) as session:
    admin = User(
        email='admin@example.com',
        name='Admin User',
        hashed_password=hash_password('your-secure-password'),
        is_active=True,
        is_admin=True,
        email_verified=True
    )
    session.add(admin)
    session.commit()
    print('Admin user created!')
"
```

### Testing Admin Access

**Test Users (Development Only):**

The following test users are available in development:

```
Admin User:
  Email: admin@test.com
  Password: password123
  is_admin: true

Regular User:
  Email: regular@test.com
  Password: password123
  is_admin: false
```

---

## Features & Capabilities

### 1. Dashboard (`/admin`)

**Purpose:** System overview and monitoring

**Features:**
- **System Statistics**
  - Total users (with admin count)
  - Total articles (with today's count)
  - Active sources
  - Configured frameworks

- **Active Jobs**
  - Currently running background jobs
  - Duration tracking
  - Real-time status

- **Recent Jobs**
  - Last 5 job executions
  - Status (success/failed)
  - Duration and items processed
  - Quick link to full job history

- **Error Summary**
  - Failed jobs in last 24 hours
  - Quick link to investigate

- **Recent Admin Actions**
  - Last 10 admin operations
  - User, action type, timestamp
  - Link to full audit log

**API Endpoint:** `GET /admin-panel/dashboard`

**Response Example:**
```json
{
  "system_stats": {
    "users": {"total": 249, "admins": 2},
    "articles": {"total": 626, "today": 197},
    "sources": {"total": 8, "active": 8},
    "frameworks": {"total": 10}
  },
  "recent_jobs": [...],
  "active_jobs": [...],
  "error_summary": {"failed_jobs_24h": 0},
  "recent_admin_actions": [...]
}
```

---

### 2. Database Management (`/admin/database`)

**Purpose:** Direct access to all database tables

**Features:**
- View all tables (users, articles, sources, etc.)
- Search and filter records
- Edit existing records
- Delete records (with confirmation)
- Create new records
- View relationships between tables
- Export data to CSV/JSON

**Supported Tables:**
- Users
- Articles
- Sources
- Topics
- Frameworks
- Newsletters
- Job Execution History
- Admin Audit Log
- Article Analysis
- Statistics Verification
- User Preferences
- Source Subscriptions

**Security:**
- All changes are logged to audit trail
- Soft deletes where applicable
- Confirmation dialogs for destructive actions

---

### 3. Job Monitoring & Control (`/admin/jobs`)

**Purpose:** Manage background job execution

**Features:**

#### Job History
- View all job executions (paginated)
- Filter by:
  - Job name (scrape, analyze, cluster, etc.)
  - Status (success, failed, running)
  - Date range
- Sort by start time, duration, status
- View detailed execution logs
- See items processed and error messages

#### Manual Job Triggering
- **Scrape RSS Feeds** - Fetch new articles from sources
- **Extract Article Content** - Extract full text from URLs
- **AI Analysis** - Analyze articles with GPT-4
- **Verify Statistics** - Run fact-checking pipeline
- **Cluster Articles** - Group similar articles
- **Generate Context** - Create article context
- **Update Frameworks** - Refresh ethical framework mappings
- **Send Newsletters** - Manually send newsletters

#### Job Scheduler Status
- View configured jobs
- Next run times
- Cron expressions
- Enable/disable scheduled jobs
- Modify job schedules

**API Endpoints:**
```
GET  /admin-panel/jobs/history       # Job execution history
GET  /admin-panel/jobs/active        # Currently running jobs
POST /admin-panel/jobs/trigger       # Trigger specific job
GET  /admin-panel/jobs/scheduler     # Scheduler status
```

---

### 4. User Management (`/admin/users`)

**Purpose:** Manage user accounts and permissions

**Features:**

#### User List
- View all registered users
- Search by email, name
- Filter by:
  - Subscription tier (FREE, PREMIUM)
  - Admin status
  - Active/inactive
  - Email verified/unverified

#### User Details
- View user profile
- See subscription details
- Check last login
- View topic preferences
- See source subscriptions
- Check newsletter settings

#### User Actions
- **Promote to Admin** - Grant admin privileges
- **Revoke Admin** - Remove admin privileges
- **Deactivate Account** - Disable user access
- **Reactivate Account** - Re-enable user access
- **Reset Password** - Force password reset
- **Delete Account** - Permanently remove user (with confirmation)
- **Add Admin Notes** - Document admin decisions

#### Bulk Actions
- Export user list to CSV
- Bulk deactivate/activate
- Bulk email operations

**Security:**
- Cannot delete your own admin account
- Requires confirmation for destructive actions
- All changes logged to audit trail

---

### 5. Source Management (`/admin/sources`)

**Purpose:** Configure RSS feeds and news sources

**Features:**

#### Source List
- View all news sources
- Search by name, URL
- Filter by:
  - Active/inactive status
  - Topic categories
  - Scrape success rate
  - Last scrape time

#### Source Configuration
- Add new RSS feed sources
- Edit source details:
  - Name
  - RSS feed URL
  - Website URL
  - Description
  - Topics (multi-select)
- Enable/disable sources
- Configure scrape settings:
  - Max articles per scrape
  - Scrape frequency override
  - Custom extraction rules

#### Source Analytics
- Articles scraped (total, last 7 days)
- Success/failure rate
- Average articles per scrape
- Last successful scrape
- Error logs

#### Actions
- **Test Feed** - Verify RSS feed is accessible
- **Force Scrape** - Immediately scrape this source
- **View Articles** - See all articles from this source
- **Delete Source** - Remove source (archives articles)

**API Endpoints:**
```
GET    /admin-panel/sources           # List all sources
POST   /admin-panel/sources           # Create new source
GET    /admin-panel/sources/{id}      # Get source details
PUT    /admin-panel/sources/{id}      # Update source
DELETE /admin-panel/sources/{id}      # Delete source
POST   /admin-panel/sources/{id}/test # Test feed
```

---

### 6. Article Management (`/admin/articles`)

**Purpose:** Browse, search, and manage articles

**Features:**

#### Article Browser
- Paginated article list
- Search by:
  - Title
  - Content
  - Source
  - Author
- Filter by:
  - Date range
  - Source
  - Topics
  - Processing status
  - Sentiment (positive, neutral, negative)
  - Bias (left, center, right)
  - Frameworks

#### Article Details
- Full article content
- AI analysis results:
  - Summary
  - Sentiment analysis
  - Bias detection
  - Ethical frameworks
- Statistics verification:
  - Verified claims
  - Source credibility ratings
  - Fact-check results
- Article context:
  - Background information
  - Timeline
  - Related articles
- Metadata:
  - Scrape time
  - Processing status
  - View count

#### Article Actions
- **Reprocess** - Re-run AI analysis
- **Reverify Stats** - Re-run fact-checking
- **Edit Content** - Manual corrections
- **Flag Article** - Mark for review
- **Delete Article** - Remove from system
- **Feature Article** - Promote to featured
- **Hide Article** - Remove from public view

#### Bulk Actions
- Bulk reprocess
- Bulk delete
- Export to CSV/JSON
- Tag multiple articles

---

### 7. Audit Log (`/admin/audit`)

**Purpose:** Track all administrative actions

**Features:**

#### Audit Trail
- Complete history of admin actions
- Filter by:
  - Admin user
  - Action type (create, update, delete, trigger)
  - Resource type (user, article, source, job)
  - Date range
- Search by resource ID or description

#### Audit Entry Details
- Admin user who performed action
- Timestamp (with timezone)
- Action type
- Resource type and ID
- Old value (before change)
- New value (after change)
- IP address
- User agent (browser/device)

#### Audit Reports
- Export audit log to CSV
- Generate compliance reports
- View admin activity summary
- Detect unusual patterns

**API Endpoint:** `GET /admin-panel/audit`

**Entry Example:**
```json
{
  "id": 123,
  "admin_email": "admin@test.com",
  "action_type": "update_user",
  "resource_type": "user",
  "resource_id": "456",
  "old_value": "{\"is_admin\": false}",
  "new_value": "{\"is_admin\": true}",
  "timestamp": "2025-10-16T03:21:32Z",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

---

## Security Model

### Defense in Depth

The admin panel implements multiple layers of security:

#### 1. Authentication Layer
- **JWT Token Validation**
  - Tokens expire after configured time (default: 30 days)
  - Tokens are signed with secret key
  - Invalid tokens rejected at API gateway

#### 2. Authorization Layer
- **Role-Based Access Control**
  - User must have `is_admin = true`
  - Checked on every admin API request
  - Non-admin users receive 403 Forbidden

#### 3. Audit Layer
- **Comprehensive Logging**
  - All admin actions logged to database
  - Includes user, timestamp, action, old/new values
  - IP address and user agent tracked
  - Cannot be deleted by admins

#### 4. Application Layer
- **Input Validation**
  - All inputs validated with Pydantic models
  - SQL injection prevention via ORM (SQLModel)
  - XSS prevention via React escaping

#### 5. Network Layer
- **HTTPS in Production**
  - All traffic encrypted with TLS
  - Tokens never sent over HTTP
  - Secure cookie flags

### Security Best Practices

#### For System Administrators

1. **Minimize Admin Accounts**
   - Only grant admin access when necessary
   - Use `admin_notes` field to document why user is admin
   - Regularly audit admin user list

2. **Monitor Audit Logs**
   - Review audit log regularly
   - Set up alerts for sensitive actions (user deletion, source changes)
   - Export logs for compliance

3. **Rotate Admin Privileges**
   - Remove admin access when no longer needed
   - Use `last_admin_action` to find inactive admins
   - Document admin role changes

4. **Secure Admin Accounts**
   - Use strong passwords
   - Enable email verification
   - Monitor login attempts

#### For Developers

1. **Use Proper Dependencies**
   - Always use `get_admin_user` dependency for admin endpoints
   - Never bypass authorization checks
   - Log all admin actions with `log_admin_action()`

2. **Validate Input**
   - Use Pydantic models for request validation
   - Sanitize user input
   - Limit query result sizes

3. **Handle Errors Securely**
   - Don't leak sensitive info in error messages
   - Log errors server-side
   - Return generic errors to client

---

## API Endpoints

### Complete Admin API Reference

All admin panel endpoints require:
- **Authorization:** `Bearer <JWT_TOKEN>`
- **Admin Privilege:** User must have `is_admin = true`

#### Dashboard

```
GET /admin-panel/dashboard
```

**Response:**
```json
{
  "system_stats": {...},
  "recent_jobs": [...],
  "active_jobs": [...],
  "error_summary": {...},
  "recent_admin_actions": [...]
}
```

#### Users

```
GET    /admin-panel/users              # List users (paginated)
GET    /admin-panel/users/{id}         # Get user details
PUT    /admin-panel/users/{id}         # Update user
DELETE /admin-panel/users/{id}         # Delete user
POST   /admin-panel/users/{id}/admin   # Toggle admin status
POST   /admin-panel/users/{id}/active  # Toggle active status
```

#### Sources

```
GET    /admin-panel/sources            # List sources
POST   /admin-panel/sources            # Create source
GET    /admin-panel/sources/{id}       # Get source
PUT    /admin-panel/sources/{id}       # Update source
DELETE /admin-panel/sources/{id}       # Delete source
POST   /admin-panel/sources/{id}/test  # Test RSS feed
```

#### Articles

```
GET    /admin-panel/articles           # List articles (paginated)
GET    /admin-panel/articles/{id}      # Get article details
PUT    /admin-panel/articles/{id}      # Update article
DELETE /admin-panel/articles/{id}      # Delete article
POST   /admin-panel/articles/{id}/reprocess  # Reprocess article
```

#### Jobs

```
GET  /admin-panel/jobs/history         # Job execution history
GET  /admin-panel/jobs/active          # Active jobs
POST /admin-panel/jobs/trigger         # Trigger job
GET  /admin-panel/jobs/scheduler       # Scheduler status
```

**Trigger Job Request:**
```json
{
  "job_name": "scrape_rss_feeds"  // or "analyze_articles", etc.
}
```

#### Audit Log

```
GET /admin-panel/audit                 # Audit trail (paginated)
```

**Query Parameters:**
- `admin_email` - Filter by admin user
- `action_type` - Filter by action
- `resource_type` - Filter by resource
- `start_date` - Start date
- `end_date` - End date
- `skip` - Pagination offset
- `limit` - Results per page

---

## Development Guide

### Adding a New Admin Feature

#### 1. Backend: Add Route

**File:** `backend/app/routes/admin_panel.py`

```python
@router.get("/admin-panel/my-feature")
def get_my_feature(
    admin_user: User = Depends(get_admin_user),  # ← Admin check
    session: Session = Depends(get_session),
    request: Request = None
):
    """Your feature description"""

    # Log the admin action
    log_admin_action(
        admin_user=admin_user,
        action_type="view_my_feature",
        resource_type="system",
        session=session,
        request=request
    )

    # Your logic here
    data = fetch_my_feature_data(session)

    return {"data": data}
```

#### 2. Frontend: Add API Method

**File:** `frontend/src/lib/api.ts`

```typescript
async getMyFeature() {
  return this.adminRequest<MyFeatureType>('/admin-panel/my-feature');
}
```

#### 3. Frontend: Create Page

**File:** `frontend/src/app/admin/my-feature/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function MyFeaturePage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const result = await api.getMyFeature();
      setData(result.data);
    } catch (error) {
      console.error('Failed to load:', error);
    }
  };

  return (
    <div>
      <h1>My Feature</h1>
      {/* Your UI here */}
    </div>
  );
}
```

#### 4. Add to Navigation

**File:** `frontend/src/app/admin/layout.tsx`

```typescript
const navItems = [
  // ... existing items
  { href: '/admin/my-feature', label: 'My Feature', icon: '✨' },
];
```

### Testing Admin Features

#### Backend Tests

**File:** `backend/tests/routes/test_admin_panel.py`

```python
def test_my_feature_as_admin(client, admin_token):
    response = client.get(
        "/admin-panel/my-feature",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "data" in response.json()

def test_my_feature_as_regular_user(client, user_token):
    response = client.get(
        "/admin-panel/my-feature",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403  # Forbidden
```

#### Frontend Tests

**File:** `frontend/src/app/admin/my-feature/__tests__/page.test.tsx`

```typescript
import { render, screen } from '@testing-library/react';
import MyFeaturePage from '../page';

jest.mock('@/lib/api');

describe('MyFeaturePage', () => {
  it('loads and displays data', async () => {
    render(<MyFeaturePage />);
    expect(await screen.findByText('My Feature')).toBeInTheDocument();
  });
});
```

---

## Troubleshooting

### Common Issues

#### 1. "Redirected to login when clicking Admin tab"

**Symptoms:**
- Click Admin tab → Immediately redirected to /login
- Already logged in as admin user

**Causes:**
- Token not loaded in API client
- Token expired
- User's `is_admin` flag is false

**Solutions:**

1. Check if user is actually admin:
```bash
docker-compose exec -T backend python -c "
from app.database import engine
from sqlmodel import Session, select
from app.models import User

with Session(engine) as session:
    user = session.exec(
        select(User).where(User.email == 'your-email@example.com')
    ).first()
    print(f'is_admin: {user.is_admin if user else \"User not found\"}')
"
```

2. Check browser console for errors (F12 → Console tab)

3. Verify JWT token in localStorage:
```javascript
// In browser console:
console.log(localStorage.getItem('token'));
```

4. Try logging out and back in

---

#### 2. "403 Forbidden on admin API calls"

**Symptoms:**
- Can access /admin page
- API calls return 403 Forbidden
- Console shows "Admin privileges required"

**Causes:**
- Token not included in request headers
- User's `is_admin` changed to false after login
- Backend not checking admin status correctly

**Solutions:**

1. Verify token is being sent:
```bash
# Check network tab in browser (F12 → Network)
# Look for Authorization header: Bearer <token>
```

2. Test backend directly:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email","password":"your-password"}' \
  | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/admin-panel/dashboard
```

3. Check backend logs:
```bash
docker logs news_backend --tail 50
```

---

#### 3. "Admin dashboard shows no data"

**Symptoms:**
- Can access admin panel
- Dashboard loads but shows 0 for all stats
- No errors in console

**Causes:**
- Database is empty
- Backend not returning data
- API response parsing error

**Solutions:**

1. Check if database has data:
```bash
docker-compose exec -T db psql -U postgres -d news_db -c \
  "SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM articles;"
```

2. Test dashboard API directly:
```bash
TOKEN=<your-jwt-token>
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/admin-panel/dashboard | jq
```

3. Check browser console for JavaScript errors

---

#### 4. "Can't make myself admin"

**Symptoms:**
- New installation, no admin users
- Can't access admin panel
- Need to create first admin

**Solution:**

Use one of these methods to create your first admin:

**Method 1: Update existing user**
```bash
docker-compose exec -T backend python -c "
from app.database import engine
from sqlmodel import Session, select
from app.models import User

with Session(engine) as session:
    user = session.exec(
        select(User).where(User.email == 'your-email@example.com')
    ).first()
    if user:
        user.is_admin = True
        session.commit()
        print('Admin privileges granted!')
"
```

**Method 2: Create new admin user**
```bash
docker-compose exec -T backend python -c "
from app.database import engine
from sqlmodel import Session
from app.models import User
from app.utils.auth import hash_password

with Session(engine) as session:
    admin = User(
        email='admin@yourcompany.com',
        name='System Administrator',
        hashed_password=hash_password('ChangeThisPassword123!'),
        is_active=True,
        is_admin=True,
        email_verified=True
    )
    session.add(admin)
    session.commit()
    print('Admin user created!')
"
```

**Method 3: Direct SQL**
```bash
docker-compose exec -T db psql -U postgres -d news_db -c \
  "UPDATE users SET is_admin = true WHERE email = 'your-email@example.com';"
```

---

### Debug Mode

Enable detailed logging:

**Backend:** Set `DEBUG=True` in `backend/.env`

**Frontend:** Check browser console (F12)

**Database:** View query logs:
```bash
docker logs news_db --tail 100
```

---

## Appendix

### Environment Variables

**Backend** (`backend/.env`):
```bash
# Admin Configuration
ADMIN_TOKEN=<legacy-token>  # No longer required for admin panel
ADMIN_PANEL_ENABLED=true
MAX_AUDIT_LOG_DAYS=90
MAX_JOB_HISTORY_DAYS=30
```

### Database Indexes

For optimal admin panel performance, ensure these indexes exist:

```sql
CREATE INDEX idx_users_is_admin ON users(is_admin);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_admin_audit_timestamp ON admin_audit_log(timestamp);
CREATE INDEX idx_admin_audit_admin_email ON admin_audit_log(admin_email);
CREATE INDEX idx_job_history_started_at ON job_execution_history(started_at);
```

### Monitoring

Key metrics to monitor:
- Admin action count per hour
- Failed admin API calls
- Audit log growth rate
- Admin user count
- Average dashboard load time

---

## Support

For issues or questions:

1. Check this documentation
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system overview
3. Check [API.md](API.md) for API details
4. Search existing issues on GitHub
5. Create new issue with:
   - Description of problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs (backend, frontend console)
   - Environment (dev, staging, prod)

---

**Last Updated:** 2025-10-16
**Admin Panel Version:** 1.0
**Documentation Version:** 1.0
