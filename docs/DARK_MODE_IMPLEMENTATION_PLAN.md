# Dark Mode Implementation Plan

## Overview
Add a dark mode toggle to the preferences page that applies a cohesive dark theme across all pages in the Pulse application.

## Requirements
1. Toggle switch in preferences page header
2. Persistent theme preference (saved to user preferences)
3. Apply theme globally across all pages
4. Smooth transitions between themes
5. Accessible color contrast ratios
6. System preference detection (optional initial state)

## Implementation Strategy

### 1. Theme Management Architecture

**Option: Tailwind CSS Dark Mode + React Context**
- Use Tailwind's built-in dark mode support (`class` strategy)
- Create React Context for theme state management
- Persist preference in localStorage + backend user settings
- Apply `dark` class to `<html>` element

### 2. Implementation Steps

#### Step 1: Configure Tailwind Dark Mode
**File**: `frontend/tailwind.config.ts`
- Enable dark mode with `class` strategy
- Define dark mode color palette

#### Step 2: Create Theme Context & Provider
**File**: `frontend/src/contexts/ThemeContext.tsx`
- Create context with theme state (light/dark)
- Provide toggle function
- Handle localStorage persistence
- Sync with user preferences API
- Apply class to document root

#### Step 3: Add Theme Provider to App Layout
**File**: `frontend/src/app/layout.tsx`
- Wrap app with ThemeProvider
- Initialize theme from localStorage or system preference

#### Step 4: Update Backend API
**File**: `backend/app/routes/preferences.py`
- Add `theme_preference` field to user settings endpoint
- Store in database (may need migration)

**File**: `backend/app/models.py`
- Add `theme_preference` column to User model (if not using JSON settings field)
- OR add to existing settings JSON field

#### Step 5: Create Dark Mode Toggle Component
**File**: `frontend/src/components/DarkModeToggle.tsx`
- Create accessible toggle switch
- Use theme context for state
- Show sun/moon icons
- Smooth transition animations

#### Step 6: Add Toggle to Preferences Page
**File**: `frontend/src/app/preferences/page.tsx`
- Add DarkModeToggle to page header
- Position alongside "Preferences" heading

#### Step 7: Update All Components with Dark Mode Styles
Apply dark mode variants using Tailwind's `dark:` prefix to:
- `frontend/src/app/page.tsx` (Landing page)
- `frontend/src/app/login/page.tsx`
- `frontend/src/app/signup/page.tsx`
- `frontend/src/app/preferences/page.tsx`
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/app/feed/page.tsx`
- `frontend/src/app/article/[id]/page.tsx`
- `frontend/src/app/how-it-works/page.tsx`
- `frontend/src/components/Navbar.tsx`

#### Step 8: Update API Client
**File**: `frontend/src/lib/api.ts`
- Add methods for updating theme preference
- Integrate with existing preferences endpoints

#### Step 9: Write Tests
**File**: `frontend/src/contexts/__tests__/ThemeContext.test.tsx`
- Test theme toggle functionality
- Test localStorage persistence
- Test context provider

**File**: `frontend/src/components/__tests__/DarkModeToggle.test.tsx`
- Test toggle rendering
- Test click interactions
- Test accessibility

#### Step 10: Database Migration (if needed)
**File**: `backend/alembic/versions/XXXXX_add_theme_preference.py`
- Add theme_preference column to users table
- OR document use of existing settings JSON field

## Color Palette Strategy

### Light Mode (Current)
- Background: White (#FFFFFF)
- Text: Gray-900 (#111827)
- Primary: Blue-600 (#2563EB)
- Secondary: Gray-100 (#F3F4F6)
- Borders: Gray-200 (#E5E7EB)

### Dark Mode (New)
- Background: Gray-900 (#111827)
- Text: Gray-100 (#F3F4F6)
- Primary: Blue-500 (#3B82F6)
- Secondary: Gray-800 (#1F2937)
- Borders: Gray-700 (#374151)
- Cards: Gray-800 (#1F2937)

## Implementation Order

1. ✅ **Setup** (Step 1-2): Configure Tailwind + Create Theme Context
2. ✅ **Integration** (Step 3): Add provider to app layout
3. ✅ **Backend** (Step 4-5): Update API and models (if needed)
4. ✅ **UI Component** (Step 6-7): Create toggle and add to preferences
5. ✅ **Styling** (Step 8): Apply dark mode styles to all pages
6. ✅ **API Integration** (Step 9): Connect toggle to backend
7. ✅ **Testing** (Step 10): Write comprehensive tests
8. ✅ **Migration** (Step 11): Create database migration if needed

## Accessibility Considerations

- Maintain WCAG AA contrast ratios (4.5:1 for text)
- Use semantic toggle with proper ARIA labels
- Support keyboard navigation
- Respect `prefers-color-scheme` media query as initial state

## Success Criteria

- [ ] Toggle visible in preferences page header
- [ ] Theme persists across page navigation
- [ ] Theme persists across browser sessions
- [ ] All pages styled appropriately in both modes
- [ ] Smooth transitions between themes
- [ ] Theme preference saved to backend
- [ ] Tests passing for theme functionality
- [ ] No accessibility violations

## File Checklist

### New Files
- [ ] `frontend/src/contexts/ThemeContext.tsx`
- [ ] `frontend/src/components/DarkModeToggle.tsx`
- [ ] `frontend/src/contexts/__tests__/ThemeContext.test.tsx`
- [ ] `frontend/src/components/__tests__/DarkModeToggle.test.tsx`

### Modified Files
- [ ] `frontend/tailwind.config.ts`
- [ ] `frontend/src/app/layout.tsx`
- [ ] `frontend/src/app/page.tsx`
- [ ] `frontend/src/app/login/page.tsx`
- [ ] `frontend/src/app/signup/page.tsx`
- [ ] `frontend/src/app/preferences/page.tsx`
- [ ] `frontend/src/app/dashboard/page.tsx`
- [ ] `frontend/src/app/feed/page.tsx`
- [ ] `frontend/src/app/article/[id]/page.tsx`
- [ ] `frontend/src/app/how-it-works/page.tsx`
- [ ] `frontend/src/components/Navbar.tsx`
- [ ] `frontend/src/lib/api.ts`
- [ ] `backend/app/routes/preferences.py` (if needed)
- [ ] `backend/app/models.py` (if needed)

### Migration Files (if needed)
- [ ] `backend/alembic/versions/XXXXX_add_theme_preference.py`

## Notes

- Use Tailwind's `dark:` prefix for all dark mode styles
- Leverage CSS transitions for smooth theme switching
- Consider using `localStorage` as immediate persistence with backend sync
- Test on multiple browsers for consistent behavior
- Ensure charts (Recharts) also support dark mode styling

---

**Created**: 2025-10-16
**Status**: Ready for implementation
