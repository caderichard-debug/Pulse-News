# Opposing Viewpoints UI Template

This document provides a template and guide for implementing new features using the same UI pattern as the Opposing Viewpoints component.

## UI Pattern Overview

The Opposing Viewpoints component follows a consistent pattern that can be reused for other features:

### 1. Expandable Card Structure
```tsx
// Initially collapsed with enticing preview
if (!expanded) {
  return (
    <div className="mt-6 border-2 border-dashed border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-800 rounded-lg p-6">
      <div className="text-center">
        <Icon className="h-8 w-8 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
          Feature Title
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Brief description of what this feature does
        </p>
        <button onClick={() => setExpanded(true)}>
          <Eye className="h-4 w-4 mr-2" />
          View Feature Details
        </button>
      </div>
    </div>
  )
}
```

### 2. Header with Controls
```tsx
<div className="flex items-center justify-between mb-4">
  <div className="flex items-center space-x-2">
    <FeatureIcon className="h-5 w-5 text-blue-600" />
    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">
      Feature Name
    </h3>
    {featureData.length > 0 && (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
        {featureData.length} items
      </span>
    )}
  </div>
  <div className="flex items-center space-x-2">
    {showFilterOption && (
      <button onClick={() => setShowFilters(!showFilters)}>
        <Filter className="h-4 w-4 mr-1" />
        Filter
      </button>
    )}
    <button onClick={() => setExpanded(false)}>
      <EyeOff className="h-4 w-4 mr-1" />
      Hide
    </button>
  </div>
</div>
```

### 3. Filter Section (Optional)
```tsx
{showFilters && (
  <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
    <div className="flex items-center justify-between mb-3">
      <h4 className="font-semibold text-blue-900 dark:text-blue-100">Filter Options</h4>
      <button onClick={() => setShowFilters(false)}>
        <X className="h-4 w-4" />
      </button>
    </div>
    <div className="flex flex-wrap gap-2 mb-3">
      {filterOptions.map(option => (
        <button
          key={option.value}
          onClick={() => setSelectedFilter(
            selectedFilter === option.value ? null : option.value
          )}
          className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
            selectedFilter === option.value
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          <span className="mr-1">{getFilterIcon(option.value)}</span>
          {option.label}
        </button>
      ))}
    </div>
  </div>
)}
```

### 4. Loading State
```tsx
{loading ? (
  <div className="text-center py-8">
    <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
    <p className="text-gray-600 dark:text-gray-400">Processing...</p>
  </div>
) : featureData.length > 0 ? (
  // Render feature items
) : (
  // Empty state with action button
)}
```

### 5. Feature Item Card Pattern
```tsx
{featureData.map((item, index) => (
  <div key={`${item.id}-${index}`} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
    {/* Header with icon and metadata */}
    <div className="p-4 pb-3 border-l-4 border-l-blue-500">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getFeatureIcon(item.type)}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
              {getFeatureLabel(item.type, item.category)}
            </h3>
            <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
              <span>{item.source_name}</span>
              <span>•</span>
              <span className="text-xs">
                {new Date(item.date).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {/* Status badges */}
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(item.strength)}`}>
            {Math.round(item.strength * 100)}% relevant
          </span>
        </div>
      </div>
    </div>

    {/* Content section */}
    <div className="p-4 space-y-3">
      <div>
        <button
          onClick={() => handleViewInApp(item.id)}
          className="font-semibold text-gray-900 dark:text-gray-100 mb-1 text-left hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
        >
          {item.title}
        </button>
        {item.summary && (
          <p className="text-gray-600 dark:text-gray-400 text-sm mb-2">{item.summary}</p>
        )}
      </div>

      {/* Additional info panels */}
      {item.type === 'specific_type' && item.detail && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-3">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Why this matters:</strong> {item.explanation || item.reasoning}
          </p>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex justify-between items-center pt-2">
        <div className="text-xs text-gray-500 dark:text-gray-400 max-w-[60%]">
          {item.description}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleViewInApp(item.id)}
            className="flex items-center space-x-1 border border-blue-300 dark:border-blue-600 px-3 py-1.5 rounded text-sm text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
          >
            View in App
          </button>
          <button
            onClick={() => window.open(item.external_url, '_blank')}
            className="flex items-center space-x-1 border border-gray-300 dark:border-gray-600 px-3 py-1.5 rounded text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          >
            View Original
            <ArrowRight className="h-3 w-3 ml-1" />
          </button>
        </div>
      </div>
    </div>
  </div>
))}
```

### 6. Empty State with Action Button
```tsx
<div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6">
  <div className="text-center text-gray-600 dark:text-gray-400">
    <FeatureIcon className="h-8 w-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
    <p className="font-medium text-gray-700 dark:text-gray-300 mb-2">
      {hasTriedAnalysis
        ? "No items found after analysis."
        : "No items available yet."
      }
    </p>
    <p className="text-sm mb-4">
      {hasTriedAnalysis
        ? "Try adjusting filters or check back later."
        : "Our system can analyze this to find relevant items."
      }
    </p>

    <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
      <button
        onClick={triggerAnalysis}
        disabled={loading}
        className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-md transition-colors"
      >
        {loading ? (
          <>
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Analyzing...</span>
          </>
        ) : (
          <>
            <RefreshCw className="h-4 w-4" />
            <span>Analyze for Items</span>
          </>
        )}
      </button>

      <button
        onClick={refreshData}
        disabled={loading}
        className="flex items-center space-x-1 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
      >
        <RefreshCw className="h-3 w-3" />
        <span>Refresh</span>
      </button>
    </div>
  </div>
</div>
```

## Implementation Steps

### Step 1: Create the Component Structure
```tsx
'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight, Eye, EyeOff, RefreshCw, Filter, X } from 'lucide-react'
import { api } from '@/lib/api'

// Define interfaces
interface FeatureItem {
  id: number
  title: string
  // ... other fields
}

interface FeatureResponse {
  items: FeatureItem[]
  total_found: number
  // ... other fields
}

interface FeatureProps {
  primaryId: number
}

export function FeatureComponent({ primaryId }: FeatureProps) {
  const router = useRouter()
  const [items, setItems] = useState<FeatureItem[]>([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // ... other state

  const handleViewInApp = (itemId: number) => {
    router.push(`/item/${itemId}`)
  }

  // ... rest of component
}
```

### Step 2: Add API Integration
```tsx
// In api.ts
async getFeatureData(params?: {
  id?: number;
  type?: string;
  limit?: number;
}) {
  const queryParams = new URLSearchParams();
  if (params?.id) queryParams.append('id', params.id.toString());
  // ... other parameters

  return this.request<FeatureResponse>(`/feature/data?${queryParams}`);
}

// In component
const fetchData = async () => {
  try {
    setLoading(true)
    const data = await api.getFeatureData({
      id: primaryId,
      limit: 10
    })
    setItems(data.items)
  } catch (err) {
    setError('Failed to load data')
  } finally {
    setLoading(false)
  }
}
```

### Step 3: Add Backend API Endpoint
```python
# In routes/feature.py
@router.get("/{id}/data")
async def get_feature_data(
    id: int,
    limit: int = Query(default=10),
    session: Session = Depends(get_session)
):
    # Query database for feature data
    items = session.exec(
        select(FeatureModel)
        .where(FeatureModel.primary_id == id)
        .limit(limit)
    ).all()

    return {
        "items": items,
        "total_found": len(items)
    }
```

### Step 4: Add Styling
Use the existing Tailwind classes from the design system:
- `bg-card`, `text-card-foreground` for main content
- `bg-blue-50 dark:bg-blue-900/20` for info sections
- `border-border` for borders
- `hover:bg-background` for interactive elements

### Step 5: Add Error Handling
```tsx
{error && (
  <div className="mb-4 border border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800 rounded-lg p-4">
    <p className="text-red-700 dark:text-red-300">{error}</p>
  </div>
)}
```

### Step 6: Add Loading States
```tsx
{loading && (
  <div className="text-center py-8">
    <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
    <p className="text-gray-600 dark:text-gray-400">Loading...</p>
  </div>
)}
```

## Best Practices

1. **Dark Mode Support**: Always use semantic classes that have dark variants
2. **Responsive Design**: Use `flex-col sm:flex-row` for responsive layouts
3. **Accessibility**: Include proper ARIA labels and keyboard navigation
4. **Loading States**: Show loading indicators during async operations
5. **Error Handling**: Display user-friendly error messages
6. **State Management**: Persist user preferences in localStorage
7. **Navigation**: Use Next.js router for in-app navigation
8. **External Links**: Open external links in new tabs

## Color Palette

Use the existing color scheme:
- **Blue**: Primary actions (`text-blue-600`, `bg-blue-50`)
- **Gray**: Secondary text (`text-gray-600`, `bg-gray-50`)
- **Red/Orange/Yellow**: Status indicators based on relevance
- **Semantic**: Use semantic classes for consistency

## File Structure

```
src/
├── components/
│   ├── FeatureComponent.tsx
│   └── __tests__/
│       └── FeatureComponent.test.tsx
├── lib/
│   └── api.ts
└── app/
    └── [feature]/
        └── page.tsx
```

This template provides a consistent foundation for implementing new features with the same high-quality UI as the Opposing Viewpoints component.