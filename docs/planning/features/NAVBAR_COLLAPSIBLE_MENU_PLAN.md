# Navbar Collapsible Menu Implementation Plan

## Overview
Add a responsive collapsible menu to the Navbar component that appears when navigation tabs start overlapping due to reduced viewport width. The menu button will be positioned on the far left of the navbar.

---

## Current State Analysis

### Existing Navbar Component
- **Location**: [frontend/src/components/Navbar.tsx](../frontend/src/components/Navbar.tsx)
- **Current Features**:
  - Dynamic user name display
  - Active page highlighting
  - Logout functionality
  - Navigation tabs: Dashboard, Feed, Preferences, Analytics, Sources, How It Works
  - Fixed positioning at top of viewport

### Current Layout
```
[Logo/Title] [Tab1] [Tab2] [Tab3] ... [User Name] [Logout]
```

---

## Proposed Solution

### New Layout (Desktop - Normal Width)
```
[☰ Menu Button (hidden)] [Logo/Title] [Tab1] [Tab2] [Tab3] ... [User Name] [Logout]
```

### New Layout (Mobile/Narrow - Overlapping)
```
[☰ Menu Button] [Logo/Title] ... [User Name] [Logout]
(Hidden tabs appear in dropdown menu when button clicked)
```

---

## Technical Implementation

### 1. Responsive Behavior Strategy

**Approach**: Use CSS-based responsive design with JavaScript state management

**Breakpoint Strategy**:
- **Large screens (≥1024px)**: Show all tabs inline, hide menu button
- **Medium screens (768px-1023px)**: Show menu button, collapse some tabs
- **Small screens (<768px)**: Show menu button, collapse all navigation tabs

**Alternative**: Dynamic overflow detection using `ResizeObserver` (more complex but more precise)

### 2. Component Structure Changes

#### State Management
```typescript
const [isMenuOpen, setIsMenuOpen] = useState(false)
```

#### New UI Elements
1. **Menu Button** (far left)
   - Icon: Hamburger menu (☰) using lucide-react or heroicons
   - Position: Far left, before logo/title
   - Visibility: Hidden on large screens, visible on medium/small
   - Click handler: Toggle `isMenuOpen`

2. **Collapsible Menu Panel**
   - Type: Dropdown/slide-down panel
   - Position: Below navbar, full width or positioned under button
   - Contents: All navigation links (or subset based on screen size)
   - Animation: Smooth slide/fade transition
   - Click-outside-to-close behavior

#### Layout Structure
```tsx
<nav className="...">
  {/* Menu Button (far left) */}
  <button
    onClick={() => setIsMenuOpen(!isMenuOpen)}
    className="lg:hidden ..."
  >
    <MenuIcon />
  </button>

  {/* Logo/Title */}
  <div className="...">Pulse</div>

  {/* Desktop Navigation (hidden on mobile) */}
  <div className="hidden lg:flex ...">
    {navigationLinks.map(...)}
  </div>

  {/* User Info & Logout */}
  <div className="...">
    <span>Welcome, {userName}</span>
    <button onClick={handleLogout}>Logout</button>
  </div>

  {/* Mobile Menu Dropdown */}
  {isMenuOpen && (
    <div className="lg:hidden absolute ...">
      {navigationLinks.map(...)}
    </div>
  )}
</nav>
```

### 3. Styling Approach

**Tailwind CSS Classes**:
- `hidden lg:flex` - Hide on mobile, show as flex on large screens
- `lg:hidden` - Show on mobile, hide on large screens
- `absolute top-full left-0 w-full` - Dropdown positioning
- `transition-all duration-300` - Smooth animations

**Menu Button Position**:
```css
/* Ensure menu button is leftmost */
order: -1; /* Or flex order in parent */
```

**Dropdown Menu**:
```css
/* Slide-down animation */
@keyframes slideDown {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
```

### 4. Accessibility Considerations

- **ARIA attributes**:
  - `aria-expanded={isMenuOpen}` on menu button
  - `aria-label="Navigation menu"` on menu button
  - `aria-hidden={!isMenuOpen}` on dropdown panel

- **Keyboard navigation**:
  - `Escape` key closes menu
  - `Tab` key navigates through menu items
  - Focus trap when menu is open (optional)

- **Screen reader support**:
  - Proper semantic HTML (`<nav>`, `<button>`, `<ul>`, `<li>`)
  - Announce menu state changes

### 5. Click-Outside-to-Close Logic

```typescript
useEffect(() => {
  if (!isMenuOpen) return

  const handleClickOutside = (event: MouseEvent) => {
    const target = event.target as HTMLElement
    if (!target.closest('.mobile-menu-container')) {
      setIsMenuOpen(false)
    }
  }

  document.addEventListener('click', handleClickOutside)
  return () => document.removeEventListener('click', handleClickOutside)
}, [isMenuOpen])
```

---

## Implementation Steps

### Step 1: Update Navbar Component Structure
- [ ] Add state for `isMenuOpen`
- [ ] Install icon library if needed (`lucide-react` or use existing)
- [ ] Extract navigation links into a constant array
- [ ] Add menu button component

### Step 2: Implement Responsive Layout
- [ ] Add Tailwind responsive classes to hide/show elements
- [ ] Create mobile menu dropdown component
- [ ] Position menu button on far left using flexbox order
- [ ] Ensure logo/title comes after menu button

### Step 3: Add Interactivity
- [ ] Implement menu toggle handler
- [ ] Add click-outside-to-close logic
- [ ] Add keyboard event handlers (Escape key)
- [ ] Add smooth transitions/animations

### Step 4: Styling & Polish
- [ ] Style menu button (size, colors, hover states)
- [ ] Style dropdown menu (background, spacing, shadows)
- [ ] Add active page highlighting in mobile menu
- [ ] Ensure consistent styling with desktop nav

### Step 5: Accessibility
- [ ] Add ARIA attributes
- [ ] Test keyboard navigation
- [ ] Test with screen reader
- [ ] Ensure focus management

### Step 6: Testing
- [ ] Create/update component tests
- [ ] Test responsive behavior at different breakpoints
- [ ] Test menu open/close functionality
- [ ] Test click-outside-to-close
- [ ] Test keyboard navigation
- [ ] Visual regression testing

---

## File Changes Required

### Primary File
- **[frontend/src/components/Navbar.tsx](../frontend/src/components/Navbar.tsx)** - Main implementation

### Test File
- **[frontend/src/components/__tests__/Navbar.test.tsx](../frontend/src/components/__tests__/Navbar.test.tsx)** - Component tests (create if doesn't exist)

### Optional
- **[frontend/src/components/MobileMenu.tsx](../frontend/src/components/MobileMenu.tsx)** - Extracted mobile menu component (if complexity warrants separation)

---

## Design Decisions

### Menu Button Icon
**Choice**: Use `lucide-react` library
- **Pros**: Already common in React ecosystem, tree-shakeable, TypeScript support
- **Icons**: `Menu` (hamburger), `X` (close)

**Alternative**: Heroicons, custom SVG

### Menu Type
**Choice**: Dropdown panel (slides down from navbar)
- **Pros**: Simple, familiar pattern, doesn't block content
- **Cons**: Adds to page height when open

**Alternative**: Sidebar (slides in from left)
- **Pros**: Doesn't affect page layout
- **Cons**: More complex, requires overlay

### Breakpoints
**Choice**: Standard Tailwind breakpoints
- `lg:` (1024px) - Primary breakpoint for showing/hiding menu
- `md:` (768px) - Optional intermediate state

### Active Page Indicator
**Choice**: Maintain same styling as desktop (background color change)
- Ensures consistency across responsive states

---

## Edge Cases to Handle

1. **Menu open while resizing to desktop**: Close menu automatically
2. **Long user names**: Truncate or wrap gracefully
3. **Menu open with logout**: Close menu after logout redirect
4. **Multiple rapid clicks**: Debounce or use state transitions properly
5. **Focus management**: Return focus to menu button when closing menu

---

## Testing Strategy

### Unit Tests
```typescript
describe('Navbar Collapsible Menu', () => {
  it('shows menu button on mobile screens', () => {})
  it('hides menu button on desktop screens', () => {})
  it('toggles menu open/closed on button click', () => {})
  it('closes menu when clicking outside', () => {})
  it('closes menu when pressing Escape key', () => {})
  it('displays all navigation links in mobile menu', () => {})
  it('highlights active page in mobile menu', () => {})
  it('maintains accessibility attributes', () => {})
})
```

### Manual Testing Checklist
- [ ] Test on iPhone (Safari)
- [ ] Test on Android (Chrome)
- [ ] Test on tablet sizes
- [ ] Test on desktop at various widths
- [ ] Test with keyboard only
- [ ] Test with screen reader
- [ ] Test rapid interactions
- [ ] Test while navigating between pages

---

## Success Criteria

1. ✅ Menu button appears on screens <1024px width
2. ✅ Menu button is positioned on far left of navbar
3. ✅ Clicking menu button toggles dropdown menu
4. ✅ Dropdown menu contains all navigation links
5. ✅ Active page is highlighted in mobile menu
6. ✅ Menu closes when clicking outside
7. ✅ Menu closes when pressing Escape key
8. ✅ Desktop navigation remains unchanged on large screens
9. ✅ All accessibility requirements met
10. ✅ Tests pass with >90% coverage
11. ✅ Smooth animations and transitions
12. ✅ No visual glitches during responsive transitions

---

## Estimated Effort

- **Planning**: ✅ Complete
- **Implementation**: ~2-3 hours
- **Testing**: ~1 hour
- **Total**: ~3-4 hours

---

## Future Enhancements (Out of Scope)

- Slide-in sidebar variant
- Submenu support for nested navigation
- Customizable breakpoints via props
- Menu position options (left/right)
- Animated hamburger-to-X icon transformation

---

**Created**: 2025-10-18
**Status**: 📋 Planning Complete - Ready for Implementation
**Related Branch**: `frontend/navbar/collapsible-menu`
