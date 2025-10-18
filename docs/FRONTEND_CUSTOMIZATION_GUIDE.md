# Frontend Customization Guide

> **Complete guide to customizing Pulse's look and feel**
>
> This document explains how to change colors, fonts, spacing, animations, and other visual aspects of the Pulse news aggregator frontend.

---

## Table of Contents

1. [Color Palette Customization](#color-palette-customization)
2. [Typography & Fonts](#typography--fonts)
3. [Spacing & Layout](#spacing--layout)
4. [Animations & Transitions](#animations--transitions)
5. [Component-Specific Styling](#component-specific-styling)
6. [Advanced Customization](#advanced-customization)

---

## Color Palette Customization

### Overview

Pulse uses a **CSS variable-based theming system** defined in `frontend/src/app/globals.css`. This allows you to change the entire site's color palette by editing a single file.

### Color System Architecture

The color system has three layers:

1. **CSS Custom Properties** (`:root` variables) - Define colors
2. **Tailwind Theme Extension** (`@theme` directive) - Map variables to Tailwind
3. **Utility Classes** (`@layer utilities`) - Pre-built classes for common patterns

### Where to Edit Colors

**File:** [frontend/src/app/globals.css](../frontend/src/app/globals.css)

### Step-by-Step: Changing the Color Palette

#### 1. Update Light Mode Colors

Edit the `:root` block (lines 7-20):

```css
/* Light mode (default) */
:root {
  --background: #ffffff;        /* Page background */
  --foreground: #111827;        /* Primary text color */
  --primary: #2563eb;           /* Brand color (buttons, links) */
  --primary-hover: #1d4ed8;     /* Brand color on hover */
  --secondary: #f3f4f6;         /* Secondary backgrounds */
  --border: #e5e7eb;            /* Border color */
  --card: #ffffff;              /* Card backgrounds */
  --card-foreground: #111827;   /* Card text color */
  --muted: #f9fafb;             /* Muted backgrounds */
  --muted-foreground: #6b7280;  /* Muted text (labels, metadata) */
  --accent: #f3f4f6;            /* Accent backgrounds (hover states) */
  --accent-foreground: #111827; /* Accent text */
}
```

#### 2. Update Dark Mode Colors

Edit the `:root.dark` block (lines 23-36):

```css
/* Dark mode */
:root.dark {
  --background: #111827;        /* Dark page background */
  --foreground: #f3f4f6;        /* Dark mode text */
  --primary: #3b82f6;           /* Brand color (slightly lighter for dark) */
  --primary-hover: #2563eb;     /* Brand hover */
  --secondary: #1f2937;         /* Dark secondary backgrounds */
  --border: #374151;            /* Dark borders */
  --card: #1f2937;              /* Dark card backgrounds */
  --card-foreground: #f3f4f6;   /* Card text in dark mode */
  --muted: #374151;             /* Dark muted backgrounds */
  --muted-foreground: #9ca3af;  /* Dark muted text */
  --accent: #374151;            /* Dark accent backgrounds */
  --accent-foreground: #f3f4f6; /* Dark accent text */
}
```

### Example: Changing to a Green Theme

```css
/* Light mode - Green theme */
:root {
  --background: #ffffff;
  --foreground: #111827;
  --primary: #059669;           /* Emerald green instead of blue */
  --primary-hover: #047857;     /* Darker emerald */
  --secondary: #f0fdf4;         /* Light green tint */
  --border: #d1fae5;            /* Green-tinted border */
  --card: #ffffff;
  --card-foreground: #111827;
  --muted: #ecfdf5;
  --muted-foreground: #6b7280;
  --accent: #d1fae5;            /* Light green accent */
  --accent-foreground: #065f46;
}

/* Dark mode - Green theme */
:root.dark {
  --background: #111827;
  --foreground: #f3f4f6;
  --primary: #10b981;           /* Brighter emerald for dark mode */
  --primary-hover: #059669;
  --secondary: #064e3b;         /* Dark green */
  --border: #065f46;
  --card: #1f2937;
  --card-foreground: #f3f4f6;
  --muted: #064e3b;
  --muted-foreground: #9ca3af;
  --accent: #065f46;
  --accent-foreground: #d1fae5;
}
```

### Testing Your Changes

1. Save `globals.css`
2. Restart the dev server: `npm run dev`
3. Test in both light and dark modes using the theme toggle
4. Check contrast ratios for accessibility (aim for WCAG AA: 4.5:1 for text)

### Color Usage Reference

| Variable | Used For | Examples |
|----------|----------|----------|
| `--primary` | Brand elements | Buttons, links, active states, Pulse logo |
| `--background` | Page background | Body, main containers |
| `--card` | Card backgrounds | Article cards, preference panels, modals |
| `--border` | All borders | Inputs, cards, dividers, navbar |
| `--muted` | Subtle backgrounds | Info boxes, disabled states |
| `--accent` | Interactive highlights | Hover states, focus rings |

---

## Typography & Fonts

### Current Font Setup

Pulse uses **Geist Sans** (primary) and **Geist Mono** (code) from Google Fonts.

**File:** [frontend/src/app/layout.tsx](../frontend/src/app/layout.tsx)

### Changing Fonts

#### Option 1: Use Different Google Fonts

1. **Update font imports** (lines 2, 6-14):

```typescript
import { Inter, Roboto_Mono } from "next/font/google";

const primaryFont = Inter({
  variable: "--font-geist-sans",  // Keep variable name for consistency
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],  // Specify weights
});

const monoFont = Roboto_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});
```

2. **Update body className** (line 29):

```typescript
<body className={`${primaryFont.variable} ${monoFont.variable} antialiased`}>
```

3. **Restart dev server** to download new fonts

#### Option 2: Use Custom/Self-Hosted Fonts

1. **Add font files** to `frontend/public/fonts/`:
   ```
   frontend/public/fonts/
   ├── CustomFont-Regular.woff2
   ├── CustomFont-Bold.woff2
   └── CustomFont-Italic.woff2
   ```

2. **Define fonts in globals.css**:

```css
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/CustomFont-Regular.woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
}

@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/CustomFont-Bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
}
```

3. **Update CSS variable** in `globals.css`:

```css
body {
  font-family: 'CustomFont', Arial, Helvetica, sans-serif;
}
```

### Font Size Scale

Font sizes use Tailwind's default scale. To customize:

**Create** `frontend/tailwind.config.ts` (if not exists):

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      fontSize: {
        'xs': '0.75rem',    // 12px
        'sm': '0.875rem',   // 14px
        'base': '1rem',     // 16px (default)
        'lg': '1.125rem',   // 18px
        'xl': '1.25rem',    // 20px
        '2xl': '1.5rem',    // 24px
        '3xl': '1.875rem',  // 30px
        '4xl': '2.25rem',   // 36px
      },
    },
  },
};
export default config;
```

---

## Spacing & Layout

### Container Widths

Most pages use `max-w-7xl` (1280px) containers. To change globally:

**Search and replace** across components:
```bash
find frontend/src -name "*.tsx" -exec sed -i '' 's/max-w-7xl/max-w-6xl/g' {} \;
```

Or create a **custom container class** in `globals.css`:

```css
@layer utilities {
  .container-custom {
    max-width: 1400px;  /* Your preferred width */
    margin-left: auto;
    margin-right: auto;
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
```

### Responsive Breakpoints

Tailwind breakpoints (default):

| Breakpoint | Min Width | Usage |
|------------|-----------|-------|
| `sm:` | 640px | Mobile landscape |
| `md:` | 768px | Tablet |
| `lg:` | 1024px | Desktop |
| `xl:` | 1280px | Large desktop |
| `2xl:` | 1536px | Extra large |

**Customize in `tailwind.config.ts`:**

```typescript
theme: {
  screens: {
    'mobile': '480px',
    'tablet': '768px',
    'laptop': '1024px',
    'desktop': '1440px',
  },
}
```

### Spacing Scale

Pulse uses Tailwind's default spacing (1 unit = 0.25rem = 4px):

```
p-4  = 1rem (16px)
gap-6 = 1.5rem (24px)
mt-8 = 2rem (32px)
```

**Customize spacing** in `tailwind.config.ts`:

```typescript
theme: {
  extend: {
    spacing: {
      '128': '32rem',   // Extra large spacing
      '144': '36rem',
    },
  },
}
```

---

## Animations & Transitions

### Global Transitions

**Current setting** in `globals.css` (line 67):

```css
body {
  transition: background-color 0.3s ease, color 0.3s ease;
}
```

**Customize duration:**

```css
body {
  transition: background-color 0.5s ease, color 0.5s ease;  /* Slower */
}
```

### Component Transitions

Most interactive elements use `transition-colors`:

**Find and customize:**
```bash
# Search for transition usage
grep -r "transition-colors" frontend/src/
```

**Change globally** via search and replace:
```bash
# Change transition speed
find frontend/src -name "*.tsx" -exec sed -i '' 's/transition-colors/transition-colors duration-500/g' {} \;
```

### Custom Animations

Add to `globals.css`:

```css
@layer utilities {
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .animate-fade-in {
    animation: fadeIn 0.3s ease-out;
  }

  @keyframes pulse-slow {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .animate-pulse-slow {
    animation: pulse-slow 3s ease-in-out infinite;
  }
}
```

**Use in components:**

```tsx
<div className="animate-fade-in">
  Content fades in
</div>
```

---

## Component-Specific Styling

### Navbar

**File:** [frontend/src/components/Navbar.tsx](../frontend/src/components/Navbar.tsx)

**Key classes:**
```tsx
// Background
className="bg-card border-b border-border"

// Active nav item
className="bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400"

// Inactive nav item
className="text-muted-foreground hover:bg-accent hover:text-accent-foreground"
```

**Customization example** (change active color from indigo to emerald):

```tsx
// Replace in Navbar.tsx
className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400"
```

### Dark Mode Toggle

**File:** [frontend/src/components/DarkModeToggle.tsx](../frontend/src/components/DarkModeToggle.tsx)

**Current styling:**
```tsx
className="px-4 py-2 rounded-lg border border-border bg-card hover:bg-accent"
```

**Customize button size:**
```tsx
className="px-6 py-3 rounded-xl border-2 border-border bg-card hover:bg-accent text-lg"
```

### Cards (Article Cards, Preference Panels)

**Common pattern:**
```tsx
className="bg-card border border-border rounded-lg p-6 hover:shadow-lg transition-shadow"
```

**Increase corner radius globally:**

Create utility in `globals.css`:
```css
@layer utilities {
  .card-rounded {
    border-radius: 1rem;  /* Larger radius */
  }
}
```

### Buttons

**Primary buttons** (used in login, signup, preferences):
```tsx
className="bg-primary text-white hover:bg-primary-hover"
```

**Secondary buttons:**
```tsx
className="bg-secondary text-foreground hover:bg-accent"
```

**Customize button radius globally:**

Add to `globals.css`:
```css
@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors;
  }

  .btn-primary {
    @apply bg-primary text-white hover:bg-primary-hover;
  }

  .btn-secondary {
    @apply bg-secondary text-foreground hover:bg-accent;
  }
}
```

Then use: `<button className="btn btn-primary">Click</button>`

### Gradients (Hero Backgrounds)

**Landing page, How It Works, Login, Signup:**

```tsx
className="bg-gradient-to-br from-blue-50 dark:from-gray-900 via-indigo-50 dark:via-gray-800 to-purple-50 dark:to-gray-900"
```

**Change to green gradient:**
```tsx
className="bg-gradient-to-br from-emerald-50 dark:from-gray-900 via-teal-50 dark:via-gray-800 to-cyan-50 dark:to-gray-900"
```

**Subtle gradient (less vibrant):**
```tsx
className="bg-gradient-to-br from-gray-50 dark:from-gray-900 via-slate-50 dark:via-gray-850 to-zinc-50 dark:to-gray-900"
```

---

## Advanced Customization

### Using Tailwind Config for Brand Colors

**Create** `frontend/tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',  // Primary brand color
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
    },
  },
};
export default config;
```

**Use in components:**
```tsx
className="bg-brand-500 text-white hover:bg-brand-600"
```

### Custom Utility Classes

Add frequently-used patterns to `globals.css`:

```css
@layer utilities {
  /* Glass morphism effect */
  .glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  /* Smooth scroll */
  .smooth-scroll {
    scroll-behavior: smooth;
  }

  /* Focus ring */
  .focus-ring {
    @apply focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2;
  }

  /* Truncate text with ellipsis */
  .truncate-2-lines {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}
```

### Dark Mode Customization

**Change dark mode behavior** in `globals.css`:

```css
/* Make dark mode slightly lighter (charcoal instead of black) */
:root.dark {
  --background: #1e293b;  /* Slate-800 instead of gray-900 */
  --foreground: #f8fafc;  /* Brighter text */
}
```

**Add custom dark mode variants:**

```css
@layer utilities {
  .dark\:shadow-xl-bright {
    @apply dark:shadow-xl dark:shadow-indigo-500/20;
  }
}
```

### Component Shadow System

Add shadow utilities:

```css
@layer utilities {
  .shadow-card {
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  }

  .shadow-card-hover {
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  }

  .dark .shadow-card {
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.5);
  }
}
```

---

## Quick Customization Recipes

### Recipe 1: Minimal Monochrome Theme

```css
:root {
  --background: #ffffff;
  --foreground: #000000;
  --primary: #000000;
  --primary-hover: #1a1a1a;
  --secondary: #f5f5f5;
  --border: #e0e0e0;
  --card: #ffffff;
  --card-foreground: #000000;
  --muted: #f5f5f5;
  --muted-foreground: #737373;
  --accent: #f5f5f5;
  --accent-foreground: #000000;
}

:root.dark {
  --background: #000000;
  --foreground: #ffffff;
  --primary: #ffffff;
  --primary-hover: #e6e6e6;
  --secondary: #1a1a1a;
  --border: #333333;
  --card: #0a0a0a;
  --card-foreground: #ffffff;
  --muted: #1a1a1a;
  --muted-foreground: #a3a3a3;
  --accent: #1a1a1a;
  --accent-foreground: #ffffff;
}
```

### Recipe 2: Warm Orange/Red Theme

```css
:root {
  --primary: #ea580c;        /* Orange-600 */
  --primary-hover: #c2410c;  /* Orange-700 */
  --accent: #fed7aa;         /* Orange-200 */
}

:root.dark {
  --primary: #fb923c;        /* Orange-400 */
  --primary-hover: #f97316;  /* Orange-500 */
  --accent: #7c2d12;         /* Orange-900 */
}
```

### Recipe 3: High Contrast Theme

```css
:root {
  --background: #ffffff;
  --foreground: #000000;
  --primary: #0066cc;
  --border: #000000;
  --card: #ffffff;
}

:root.dark {
  --background: #000000;
  --foreground: #ffffff;
  --primary: #66b3ff;
  --border: #ffffff;
  --card: #000000;
}
```

---

## Testing & Validation

### Accessibility Checklist

After customizing colors:

1. **Test contrast ratios** using [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
   - Text: 4.5:1 minimum (WCAG AA)
   - Large text: 3:1 minimum

2. **Test dark mode** thoroughly:
   ```bash
   # Toggle between light/dark/auto modes
   # Check all pages: landing, login, signup, feed, preferences, etc.
   ```

3. **Test color blindness** using Chrome DevTools:
   - Open DevTools → Rendering → Emulate vision deficiencies

4. **Validate focus states** (keyboard navigation):
   ```bash
   # Tab through all interactive elements
   # Ensure focus rings are visible
   ```

### Browser Testing

Test customizations in:
- Chrome/Edge (Chromium)
- Firefox
- Safari (important for gradient rendering differences)

### Performance Impact

After customization:

```bash
# Build and check bundle size
npm run build

# Look for CSS size in output:
# ⚠️ If CSS bundle > 50KB, consider optimization
```

---

## Troubleshooting

### Colors Not Updating

1. **Clear Next.js cache:**
   ```bash
   rm -rf .next
   npm run dev
   ```

2. **Hard refresh browser:** `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

3. **Check CSS variable syntax:**
   ```css
   /* ✅ Correct */
   --primary: #2563eb;

   /* ❌ Incorrect */
   --primary = #2563eb;  /* Missing colon */
   ```

### Dark Mode Not Working

1. **Verify `@variant` directive** is present in `globals.css`:
   ```css
   @variant dark (.dark &);
   ```

2. **Check ThemeProvider** is wrapping app in `layout.tsx`

3. **Inspect HTML element** in DevTools - should have `class="dark"` in dark mode

### Font Not Loading

1. **Check font import** in `layout.tsx`
2. **Verify font variable** is applied to `<body>`
3. **Check Network tab** in DevTools for 404s
4. **Clear browser cache** and restart dev server

---

## Resources

### Color Tools

- [Coolors](https://coolors.co/) - Color palette generator
- [Adobe Color](https://color.adobe.com/) - Color wheel and schemes
- [Tailwind Color Palette](https://tailwindcss.com/docs/customizing-colors) - Reference
- [Contrast Checker](https://webaim.org/resources/contrastchecker/) - WCAG validation

### Font Resources

- [Google Fonts](https://fonts.google.com/) - Free web fonts
- [Font Pair](https://www.fontpair.co/) - Font combination suggestions
- [Modern Font Stacks](https://modernfontstacks.com/) - System font stacks

### Design Inspiration

- [Dribbble](https://dribbble.com/tags/news-app) - News app designs
- [Awwwards](https://www.awwwards.com/) - Award-winning designs
- [Tailwind UI](https://tailwindui.com/) - Component examples

---

## Summary

### Key Files for Customization

| File | Purpose | Restart Required? |
|------|---------|-------------------|
| `frontend/src/app/globals.css` | Colors, fonts, utilities | Yes |
| `frontend/src/app/layout.tsx` | Font imports, metadata | Yes |
| `frontend/tailwind.config.ts` | Tailwind config | Yes |
| Component files (`*.tsx`) | Individual styling | No (hot reload) |

### Workflow

1. Edit `globals.css` for color palette
2. Edit `layout.tsx` for fonts
3. Restart dev server: `npm run dev`
4. Test in browser (light + dark mode)
5. Validate accessibility
6. Commit changes with descriptive message

---

**Last Updated:** 2025-10-17
**Maintained by:** Pulse Development Team

For questions or suggestions, please open an issue on GitHub or consult the main [README.md](../README.md).
