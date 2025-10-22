# NextAuth.js Integration with Google OAuth Sign-In

## Overview

This guide provides step-by-step instructions for integrating NextAuth.js with Google OAuth provider in the Pulse news aggregator platform, enhancing the existing custom JWT authentication system.

## Current Architecture Analysis

**Current Setup:**
- Backend: FastAPI with custom JWT authentication (`/auth/routes/auth.py`)
- Frontend: Next.js 15.5.4 with manual token management (`/lib/api.ts`)
- Database: PostgreSQL with `users` table supporting email/password authentication
- Email verification system in place

**Target Setup:**
- Backend: Enhanced FastAPI with OAuth user support
- Frontend: NextAuth.js for session management
- OAuth Provider: Google only
- Hybrid approach: OAuth + existing email/password option

## Prerequisites

### Required API Keys & Credentials

#### 1. Google OAuth 2.0 Credentials
- **Google Cloud Console**: https://console.cloud.google.com/
- **Required items:**
  - Client ID
  - Client Secret
  - Authorized redirect URIs

#### 2. Environment Variables
```bash
# NextAuth.js Configuration (uses existing Pulse environment variables)
NEXTAUTH_URL=FRONTEND_URL  # From backend/.env - e.g., http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret-key

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Existing Pulse URLs (from backend/.env)
FRONTEND_URL=http://localhost:3000
FRONTEND_CUSTOM_URL=your-custom-domain.com  # Optional
BACKEND_URL=http://localhost:8000
```

**OAuth Configuration Notes:**
- **Email Verification**: OAuth users skip email verification (trust provider)
- **Account Linking**: Users can link Google OAuth to existing email accounts
- **Domain Flexibility**: Uses existing FRONTEND_URL and FRONTEND_CUSTOM_URL from Pulse config
- **Mobile App**: Future consideration - OAuth provider configured for mobile redirects

## Implementation Plan

### Phase 1: Backend Enhancements (FastAPI)

#### 1.1 Database Schema Updates
**File: `backend/app/models.py`**

Add OAuth fields to User model:
```python
# Add to User class after the existing fields
oauth_provider: Optional[str] = Field(default=None, max_length=50)  # 'google', 'apple'
oauth_provider_id: Optional[str] = Field(default=None, max_length=255)  # Provider-specific user ID
oauth_provider_data: Optional[str] = Field(default=None, max_length=2000)  # JSON string with provider data
oauth_avatar_url: Optional[str] = Field(default=None, max_length=500)
passwordless_login_enabled: bool = Field(default=False)
```

Create OAuth account linking table:
```python
class OAuthAccount(SQLModel, table=True):
    __tablename__ = "oauth_accounts"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    provider: str = Field(max_length=50)  # 'google', 'apple'
    provider_user_id: str = Field(max_length=255)
    provider_data: Optional[str] = Field(default=None, max_length=2000)  # JSON
    access_token: Optional[str] = Field(default=None, max_length=1000)
    refresh_token: Optional[str] = Field(default=None, max_length=1000)
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 1.2 Create OAuth Authentication Service
**File: `backend/app/services/oauth_service.py`**

Implement OAuth user management:
```python
from sqlmodel import Session, select
from ..models import User, OAuthAccount
import json
from typing import Optional, Dict, Any

class OAuthService:
    def __init__(self, session: Session):
        self.session = session

    def find_or_create_oauth_user(
        self,
        provider: str,
        provider_user_id: str,
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None
    ) -> User:
        # Implementation for finding/creating OAuth users
        pass

    def link_oauth_account(self, user_id: int, provider: str, account_data: Dict[str, Any]):
        # Implementation for linking OAuth accounts to existing users
        pass

    def update_oauth_tokens(self, user_id: int, provider: str, tokens: Dict[str, Any]):
        # Implementation for updating OAuth tokens
        pass
```

#### 1.3 Add OAuth Authentication Routes
**File: `backend/app/routes/oauth.py`**

Create OAuth-specific endpoints:
```python
from fastapi import APIRouter, Depends, HTTPException
from ..database import get_session
from ..services.oauth_service import OAuthService
from ..utils.auth import create_access_token
from sqlmodel import Session

router = APIRouter(prefix="/auth/oauth", tags=["oauth authentication"])

@router.post("/google")
async def google_oauth_login(
    google_data: dict,
    session: Session = Depends(get_session)
):
    # Handle Google OAuth callback
    pass

@router.post("/apple")
async def apple_oauth_login(
    apple_data: dict,
    session: Session = Depends(get_session)
):
    # Handle Apple OAuth callback
    pass

@router.post("/link/{provider}")
async def link_oauth_account(
    provider: str,
    oauth_data: dict,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Link OAuth account to existing user
    pass

@router.delete("/unlink/{provider}")
async def unlink_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Unlink OAuth account
    pass
```

### Phase 2: Frontend NextAuth.js Setup

#### 2.1 Install Dependencies
```bash
cd frontend
npm install next-auth @auth/prisma-adapter
```

#### 2.2 Create NextAuth Configuration
**File: `frontend/src/pages/api/auth/[...nextauth].ts`**

```typescript
import NextAuth from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import AppleProvider from 'next-auth/providers/apple'
import { api } from '@/lib/api'

export default NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    AppleProvider({
      clientId: process.env.APPLE_CLIENT_ID!,
      clientSecret: process.env.APPLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      // Custom sign-in logic to sync with FastAPI backend
      try {
        const response = await api.post('/auth/oauth/' + account?.provider, {
          provider: account?.provider,
          providerAccountId: account?.providerAccountId,
          user: {
            email: user.email,
            name: user.name,
            image: user.image,
          },
          account: account,
        })

        // Store backend token for API calls
        if (response.access_token) {
          api.setToken(response.access_token)
        }

        return true
      } catch (error) {
        console.error('OAuth sign-in error:', error)
        return false
      }
    },
    async jwt({ token, user, account }) {
      // Custom JWT logic
      return token
    },
    async session({ session, token }) {
      // Custom session logic
      return session
    },
  },
  pages: {
    signIn: '/login',
    signUp: '/signup',
  },
})
```

#### 2.3 Create Auth Context Provider
**File: `frontend/src/contexts/AuthContext.tsx`**

```typescript
'use client'

import { SessionProvider } from 'next-auth/react'
import { ReactNode } from 'react'

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <SessionProvider>
      {children}
    </SessionProvider>
  )
}
```

#### 2.4 Update App Root Component
**File: `frontend/src/app/layout.tsx`**

```typescript
import { AuthProvider } from '@/contexts/AuthContext'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  )
}
```

### Phase 3: Update Authentication UI

#### 3.1 Enhance Login Page
**File: `frontend/src/app/login/page.tsx`**

Add OAuth buttons to existing login form:

```typescript
'use client'

import { signIn, getSession } from 'next-auth/react'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import BrandCard from '@/components/BrandCard'

export default function LoginPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleOAuthSignIn = async (provider: 'google' | 'apple') => {
    setLoading(true)
    setError('')

    try {
      const result = await signIn(provider, {
        redirect: false,
      })

      if (result?.error) {
        setError(`${provider} sign-in failed: ${result.error}`)
      } else {
        // Successfully signed in, redirect to feed
        router.push('/feed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `${provider} sign-in failed`)
    } finally {
      setLoading(false)
    }
  }

  // ... existing email/password login logic ...

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 dark:from-gray-900 to-indigo-100 dark:to-gray-800 transition-colors flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-card rounded-lg shadow-xl flex-grow p-8">
        <div className="flex flex-col items-center mb-8">
          <BrandCard size="large" />
          <h2 className="text-muted-foreground mt-2 text-xl">Welcome back</h2>
        </div>

        {/* OAuth Sign-In Buttons */}
        <div className="space-y-3 mb-6">
          <button
            onClick={() => handleOAuthSignIn('google')}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              {/* Google SVG icon */}
            </svg>
            Continue with Google
          </button>

          <button
            onClick={() => handleOAuthSignIn('apple')}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              {/* Apple SVG icon */}
            </svg>
            Continue with Apple
          </button>
        </div>

        {/* Divider */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-card text-muted-foreground">Or continue with email</span>
          </div>
        </div>

        {/* Existing email/password form */}
        {/* ... keep existing form code ... */}
      </div>
    </div>
  )
}
```

#### 3.2 Update Sign-Up Page
**File: `frontend/src/app/signup/page.tsx`**

Similar OAuth integration with social sign-up options.

#### 3.3 Create Account Settings Page
**File: `frontend/src/app/settings/account/page.tsx`**

Allow users to link/unlink OAuth accounts:

```typescript
'use client'

import { useSession, signOut } from 'next-auth/react'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

export default function AccountSettingsPage() {
  const { data: session } = useSession()
  const [linkedAccounts, setLinkedAccounts] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleLinkOAuth = async (provider: 'google' | 'apple') => {
    // Implement OAuth account linking
  }

  const handleUnlinkOAuth = async (provider: string) => {
    // Implement OAuth account unlinking
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Account Settings</h1>

      {/* Linked Accounts Section */}
      <div className="bg-card p-6 rounded-lg border">
        <h2 className="text-lg font-semibold mb-4">Linked Accounts</h2>

        <div className="space-y-3">
          {/* Display linked OAuth accounts */}
          {/* Add link/unlink buttons */}
        </div>
      </div>
    </div>
  )
}
```

### Phase 4: Database Migration

#### 4.1 Create Alembic Migration
**File: `backend/alembic/versions/XXXX_add_oauth_fields.py`**

**🚨 CRITICAL: Local-Container Parity Requirements**

Your Pulse project requires strict local-container parity. After creating ANY migration in the container, you MUST immediately sync it to the local filesystem:

```bash
# 1. Create migration in container
docker-compose exec backend alembic revision --autogenerate -m "Add OAuth support to users table"

# 2. IMMEDIATELY copy to local filesystem (required for deployment)
docker cp news_backend:/app/alembic/versions/XXXX_add_oauth_fields.py backend/alembic/versions/

# 3. Apply migration in container
docker-compose exec backend alembic upgrade head

# 4. Verify parity with local
ls backend/alembic/versions/ | grep XXXX_add_oauth_fields.py
```

**Use the sync script for automated parity:**
```bash
./scripts/sync-local-container.sh --check-migrations
```

**Migration File:**

```python
"""Add OAuth support to users table

Revision ID: XXXX
Revises: previous_revision
Create Date: YYYY-MM-DD HH:MM:SS.ssssss

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'XXXX'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Add OAuth columns to users table
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_data', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('oauth_avatar_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('passwordless_login_enabled', sa.Boolean(), nullable=True, default=False))

    # Create oauth_accounts table
    op.create_table('oauth_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_user_id', sa.String(length=255), nullable=False),
        sa.Column('provider_data', sa.Text(), nullable=True),
        sa.Column('access_token', sa.String(length=1000), nullable=True),
        sa.Column('refresh_token', sa.String(length=1000), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_accounts_provider'), 'oauth_accounts', ['provider'], unique=False)

def downgrade():
    # Remove OAuth columns from users table
    op.drop_column('users', 'passwordless_login_enabled')
    op.drop_column('users', 'oauth_avatar_url')
    op.drop_column('users', 'oauth_provider_data')
    op.drop_column('users', 'oauth_provider_id')
    op.drop_column('users', 'oauth_provider')

    # Drop oauth_accounts table
    op.drop_index(op.f('ix_oauth_accounts_provider'), table_name='oauth_accounts')
    op.drop_table('oauth_accounts')
```

### Phase 5: Testing & Validation

#### 5.1 Backend Tests
**File: `backend/tests/test_oauth.py`**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_google_oauth_login():
    # Test Google OAuth endpoint
    pass

def test_apple_oauth_login():
    # Test Apple OAuth endpoint
    pass

def test_oauth_account_linking():
    # Test OAuth account linking
    pass
```

#### 5.2 Frontend Tests
**File: `frontend/src/__tests__/oauth.test.tsx`**

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SessionProvider } from 'next-auth/react'
import LoginPage from '@/app/login/page'

describe('OAuth Authentication', () => {
  test('Google sign-in button renders and is clickable', () => {
    // Test Google OAuth button
  })

  test('Apple sign-in button renders and is clickable', () => {
    // Test Apple OAuth button
  })
})
```

## Security Considerations

### 1. OAuth Token Security
- Store OAuth tokens securely in database
- Implement token refresh mechanisms
- Use HTTPS for all OAuth communications

### 2. Account Linking Security
- Verify user owns existing email account before linking
- Implement account unlinking confirmation
- Prevent account takeover attacks

### 3. Session Management
- Secure NextAuth.js session configuration
- Implement proper logout flows
- Handle session expiration gracefully

## Environment Configuration

### Development Environment
```bash
# .env.local (frontend)
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-key
GOOGLE_CLIENT_ID=your-dev-google-client-id
GOOGLE_CLIENT_SECRET=your-dev-google-client-secret
APPLE_CLIENT_ID=your-dev-apple-client-id
APPLE_CLIENT_SECRET=your-dev-apple-client-secret
```

### Production Environment
```bash
# .env.production (frontend)
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=your-production-secret-key
GOOGLE_CLIENT_ID=your-prod-google-client-id
GOOGLE_CLIENT_SECRET=your-prod-google-client-secret
APPLE_CLIENT_ID=your-prod-apple-client-id
APPLE_CLIENT_SECRET=your-prod-apple-client-secret
```

## Deployment Considerations

### 1. Database Migration
- Run Alembic migration in production
- Backup database before migration
- Test migration in staging first

### 2. Environment Variables
- Configure OAuth callbacks in production
- Update allowed redirect URIs
- Set secure NextAuth.js secret

### 3. SSL/HTTPS
- Required for OAuth in production
- Configure SSL certificates
- Update OAuth provider configurations

## Troubleshooting

### Common Issues

1. **Google OAuth Redirect Mismatch**
   - Ensure `NEXTAUTH_URL` matches authorized redirect URIs
   - Check Google Cloud Console OAuth settings

2. **Apple Sign In Private Key Issues**
   - Verify .p8 file format and permissions
   - Check Apple Developer Portal configuration

3. **Database Migration Errors**
   - Check database connection during migration
   - Verify Alembic configuration

4. **Session Persistence Issues**
   - Verify NextAuth.js secret configuration
   - Check database session storage setup

### Debug Mode
Enable debug logging:
```typescript
// In [...nextauth].ts
export default NextAuth({
  debug: process.env.NODE_ENV === 'development',
  // ... rest of configuration
})
```

## Rollback Plan

If issues arise during deployment:

1. **Frontend Rollback**
   - Revert to previous commit without OAuth
   - Redeploy frontend

2. **Backend Rollback**
   - Run downgrade Alembic migration
   - Restore previous backend code

3. **OAuth Provider Rollback**
   - Disable OAuth providers in console
   - Revert OAuth app configurations

## Development Workflow & Commit Guidelines

### 🔄 Structured Commit Requirements

This is a **multi-phase implementation** that requires structured, atomic commits. Each phase should be committed with clear, descriptive messages.

#### Commit Structure Pattern:
```bash
# Feature commits
feat(auth): add OAuth database schema migration
feat(auth): implement Google OAuth backend service
feat(auth): configure NextAuth.js with Google provider
feat(ui): add Google sign-in button to login page
feat(tests): add OAuth integration tests

# Bug fix commits
fix(auth): resolve OAuth token storage issue
fix(ui): fix Apple sign-in button alignment

# Infrastructure commits
chore(deps): add next-auth dependency
chore(migration): sync local-container OAuth migration
```

#### Commit Examples for This Implementation:

```bash
# Phase 1 - Backend Setup
git add backend/app/models.py
git commit -m "feat(auth): add OAuth fields to User model

- Add oauth_provider, oauth_provider_id, oauth_provider_data fields
- Add oauth_avatar_url and passwordless_login_enabled fields
- Maintain backward compatibility with existing users
- Fixes: #oauth-integration"

git add backend/app/services/oauth_service.py
git commit -m "feat(auth): implement OAuth service for user management

- Add OAuthService class for provider authentication
- Implement find_or_create_oauth_user method
- Add account linking and token management
- Supports Google and Apple OAuth providers
- Fixes: #oauth-integration"

git add backend/app/routes/oauth.py
git commit -m "feat(auth): add OAuth authentication endpoints

- Add /auth/oauth/google endpoint
- Add /auth/oauth/apple endpoint
- Add OAuth account linking endpoints
- Implement proper error handling and validation
- Fixes: #oauth-integration"

# Phase 2 - NextAuth.js Setup
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(deps): add NextAuth.js dependencies

- Add next-auth for session management
- Add @auth/prisma-adapter for future database sessions
- Prepare for OAuth provider integration
- Fixes: #oauth-integration"

git add frontend/src/pages/api/auth/[...nextauth].ts
git commit -m "feat(auth): configure NextAuth.js with OAuth providers

- Configure Google and Apple OAuth providers
- Add custom signIn callback for FastAPI backend sync
- Implement JWT and session callbacks
- Add error handling for OAuth failures
- Fixes: #oauth-integration"

# Phase 3 - UI Updates
git add frontend/src/app/login/page.tsx
git commit -m "feat(ui): add OAuth sign-in buttons to login page

- Add Google and Apple sign-in buttons
- Maintain existing email/password form
- Add loading states and error handling
- Implement OAuth flow integration
- Fixes: #oauth-integration"

git add frontend/src/app/signup/page.tsx
git commit -m "feat(ui): add OAuth sign-up options

- Add Google and Apple sign-up buttons
- Preserve existing two-step registration flow
- Add OAuth user data handling
- Maintain topic selection for OAuth users
- Fixes: #oauth-integration"

# Phase 4 - Database Migration
git add backend/alembic/versions/XXXX_add_oauth_fields.py
git commit -m "feat(migration): add OAuth support database migration

- Add OAuth columns to users table
- Create oauth_accounts table for token management
- Implement proper foreign key constraints
- Add indexes for OAuth provider lookups
- Local-container parity verified
- Fixes: #oauth-integration"

# Phase 5 - Testing
git add backend/tests/test_oauth.py
git commit -m "feat(tests): add OAuth backend integration tests

- Test Google OAuth endpoint functionality
- Test Apple OAuth endpoint functionality
- Test OAuth account linking/unlinking
- Add OAuth user creation and lookup tests
- Fixes: #oauth-integration"

git add frontend/src/__tests__/oauth.test.tsx
git commit -m "feat(tests): add OAuth frontend component tests

- Test Google sign-in button rendering and interaction
- Test Apple sign-in button functionality
- Test OAuth error handling and loading states
- Test session management after OAuth sign-in
- Fixes: #oauth-integration"
```

### 📋 Pre-Commit Checklist

Before each commit, verify:

- [ ] Code follows existing Pulse project conventions
- [ ] All OAuth environment variables documented
- [ ] Database migrations synced between container and local
- [ ] Tests pass for the specific feature being committed
- [ ] No hardcoded credentials or secrets
- [ ] Error handling implemented for OAuth failures
- [ ] UI components support both light and dark modes
- [ ] API endpoints include proper validation
- [ ] Commit message follows conventional commit format

### 🔄 Branch Strategy

```bash
# Create feature branch
git checkout -b feature/oauth-integration

# Work through phases, committing each one
# ... (implement Phase 1)
git commit -m "feat(auth): add OAuth database schema migration"

# ... (implement Phase 2)
git commit -m "feat(auth): configure NextAuth.js with OAuth providers"

# Push branch for review (NEVER push to main without approval)
git push origin feature/oauth-integration

# Create pull request for review
# Get approval before merging to main
```

### 🚨 Critical Rule: NEVER Auto-Push

**DO NOT automatically push commits to remote.** Always wait for explicit user approval before pushing any changes to the remote repository.

## Timeline Estimate

- **Phase 1 (Backend)**: 2-3 days (6-9 structured commits)
- **Phase 2 (NextAuth.js Setup)**: 1-2 days (3-4 structured commits)
- **Phase 3 (UI Updates)**: 2-3 days (4-5 structured commits)
- **Phase 4 (Migration)**: 1 day (1-2 structured commits, includes local-container sync)
- **Phase 5 (Testing)**: 2-3 days (3-4 structured commits)
- **Total**: 8-12 days (17-24 structured commits)

## Success Criteria

1. ✅ Users can sign up/in with Google OAuth
2. ✅ Users can sign up/in with Apple Sign In
3. ✅ Existing email/password users remain functional
4. ✅ Users can link/unlink OAuth accounts
5. ✅ All OAuth tokens stored securely
6. ✅ Session management works correctly
7. ✅ Mobile OAuth flows work properly
8. ✅ All existing tests pass
9. ✅ New OAuth tests pass
10. ✅ Production deployment successful