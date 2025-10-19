# Account Deletion & Source Improvements Implementation Plan

**Created**: 2025-10-18
**Status**: Planning Phase
**Estimated Time**: 4-6 hours

---

## Overview

This plan covers three major improvements:
1. **Account Deletion** - Allow users to delete their accounts
2. **Contact Us Link** - Replace "Sign up" with "Contact us" on authenticated pages
3. **Source Management Improvements** - Add descriptions to all sources, make source details database-driven, and add endpoint to create sources from URLs

---

## Task Breakdown

### 1. Account Deletion Feature

#### Backend Changes

**1.1. Create DELETE endpoint** (`/backend/app/routes/auth.py`)
```python
@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete the authenticated user's account and all associated data.

    This is a destructive operation that:
    - Deletes user preferences (topics, sources, settings)
    - Deletes newsletters associated with user
    - Deletes the user account

    Returns 204 No Content on success
    """
    # Delete all user preferences
    # Delete all newsletters
    # Delete user account
    # Return 204
```

**Implementation steps:**
- Add endpoint to [auth.py](backend/app/routes/auth.py)
- Handle cascading deletes for user data:
  - UserTopicPreference
  - UserSourceSubscription
  - Newsletter (where user_id matches)
- Use transactions to ensure atomicity
- Return 204 No Content on success

**1.2. Write backend tests** (`/backend/tests/routes/test_auth.py`)
- Test successful account deletion
- Test that all related data is deleted
- Test that authentication is required
- Test that deleted user cannot log in

#### Frontend Changes

**1.3. Add Account Deletion UI** (`/frontend/src/app/preferences/page.tsx`)
- Add new "Account" tab to preferences page
- Create "Delete Account" section with:
  - Warning message about permanent deletion
  - Confirmation dialog (requires typing "DELETE" to confirm)
  - Delete button
- Handle API call to delete endpoint
- Redirect to landing page on success
- Clear local storage/cookies

**1.4. Write frontend tests**
- Test that delete button shows confirmation dialog
- Test that confirmation requires typing "DELETE"
- Test successful deletion flow
- Test error handling

---

### 2. Contact Us Link Feature

#### Frontend Changes

**2.1. Update Navbar component** (`/frontend/src/components/Navbar.tsx`)
- Add logic to detect if user is authenticated
- If authenticated, show "Contact us" link instead of "Sign up"
- Link should go to email: `mailto:support@pulse-news.com` (or appropriate email)

**2.2. Update landing page footer** (`/frontend/src/app/page.tsx`)
- Keep "Sign up" link on unauthenticated landing page
- This change only affects authenticated pages

**Implementation steps:**
- Modify Navbar.tsx to check authentication state
- Replace conditional rendering for "Sign up" button
- Add "Contact us" link with mailto: href
- Test in both authenticated and unauthenticated states

---

### 3. Source Management Improvements

#### Backend Changes

**3.1. Add description field migration**
- Check if `sources` table already has `description` field
- If not, create Alembic migration to add `description` column (TEXT, nullable)
- Update Source model in [models.py](backend/app/models.py) if needed

**3.2. Populate source descriptions**
- Create data migration or script to add descriptions for existing sources
- Sources to update (based on typical Pulse sources):
  - BBC News
  - CNN
  - The New York Times
  - The Guardian
  - Reuters
  - Associated Press
  - NPR
  - Al Jazeera
  - The Wall Street Journal
  - The Washington Post
  - Fox News
  - MSNBC
  - Bloomberg
  - Financial Times
  - Politico
  - The Hill
  - ProPublica
  - The Atlantic
  - The Economist
  - TechCrunch
  - Ars Technica
  - Wired
  - The Verge

**3.3. Create endpoint to add source by URL** (`/backend/app/routes/admin.py`)
```python
@router.post("/sources/from-url")
async def create_source_from_url(
    url: str,
    session: Session = Depends(get_session)
):
    """
    Create a new source by analyzing an RSS feed URL.

    This endpoint:
    1. Fetches the RSS feed from the URL
    2. Extracts source metadata (name, category)
    3. Uses AI to analyze source bias and credibility
    4. Creates source entry in database

    Args:
        url: RSS feed URL to analyze

    Returns:
        Created source object with analysis
    """
```

**Implementation steps:**
- Create new service: `source_analyzer.py` in `/backend/app/services/`
- Service should:
  - Fetch RSS feed from URL
  - Extract source name from feed metadata
  - Sample 5-10 recent articles
  - Use OpenAI to analyze source characteristics:
    - Political bias (left/center/right)
    - Credibility rating
    - Primary topics covered
    - Generate description blurb
  - Detect category based on topics
- Add endpoint to admin routes
- Require authentication (admin only if admin system exists)

**3.4. Update Sources API endpoint** (`/backend/app/routes/preferences.py`)
- Ensure GET `/sources` endpoint returns `description` field
- Add any missing fields needed for source cards

**3.5. Write backend tests**
- Test source analyzer service
- Test create source from URL endpoint
- Test that descriptions are returned in API

#### Frontend Changes

**3.6. Update Source cards to use API data** (`/frontend/src/app/preferences/page.tsx`)
- Remove any hardcoded source descriptions
- Use description field from API response
- Ensure all source card details come from database:
  - Name
  - Description
  - Category
  - RSS URL
  - Bias rating (if available)

**3.7. Create Source Management UI** (Optional - Admin only)
- Add ability to add source by URL through UI
- Could be part of admin panel or preferences for now
- Simple form with URL input and submit button

**3.8. Write frontend tests**
- Test that source cards display API data
- Test source creation UI if implemented

---

## Database Schema Changes

### Migration 1: Add description to sources table
```sql
ALTER TABLE sources ADD COLUMN description TEXT;
```

### Migration 2: Populate descriptions
```sql
UPDATE sources SET description = 'Blurb text' WHERE name = 'Source Name';
-- Repeat for all sources
```

---

## New Files to Create

### Backend
1. `/backend/app/services/source_analyzer.py` - Source analysis service
2. `/backend/tests/services/test_source_analyzer.py` - Tests for analyzer
3. `/backend/tests/routes/test_auth_delete.py` - Account deletion tests
4. `/backend/alembic/versions/XXXXX_add_source_descriptions.py` - Migration

### Frontend
1. `/frontend/src/app/preferences/__tests__/account-deletion.test.tsx` - Account deletion tests

---

## Files to Modify

### Backend
1. [backend/app/routes/auth.py](backend/app/routes/auth.py) - Add DELETE endpoint
2. [backend/app/routes/admin.py](backend/app/routes/admin.py) - Add source creation endpoint
3. [backend/app/models.py](backend/app/models.py) - Update Source model if needed
4. [backend/tests/routes/test_auth.py](backend/tests/routes/test_auth.py) - Add deletion tests

### Frontend
1. [frontend/src/components/Navbar.tsx](frontend/src/components/Navbar.tsx) - Contact us link
2. [frontend/src/app/preferences/page.tsx](frontend/src/app/preferences/page.tsx) - Account deletion UI, source cards
3. [frontend/src/lib/api.ts](frontend/src/lib/api.ts) - Add deleteAccount function
4. [frontend/src/app/preferences/__tests__/page.test.tsx](frontend/src/app/preferences/__tests__/page.test.tsx) - Update tests

---

## Implementation Order

### Phase 1: Database & Backend Core (2-3 hours)
1. Create and apply source description migration
2. Populate source descriptions
3. Create source_analyzer.py service
4. Add create source from URL endpoint
5. Add account deletion endpoint
6. Write backend tests

### Phase 2: Frontend Integration (1-2 hours)
7. Update Navbar with Contact us link
8. Add account deletion UI to preferences
9. Update source cards to use API data
10. Write frontend tests

### Phase 3: Testing & Refinement (1 hour)
11. Run all tests (backend + frontend)
12. Manual testing of all features
13. Fix any bugs
14. Update documentation

### Phase 4: Git Organization (30 min)
15. Organize changes into logical commits:
    - Commit 1: Add source descriptions to database
    - Commit 2: Create source analyzer service and endpoint
    - Commit 3: Add account deletion backend
    - Commit 4: Update Navbar with Contact us link
    - Commit 5: Add account deletion UI
    - Commit 6: Update source cards to use API data
    - Commit 7: Add tests for all new features

---

## Source Descriptions (Draft)

Here are suggested descriptions for common news sources:

- **BBC News**: "British public service broadcaster providing impartial international news coverage with a global perspective."
- **CNN**: "American cable news network offering breaking news, analysis, and commentary on domestic and international events."
- **The New York Times**: "Leading American newspaper known for in-depth investigative journalism and comprehensive global coverage."
- **The Guardian**: "British daily newspaper with progressive editorial stance, covering politics, culture, and world affairs."
- **Reuters**: "International news agency delivering fast, accurate, and unbiased reporting to media organizations worldwide."
- **Associated Press**: "Independent global news organization providing factual, nonpartisan reporting to thousands of outlets."
- **NPR**: "American public radio network offering in-depth news analysis, cultural programming, and investigative journalism."
- **Al Jazeera**: "Qatar-based media network providing news and analysis with focus on Middle East and Global South perspectives."
- **The Wall Street Journal**: "Business-focused newspaper offering financial news, analysis, and reporting on global markets."
- **The Washington Post**: "American newspaper known for political reporting, investigative journalism, and coverage of national affairs."
- **Fox News**: "American conservative cable news channel providing news and commentary on politics and current events."
- **MSNBC**: "American progressive cable news network offering news analysis and political commentary."
- **Bloomberg**: "Global financial news and data provider focusing on business, markets, and economic policy."
- **Financial Times**: "International daily newspaper with emphasis on business and economic news from a global perspective."
- **Politico**: "Political journalism company covering politics and policy with insider perspectives on government affairs."
- **The Hill**: "American political newspaper and website covering Congress, the White House, and political campaigns."
- **ProPublica**: "Independent nonprofit newsroom producing investigative journalism in the public interest."
- **The Atlantic**: "American magazine covering politics, culture, technology, and international affairs with long-form journalism."
- **The Economist**: "British weekly newspaper focusing on international politics, business, finance, and economics."
- **TechCrunch**: "Online publisher covering technology industry news, startups, and venture capital."
- **Ars Technica**: "Technology news website offering deep-dive analysis of tech policy, hardware, and software."
- **Wired**: "Magazine covering technology, science, culture, and their impact on politics and the economy."
- **The Verge**: "Technology news website covering consumer electronics, science, entertainment, and culture."

---

## API Changes Summary

### New Endpoints

**DELETE /auth/account**
- Deletes authenticated user's account
- Requires authentication
- Returns 204 No Content
- Cascades to delete user preferences and newsletters

**POST /admin/sources/from-url**
- Creates new source by analyzing RSS feed URL
- Requires authentication (admin)
- Request: `{"url": "https://example.com/rss"}`
- Response: Source object with analysis

### Modified Endpoints

**GET /sources**
- Now returns `description` field for each source
- All source details are database-driven

---

## Testing Checklist

### Backend Tests
- [ ] Account deletion removes user and all related data
- [ ] Account deletion requires authentication
- [ ] Deleted user cannot log in
- [ ] Source analyzer extracts metadata from RSS feed
- [ ] Source analyzer uses AI to generate description
- [ ] Create source endpoint creates valid source
- [ ] Sources endpoint returns descriptions

### Frontend Tests
- [ ] Contact us link appears when authenticated
- [ ] Sign up link appears when not authenticated
- [ ] Account deletion shows confirmation dialog
- [ ] Account deletion requires typing "DELETE"
- [ ] Account deletion redirects to landing page
- [ ] Source cards display API data correctly
- [ ] Source descriptions render properly

### Manual Testing
- [ ] Delete account flow works end-to-end
- [ ] Contact us link opens email client
- [ ] All source cards show descriptions
- [ ] Source creation from URL works
- [ ] No UI regressions on preferences page
- [ ] Dark mode support for new UI elements

---

## Security Considerations

1. **Account Deletion**
   - Ensure only authenticated user can delete their own account
   - Use transactions to prevent partial deletions
   - Consider soft delete vs hard delete (currently hard delete)
   - Log deletion events for audit trail

2. **Source Creation**
   - Validate RSS feed URLs before processing
   - Limit rate of source creation (prevent abuse)
   - Consider admin-only access
   - Sanitize source names and descriptions

3. **Contact Us**
   - Use mailto: link (no backend needed)
   - Could add contact form later for better security

---

## Documentation Updates

After implementation, update:
1. [CHANGELOG.md](../CHANGELOG.md) - Document all changes
2. [API.md](API.md) - Add new endpoints
3. [CLAUDE.md](../CLAUDE.md) - Update feature list
4. This plan document - Mark as complete

---

**Implementation Start**: TBD
**Implementation End**: TBD
**Total Commits**: ~7 logical commits
