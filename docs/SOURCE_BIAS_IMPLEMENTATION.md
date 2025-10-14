# Source Bias Implementation Plan

## Overview
Add organizational bias information to news sources and create a supported sources page.

## Goals
1. Add `organizational_bias` field to Source model
2. Create API endpoint to add sources with bias data
3. Integrate bias data API/scraper
4. Display source bias badges on feed and article pages
5. Create "Supported Sources" page with filtering

---

## Phase 1: Database & Model Updates

### 1.1 Update Source Model
**File**: `backend/app/models.py`

Add fields:
- `organizational_bias`: Optional enum ("left", "center-left", "center", "center-right", "right")
- `bias_description`: Optional text field (max 500 chars)

### 1.2 Create Alembic Migration
**Command**: `alembic revision --autogenerate -m "add_source_bias_fields"`

Fill in known values for existing sources:
- AP: center
- Reuters: center
- BBC: center-left
- NPR: center-left
- NYT: center-left
- Politico: center
- The Atlantic: center-left
- Ars Technica: center (TODO: research)

---

## Phase 2: Backend - Source Management API

### 2.1 Create Source Management Route
**File**: `backend/app/routes/sources.py` (NEW)

Endpoints:
- `GET /sources` - List all sources with bias info
- `POST /sources` - Add new source (admin only)
- `GET /sources/{source_id}` - Get source details
- `PUT /sources/{source_id}` - Update source
- `DELETE /sources/{source_id}` - Soft delete (set is_active=false)

### 2.2 Bias Data Integration
**File**: `backend/app/services/bias_data_fetcher.py` (NEW)

Research and integrate one of:
- AllSides Media Bias API
- Media Bias/Fact Check scraper
- Ad Fontes Media API

Function: `fetch_source_bias(domain: str) -> dict`
Returns: { "bias": str, "description": str, "confidence": float }

### 2.3 Update Existing Endpoints
Update these to include source bias:
- `/feed/sources` - Add organizational_bias field
- `/articles/{id}` - Include source bias in response
- `/preferences/sources` - Add organizational_bias field

---

## Phase 3: Frontend - Bias Badge Component

### 3.1 Create SourceBiasBadge Component
**File**: `frontend/src/components/SourceBiasBadge.tsx` (NEW)

Props:
- `bias`: "left" | "center-left" | "center" | "center-right" | "right"
- `size`: "sm" | "md" | "lg"
- `showLabel`: boolean

Color scheme:
- left: blue-600
- center-left: blue-400
- center: purple-600
- center-right: red-400
- right: red-600

### 3.2 Update Feed Page
**File**: `frontend/src/app/feed/page.tsx`

- Add source bias badge next to source name in article card header
- Update Article interface to include `source_bias`

### 3.3 Update Article Detail Page
**File**: `frontend/src/app/article/[id]/page.tsx`

- Add source bias badge next to source name in header
- Add "Article Bias:" label before article political_lean
- Update ArticleDetail interface to include `source_bias`

---

## Phase 4: Frontend - Supported Sources Page

### 4.1 Create Sources Page
**File**: `frontend/src/app/sources/page.tsx` (NEW)

Features:
- Display all sources in grid/card layout
- Show: name, URL, bias badge, trust score, article count, status
- Filter by bias (dropdown)
- Sort by: name, trust score, article count

### 4.2 Update API Client
**File**: `frontend/src/lib/api.ts`

Add methods:
- `getSources()` - Fetch all sources with bias
- `getSourceById(id)` - Get single source details

### 4.3 Update Navbar
**File**: `frontend/src/components/Navbar.tsx`

Add "Sources" link to navigation menu

---

## Phase 5: Testing

### 5.1 Backend Tests
**File**: `backend/tests/routes/test_sources.py` (NEW)

Test cases:
- List sources
- Create source with bias
- Update source bias
- Filter sources by bias

### 5.2 Frontend Tests
**File**: `frontend/src/components/__tests__/SourceBiasBadge.test.tsx` (NEW)

Test cases:
- Render all bias types correctly
- Color coding matches spec
- Size variants work

**File**: `frontend/src/app/sources/__tests__/page.test.tsx` (NEW)

Test cases:
- Sources load and display
- Filtering works
- Sorting works

---

## Implementation Order

1. ✅ Update Source model with bias fields
2. ✅ Create and run Alembic migration
3. ✅ Populate existing sources with bias data
4. ✅ Create `/sources` API endpoints
5. ✅ Integrate bias data API/scraper
6. ✅ Update existing endpoints to include bias
7. ✅ Create SourceBiasBadge component
8. ✅ Update feed page with badges
9. ✅ Update article detail page with badges
10. ✅ Create sources page
11. ✅ Update navbar
12. ✅ Write backend tests
13. ✅ Write frontend tests
14. ✅ Update CHANGELOG.md

---

## Notes

- Keep article-level `political_lean` separate from source-level `organizational_bias`
- Source bias is informational context; article analysis takes precedence
- All bias values should be nullable (some sources may not have bias ratings)
- Use consistent terminology: "organizational bias" in backend, "source bias" in UI
