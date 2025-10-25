# Navbar Reorganization Plan

**Created**: 2025-10-18
**Status**: Planning Phase

---

## Overview

Consolidate Analyze, Sources, and Analytics into a single "Insights" tab with subtabs, similar to the Preferences page pattern.

---

## Current Navbar Structure

```
Feed | Analyze | Sources | Analytics | Preferences | How It Works | Admin*
```

*Admin only visible to admin users

---

## Proposed Navbar Structure

```
Feed | Insights | Preferences | How It Works | Admin*
```

Where **Insights** contains three subtabs:
- **Analyze** - Article URL analysis tool
- **Sources** - Browse and manage news sources
- **Analytics** - View reading patterns and statistics

---

## Implementation Steps

### Phase 1: Create New Insights Page (30-45 min)

**1.1. Create page structure** (`/frontend/src/app/insights/page.tsx`)
- Create new Insights page with tab navigation
- Use same pattern as Preferences page (3-tab interface)
- Tabs: Analyze, Sources, Analytics
- URL-based tab switching: `/insights?tab=analyze|sources|analytics`

**1.2. Move existing page content**
- **Analyze tab**: Copy content from `/frontend/src/app/analyze/page.tsx`
- **Sources tab**: Copy content from `/frontend/src/app/sources/page.tsx`
- **Analytics tab**: Copy content from `/frontend/src/app/analytics/page.tsx`

**1.3. Handle tab state**
- Use `useSearchParams` to read `tab` query parameter
- Default to `analyze` tab if no tab specified
- Update URL when switching tabs
- Maintain scroll position behavior

### Phase 2: Update Navbar (10 min)

**2.1. Update navigation items** (`/frontend/src/components/Navbar.tsx`)
- Remove: Analyze, Sources, Analytics
- Add: Insights (single item)
- Update `navItems` array
- Path: `/insights`

**2.2. Update active state logic**
- Highlight Insights when on `/insights` route
- No need to check subtab (entire Insights tab is active when on that page)

### Phase 3: Add Redirects (10 min)

**3.1. Create redirect pages**
To maintain backward compatibility with existing links:
- `/frontend/src/app/analyze/page.tsx` → Redirect to `/insights?tab=analyze`
- `/frontend/src/app/sources/page.tsx` → Redirect to `/insights?tab=sources`
- `/frontend/src/app/analytics/page.tsx` → Redirect to `/insights?tab=analytics`

**3.2. Implement redirects**
```tsx
'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AnalyzeRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/insights?tab=analyze');
  }, [router]);
  return null;
}
```

### Phase 4: Update Tests (15-20 min)

**4.1. Move test files**
- Move or copy tests to `/frontend/src/app/insights/__tests__/`
- Update imports and paths
- Test all three tabs

**4.2. Update existing tests**
- Update any tests that navigate to `/analyze`, `/sources`, or `/analytics`
- Change to navigate to `/insights?tab=X` instead

### Phase 5: Update Internal Links (10 min)

**5.1. Search for internal links**
- Search codebase for links to `/analyze`, `/sources`, `/analytics`
- Update to use `/insights?tab=X` format
- Check README, docs, and any tutorial content

---

## File Changes Summary

### New Files
1. `/frontend/src/app/insights/page.tsx` - Main Insights page with tabs
2. `/frontend/src/app/insights/__tests__/page.test.tsx` - Tests for Insights page

### Modified Files
1. `/frontend/src/components/Navbar.tsx` - Update navigation items
2. `/frontend/src/app/analyze/page.tsx` - Convert to redirect
3. `/frontend/src/app/sources/page.tsx` - Convert to redirect
4. `/frontend/src/app/analytics/page.tsx` - Convert to redirect

### Optional Cleanup (Later)
- Could delete old page files after redirects are tested
- Could delete old test files after new tests pass

---

## Detailed Code Structure

### Insights Page Structure

```tsx
'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Navbar from '@/components/Navbar';

type InsightsTab = 'analyze' | 'sources' | 'analytics';

function InsightsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const getInitialTab = (): InsightsTab => {
    const tab = searchParams.get('tab');
    if (tab === 'analyze' || tab === 'sources' || tab === 'analytics') {
      return tab;
    }
    return 'analyze';
  };

  const [activeTab, setActiveTab] = useState<InsightsTab>(getInitialTab());

  // Update activeTab when URL changes
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'analyze' || tab === 'sources' || tab === 'analytics') {
      setActiveTab(tab);
    }
  }, [searchParams]);

  const handleTabChange = (tab: InsightsTab) => {
    setActiveTab(tab);
    router.push(`/insights?tab=${tab}`, { scroll: false });
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-foreground mb-6">Insights</h1>

        {/* Tab Navigation */}
        <div className="border-b border-border mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => handleTabChange('analyze')}
              className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'analyze'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Analyze
            </button>
            <button
              onClick={() => handleTabChange('sources')}
              className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'sources'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Sources
            </button>
            <button
              onClick={() => handleTabChange('analytics')}
              className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'analytics'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Analytics
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'analyze' && <AnalyzeTabContent />}
        {activeTab === 'sources' && <SourcesTabContent />}
        {activeTab === 'analytics' && <AnalyticsTabContent />}
      </div>
    </div>
  );
}

export default function InsightsPage() {
  return (
    <Suspense>
      <InsightsContent />
    </Suspense>
  );
}
```

---

## Benefits

1. **Cleaner Navigation**: Reduces navbar clutter (7 items → 4 items)
2. **Logical Grouping**: All data/analytics features in one place
3. **Consistent UX**: Matches Preferences page pattern
4. **Easier Discovery**: Users can explore related features via tabs
5. **Mobile-Friendly**: Fewer top-level nav items on small screens

---

## Risks & Mitigations

**Risk**: Users with bookmarks to old URLs
- **Mitigation**: Keep redirect pages indefinitely

**Risk**: Breaking existing tests
- **Mitigation**: Update tests incrementally, run full suite before committing

**Risk**: Confusion about where features moved
- **Mitigation**: Could add temporary "Moved to Insights" banner on old pages

---

## Testing Checklist

- [ ] All three tabs load correctly in Insights page
- [ ] Tab switching updates URL
- [ ] Direct navigation to `/insights?tab=X` works
- [ ] Redirects from old URLs work
- [ ] Navbar highlights Insights correctly
- [ ] Mobile menu works properly
- [ ] Dark mode styling correct on all tabs
- [ ] All functionality preserved (analyze, sources, analytics)
- [ ] Existing tests updated and passing
- [ ] New Insights page tests passing

---

## Timeline

- **Phase 1**: 30-45 minutes (Create Insights page)
- **Phase 2**: 10 minutes (Update Navbar)
- **Phase 3**: 10 minutes (Add redirects)
- **Phase 4**: 15-20 minutes (Update tests)
- **Phase 5**: 10 minutes (Update links)

**Total Estimated Time**: 75-95 minutes (~1.5 hours)

---

## Notes

- This is a non-breaking change thanks to redirects
- Can be implemented incrementally and tested at each phase
- Consider adding breadcrumbs later for better navigation
- Could add icons to tabs for visual clarity

---

**Status**: Ready for implementation
