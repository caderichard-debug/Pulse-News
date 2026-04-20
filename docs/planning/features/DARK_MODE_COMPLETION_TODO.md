# Dark Mode Completion TODO

## Current Status
✅ Dark mode infrastructure complete (ThemeContext, CSS variables, backend API)
✅ Navbar updated with dark mode styles
✅ Preferences page header updated
⚠️ **Only ~10% of components have dark mode styles applied**

## Remaining Work

### High Priority - User-Facing Pages

#### 1. Landing Page (`/`)
- [ ] Hero section background and text
- [ ] Feature cards
- [ ] Call-to-action buttons
- [ ] Footer

#### 2. Authentication Pages
- [ ] Login page (`/login`)
  - Form backgrounds
  - Input fields
  - Placeholder text visibility
  - Button styles
  - Error messages
- [ ] Signup page (`/signup`)
  - Step 1: User details form
  - Step 2: Topic selection cards
  - Progress indicators
  - Submit buttons
- [ ] Forgot password page (`/forgot-password`)
- [ ] Reset password page (`/reset-password`)
- [ ] Email verification page (`/verify-email`)

#### 3. Dashboard Page (`/dashboard`)
- [ ] Page background
- [ ] Stats cards (articles read, newsletters received, etc.)
- [ ] Chart containers
- [ ] Recharts components (sentiment line chart, bias area chart)
- [ ] Section headers
- [ ] Grid layouts

#### 4. Feed Page (`/feed`)
- [ ] Page background
- [ ] Filter controls
- [ ] Search input
- [ ] Article cards
  - Card backgrounds
  - Titles and text
  - Metadata (date, source, etc.)
  - Hover states
- [ ] Pagination controls
- [ ] Loading states

#### 5. Article Detail Page (`/article/[id]`)
- [ ] Page background
- [ ] Article header
- [ ] Content sections
- [ ] Analysis cards (sentiment, bias, frameworks)
- [ ] Statistics verification display
- [ ] Related articles section
- [ ] Back button

#### 6. Sources Page (`/sources`)
- [ ] Page background
- [ ] Source cards
- [ ] Filter/sort controls
- [ ] Source metadata displays
- [ ] Bias badges (already themed via SourceBiasBadge component)

#### 7. Analytics Page (`/analytics`)
- [ ] Page background
- [ ] Analytics cards
- [ ] Chart containers
- [ ] Recharts visualizations
- [ ] Time period selectors
- [ ] Metrics displays

#### 8. How It Works Page (`/how-it-works`)
- [ ] Page background
- [ ] Section cards
- [ ] Step indicators
- [ ] Feature explanations
- [ ] Diagrams/illustrations backgrounds

### Medium Priority - Preferences Page Tabs

#### 9. Preferences - Topics Tab (PARTIAL)
- [x] Header with toggle (DONE)
- [x] Background (DONE)
- [ ] Topic cards
  - Active state backgrounds
  - Inactive state backgrounds
  - Toggle switches
  - Borders
- [ ] Save button
- [ ] Success/error messages
- [ ] Summary card

#### 10. Preferences - Sources Tab
- [ ] Source grid cards
  - Selected state
  - Unselected state
  - Hover effects
- [ ] Checkboxes
- [ ] Source metadata text
- [ ] Trust score displays
- [ ] Save button

#### 11. Preferences - Settings Tab
- [ ] Form backgrounds
- [ ] Select dropdowns
  - Background colors
  - Border colors
  - Option text
- [ ] Slider (articles per topic)
  - Track color
  - Thumb color
  - Labels
- [ ] Help text
- [ ] Save button

#### 12. Preferences - Account Tab
- [ ] Form inputs
  - Name field
  - Email field (disabled state)
  - Background colors
  - Border colors
- [ ] Section dividers
- [ ] Security section
- [ ] Change password button
- [ ] Save button

### Low Priority - Admin Pages

#### 13. Admin Dashboard (`/admin`)
- [ ] Main dashboard background
- [ ] Stats cards
- [ ] Quick action buttons

#### 14. Admin - Users (`/admin/users`)
- [ ] User table
- [ ] Table headers
- [ ] Table rows (alternating)
- [ ] Action buttons

#### 15. Admin - Articles (`/admin/articles`)
- [ ] Article table
- [ ] Filters
- [ ] Status badges

#### 16. Admin - Sources (`/admin/sources`)
- [ ] Source table
- [ ] Add source form
- [ ] Edit controls

#### 17. Admin - Jobs (`/admin/jobs`)
- [ ] Job status displays
- [ ] Trigger buttons
- [ ] Job history table

#### 18. Admin - Database (`/admin/database`)
- [ ] Table list
- [ ] Database stats
- [ ] Management controls

#### 19. Admin - API (`/admin/api`)
- [ ] API endpoint list
- [ ] Documentation display

#### 20. Admin - Audit (`/admin/audit`)
- [ ] Audit log table
- [ ] Filter controls
- [ ] Timestamp displays

### Shared Components

#### 21. UnverifiedEmailAlert
- [ ] Alert background
- [ ] Alert text
- [ ] Alert border
- [ ] Close button

#### 22. Loading States
- [ ] Spinner colors
- [ ] Loading text
- [ ] Skeleton screens (if any)

#### 23. Error States
- [ ] Error message backgrounds
- [ ] Error text colors
- [ ] Error borders

#### 24. Modals/Dialogs
- [ ] Modal backgrounds
- [ ] Modal overlays
- [ ] Modal borders
- [ ] Close buttons

## Implementation Strategy

### Approach 1: Systematic Page-by-Page (RECOMMENDED)
1. Start with high-traffic pages (landing, auth, dashboard, feed)
2. Test each page after updating
3. Verify all interactive states (hover, focus, active)
4. Check accessibility (contrast ratios)

### Approach 2: Color Class Replacement
1. Create a mapping of old classes to new theme-aware classes
2. Use find-replace for common patterns:
   - `bg-white` → `bg-card`
   - `bg-gray-50` → `bg-background`
   - `text-gray-900` → `text-foreground`
   - `text-gray-600` → `text-muted-foreground`
   - `border-gray-200` → `border-border`
   - `bg-indigo-600` → `bg-primary`
   - `hover:bg-indigo-700` → `hover:bg-primary-hover`

### Approach 3: Component Library
1. Create dark-mode-aware variants of common components:
   - Card component
   - Button component
   - Input component
   - Badge component
2. Replace existing usage with these components

## Color Mapping Reference

### Backgrounds
- `bg-white` → `bg-card` (for card backgrounds)
- `bg-gray-50` → `bg-background` (for page backgrounds)
- `bg-gray-100` → `bg-secondary` or `bg-accent`
- `bg-gray-200` → `bg-muted`

### Text
- `text-gray-900` → `text-foreground` (primary text)
- `text-gray-800` → `text-foreground`
- `text-gray-700` → `text-card-foreground`
- `text-gray-600` → `text-muted-foreground` (secondary text)
- `text-gray-500` → `text-muted-foreground`

### Borders
- `border-gray-200` → `border-border`
- `border-gray-300` → `border-border`

### Primary Colors (keep specific for branding)
- `bg-indigo-600` → `bg-primary`
- `text-indigo-600` → `text-primary`
- `hover:bg-indigo-700` → `hover:bg-primary-hover`

### Special Cases
- Keep error colors: `bg-red-50`, `text-red-800`, etc. but add dark variants
- Keep success colors: `bg-green-50`, `text-green-800`, etc. but add dark variants
- Keep warning colors: `bg-yellow-50`, `text-yellow-800`, etc. but add dark variants

## Testing Checklist

For each page/component updated:
- [ ] Light mode looks correct
- [ ] Dark mode looks correct
- [ ] Transitions are smooth
- [ ] Text is readable (sufficient contrast)
- [ ] Hover states work in both modes
- [ ] Focus states are visible
- [ ] Active states are clear
- [ ] No flash of unstyled content (FOUC)

## Recharts Dark Mode

Special attention needed for charts (Dashboard, Analytics):
- Update Recharts theme colors
- Change axis colors
- Update tooltip backgrounds
- Adjust legend text colors
- Update grid line colors

Example pattern:
```tsx
<LineChart>
  <CartesianGrid
    strokeDasharray="3 3"
    className="stroke-border"
  />
  <XAxis
    className="text-muted-foreground"
    stroke="var(--muted-foreground)"
  />
  <YAxis
    className="text-muted-foreground"
    stroke="var(--muted-foreground)"
  />
  <Tooltip
    contentStyle={{
      backgroundColor: 'var(--card)',
      border: '1px solid var(--border)',
      color: 'var(--foreground)'
    }}
  />
</LineChart>
```

## Estimated Time

- High Priority Pages: ~4-6 hours
- Preferences Tabs: ~2-3 hours
- Admin Pages: ~3-4 hours
- Shared Components: ~1 hour
- Testing & Polish: ~2 hours

**Total: 12-16 hours**

## Priority Order

1. Landing page (first impression)
2. Auth pages (login, signup)
3. Dashboard (main user page)
4. Feed (high usage)
5. Article detail (high usage)
6. Preferences tabs (where toggle is)
7. Analytics
8. Sources
9. How It Works
10. Admin pages (last priority)

---

**Status**: Ready to implement
**Created**: 2025-10-17 05:45
