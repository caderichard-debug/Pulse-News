# Pulse Frontend Architecture Plan
**"A Lens on Discourse Itself"**

## 📋 Table of Contents
1. [Overview](#overview)
2. [Current State](#current-state)
3. [New Pages & Features](#new-pages--features)
4. [Technical Architecture](#technical-architecture)
5. [Data Visualization Components](#data-visualization-components)
6. [API Extensions Required](#api-extensions-required)
7. [Implementation Phases](#implementation-phases)
8. [Database Schema Additions](#database-schema-additions)

---

## 🎯 Overview

Transform Pulse from a basic newsletter service into a comprehensive **media literacy and discourse analysis platform** that helps users understand not just the news, but how news shapes discourse.

### Core Philosophy
- **Transparency**: Show users how bias, sentiment, and frameworks evolve
- **Engagement**: Challenge users' views with opposite viewpoints
- **Insight**: Provide multi-dimensional analysis of media discourse
- **Agency**: Give users full control over their information diet

---

## 📊 Current State

### Existing Pages
- ✅ `/` - Landing page (hero, features, sources, CTA)
- ✅ `/login` - User authentication
- ✅ `/signup` - User registration
- ✅ `/preferences` - Basic topic toggle

### Existing Infrastructure
- ✅ Next.js 15 with App Router
- ✅ React 19 with TypeScript
- ✅ Tailwind CSS 4
- ✅ JWT authentication
- ✅ API client (`src/lib/api.ts`)

---

## 🚀 New Pages & Features

### 1. **Enhanced Preferences Page** (`/preferences`)
Expand from basic topic toggles to comprehensive customization.

#### 1.1 Topic Customization
- **Toggle topics** (existing)
- **Priority slider** (1-5 stars) - affects article selection
- **Articles per topic** - dropdown (1-10 articles)
- **Good news placement** - radio buttons:
  - "Good news first" (positive sentiment → negative)
  - "Good news last" (negative → positive)
  - "Mixed" (balanced alternation)

#### 1.2 Source Customization
```
┌─────────────────────────────────────────────┐
│  Source Management                          │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ 🟢 Reuters          Trust: 9.5/10     │ │
│  │ Political Lean: Center                │ │
│  │ [✓] Subscribed    [View Profile →]   │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ 🔵 Fox News         Trust: 6.2/10     │ │
│  │ Political Lean: Right                 │ │
│  │ [✗] Subscribed    [View Profile →]   │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Source Discovery:                          │
│  ○ No new sources                           │
│  ◉ Mostly my selections, some new           │
│  ○ Totally open to new sources              │
│                                             │
│  [Learn How We Rate Sources →]              │
└─────────────────────────────────────────────┘
```

**Features:**
- **Subscribe/unsubscribe** to specific sources
- **Display credibility score** (from `sources.trust_score`)
- **Display political lean** (from aggregated `article_analysis.political_lean`)
- **Source discovery preference** (stored in new `user_preferences` table)
- **Link to bias aggregator** (e.g., AllSides, Media Bias Fact Check)

#### 1.3 Preset Configurations
- **"Balanced Bundle"**: Mix of high-credibility + biased sources
  - Reuters (9.5, center)
  - AP News (9.3, center)
  - NPR (7.8, center-left)
  - Fox News (6.2, right)
- **"High Credibility Only"**: Trust score ≥ 8.0
- **"Diverse Perspectives"**: Equal representation across lean spectrum

---

### 2. **Dashboard Page** (`/dashboard`)
Central hub for user insights and analytics.

#### 2.1 Overview Section
```
┌─────────────────────────────────────────────┐
│  Your Discourse Snapshot                    │
│                                             │
│  📰 Articles Read: 127                      │
│  📧 Newsletters Received: 42                │
│  🎯 Topics Tracked: 5                       │
│  📊 Views Changed: 3 (see below)            │
└─────────────────────────────────────────────┘
```

#### 2.2 Sentiment Over Time Graph
**Chart Type**: Multi-line time series

```
Sentiment Score
   +10 ┼                                    ╱╲
       │                                  ╱    ╲
    +5 ┼              ╱╲                ╱
       │            ╱    ╲            ╱
     0 ┼──────────╱────────╲────────╱───────────
       │                      ╲    ╱
    -5 ┼                        ╲╱
       │
   -10 ┼─────────────────────────────────────────
       └──────────────────────────────────────────→
        Sep 1   Sep 15   Oct 1   Oct 15   Nov 1

        ━━ Politics    ━━ Technology    ━━ Climate
```

**Data Source**:
- `article_analysis.sentiment_score` grouped by `published_at` and `topic_category`
- Rolling 7-day average to smooth noise

#### 2.3 Source Bias Over Time
**Chart Type**: Stacked area chart

```
% of Articles
   100% ┼
        │                ┌────────┐
        │        ┌───────┤ Right  │
    66% ┼────────┤       └────────┘
        │        │ Center
    33% ┼────────┤
        │        │ Left
     0% ┼────────┴───────────────────────────────
        └──────────────────────────────────────→
         Week 1  Week 2  Week 3  Week 4
```

**Calculation**:
```sql
SELECT
  DATE_TRUNC('week', published_at) as week,
  political_lean,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATE_TRUNC('week', published_at))
FROM article_analysis
GROUP BY week, political_lean
```

#### 2.4 Framework Positioning Chart
**Chart Type**: 2-axis scatter plot (primary frameworks)

```
Collective Welfare (+10)
        ↑
        │     ●              ● = Article
        │  ●     ●           Size = relevance
    +5  ┼    ●               Color = sentiment
        │       ●  ●
Individual ←───┼───────────→ Collective
Liberty    -5  ┼  ●    ●     Welfare
        │   ●     ●
   -10  ┼ ●
        │
        ↓
Individual Liberty (+10)
```

**Data Source**:
- `article_frameworks.position_on_axis` for X/Y coordinates
- `article_frameworks.relevance_score` for bubble size
- `article_analysis.sentiment_score` for color gradient

---

### 3. **Home Feed Page** (`/home` or `/feed`)
Personalized article feed with advanced filtering.

#### 3.1 Feed Layout
```
┌─────────────────────────────────────────────┐
│  Filters: [All Topics ▼] [All Sources ▼]   │
│  Sort: [Newest ▼] | View: [List] [Grid]    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🔵 Reuters | Politics | 2 hours ago        │
│  Biden Announces New Climate Initiative     │
│                                             │
│  📊 Sentiment: +6 | Lean: Center            │
│  🎯 Frameworks: Liberty vs Welfare (+4)     │
│                                             │
│  [View Analysis →]                          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  🔴 Fox News | Politics | 3 hours ago       │
│  Critics Slam Federal Overreach             │
│                                             │
│  📊 Sentiment: -3 | Lean: Right             │
│  🎯 Frameworks: Liberty vs Welfare (-7)     │
│                                             │
│  [View Analysis →]                          │
└─────────────────────────────────────────────┘
```

#### 3.2 Article Analysis Page (`/article/[id]`)
Deep dive into individual article with cross-source comparison.

**Sections:**
1. **Article Summary** (from `article_analysis.summary`)
2. **Sentiment & Bias** (visual indicators)
3. **Verified Statistics** (from `statistic_verifications`)
4. **Framework Positioning** (visual plot)
5. **Coverage Comparison** (how other sources covered the same story)
   - Cluster detection: `article_clusters` + `article_cluster_members`
   - Side-by-side headlines & sentiment scores
6. **Context** (from `article_context`)
   - Background
   - Key players
   - Timeline
   - Significance

---

### 4. **Challenge System** (`/challenge`)
Weekly viewpoint engagement to track view changes.

#### 4.1 Weekly Challenge Flow
```
Monday: Challenge Issued
┌─────────────────────────────────────────────┐
│  This Week's Challenge                      │
│                                             │
│  "Should the government regulate AI?"       │
│                                             │
│  Rate your stance:                          │
│  ◉ Strongly Disagree                        │
│  ○ Disagree                                 │
│  ○ Neutral                                  │
│  ○ Agree                                    │
│  ○ Strongly Agree                           │
│                                             │
│  [Submit Response]                          │
└─────────────────────────────────────────────┘

Tuesday-Saturday: Curated Content
- 2 articles supporting "Agree"
- 2 articles supporting "Disagree"
- 1 neutral analysis

Sunday: Reflection
┌─────────────────────────────────────────────┐
│  Has your view changed?                     │
│                                             │
│  Original stance: Strongly Agree            │
│  New stance:                                │
│  ○ Strongly Disagree                        │
│  ○ Disagree                                 │
│  ◉ Neutral ← Changed!                       │
│  ○ Agree                                    │
│  ○ Strongly Agree                           │
│                                             │
│  Write about your shift (optional):         │
│  ┌─────────────────────────────────────┐   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [Submit Reflection]                        │
└─────────────────────────────────────────────┘

Monday: Curated Reflections Email
- 5-10 anonymous user reflections
- Aggregated view-change statistics
```

#### 4.2 Challenge History (`/challenge/history`)
Track your opinion evolution over time.

```
┌─────────────────────────────────────────────┐
│  Your Challenge Journey                     │
│                                             │
│  ✓ Week 12: AI Regulation                  │
│    Before: Strongly Agree → After: Neutral  │
│    [Read Your Reflection]                   │
│                                             │
│  ✓ Week 11: Student Loan Forgiveness       │
│    Before: Disagree → After: Disagree       │
│    [Read Your Reflection]                   │
│                                             │
│  View Changes: 8 out of 12 challenges       │
└─────────────────────────────────────────────┘
```

---

### 5. **Analytics Dashboard** (`/analytics`)
Advanced data visualizations for discourse patterns.

#### 5.1 Sentiment × Framework Heatmap
**The Signature Feature**

```
Framework Axis
    ↑
    │  Collective Welfare
+10 ┼ ┌─┬─┬─┬─┬─┐
    │ │░│▒│▓│█│▓│  Intensity:
 +5 ┼ ├─┼─┼─┼─┼─┤  ░ Low article count
    │ │░│░│▒│▓│▒│  ▒ Medium count
  0 ┼ ├─┼─┼─┼─┼─┤  ▓ High count
    │ │▒│░│░│▒│░│  █ Very high count
 -5 ┼ ├─┼─┼─┼─┼─┤
    │ │▓│▒│░│░│░│  Color gradient:
-10 ┼ └─┴─┴─┴─┴─┘  Red → negative sentiment
    └────────────→  Green → positive sentiment
    -10 -5 0 +5 +10  Blue → neutral

    Individual Liberty

Hover tooltip:
┌─────────────────────────────┐
│ Position: Liberty -8, +6    │
│ Articles: 23                │
│ Avg Sentiment: -4.2         │
│ Example Articles:           │
│ • "Biden's Vaccine Mandate" │
│ • "Federal Mask Rules"      │
└─────────────────────────────┘
```

**Data Aggregation**:
```sql
SELECT
  af1.position_on_axis as x_axis,
  af2.position_on_axis as y_axis,
  AVG(aa.sentiment_score) as avg_sentiment,
  COUNT(*) as article_count,
  ARRAY_AGG(a.title LIMIT 3) as sample_articles
FROM article_frameworks af1
JOIN article_frameworks af2 ON af1.article_id = af2.article_id
JOIN article_analysis aa ON aa.article_id = af1.article_id
JOIN articles a ON a.id = af1.article_id
WHERE af1.framework_id = 1  -- Primary framework (e.g., Liberty vs Welfare)
  AND af2.framework_id = 2  -- Secondary framework
  AND a.published_at > NOW() - INTERVAL '30 days'
GROUP BY x_axis, y_axis
```

**Time Evolution Toggle**:
- Week-by-week animation
- "Did left-leaning articles become more negative after Event X?"
- "Are neutral sources clustering while partisan ones diverge?"

#### 5.2 Claim Recurrence Plot
Track which statistics/claims appear across sources.

```
Claim: "50% increase in border crossings"

Timeline:
Oct 1  ●────●────────────●─────●─── Oct 15
       │    │            │     │
    Reuters Fox    Breitbart  CNN
    (verified) (disputed) (false) (unverified)

Sources: 4
Verification: 25% verified, 25% disputed, 25% false
First seen: Reuters (Oct 1)
Last seen: CNN (Oct 14)
```

**Data Source**: `statistic_verifications` with cross-article matching

---

## 🛠️ Technical Architecture

### Tech Stack (No Changes)
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4
- **Charts**: Recharts or Chart.js
- **State Management**: React Context + Hooks
- **Data Fetching**: React Query (TanStack Query)

### New Libraries to Add
```bash
npm install recharts              # Charts & visualizations
npm install @tanstack/react-query # Data fetching & caching
npm install date-fns              # Date manipulation
npm install framer-motion         # Animations
npm install react-hot-toast       # Notifications
```

### Folder Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/              # Auth layout group
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── (dashboard)/         # Protected routes
│   │   │   ├── dashboard/
│   │   │   ├── feed/
│   │   │   ├── preferences/
│   │   │   ├── challenge/
│   │   │   ├── analytics/
│   │   │   └── article/[id]/
│   │   ├── layout.tsx
│   │   └── page.tsx             # Landing page
│   ├── components/
│   │   ├── ui/                  # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Slider.tsx
│   │   │   └── ...
│   │   ├── charts/              # Chart components
│   │   │   ├── SentimentLineChart.tsx
│   │   │   ├── BiasStackedArea.tsx
│   │   │   ├── FrameworkScatter.tsx
│   │   │   └── SentimentHeatmap.tsx
│   │   ├── feed/                # Feed components
│   │   │   ├── ArticleCard.tsx
│   │   │   ├── FeedFilters.tsx
│   │   │   └── ArticleAnalysis.tsx
│   │   └── layout/              # Layout components
│   │       ├── Navbar.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── lib/
│   │   ├── api.ts               # Existing API client
│   │   ├── api/                 # New: organized by domain
│   │   │   ├── articles.ts
│   │   │   ├── analytics.ts
│   │   │   ├── preferences.ts
│   │   │   └── challenges.ts
│   │   ├── utils.ts
│   │   └── hooks/               # Custom React hooks
│   │       ├── useAuth.ts
│   │       ├── useAnalytics.ts
│   │       └── useChallenge.ts
│   └── types/
│       ├── api.ts               # API response types
│       ├── chart.ts             # Chart data types
│       └── index.ts
```

---

## 📊 Data Visualization Components

### 1. **SentimentLineChart**
```typescript
// components/charts/SentimentLineChart.tsx
interface SentimentData {
  date: string;
  [topicName: string]: number | string;  // Dynamic topic keys
}

interface Props {
  data: SentimentData[];
  topics: string[];
  dateRange: [Date, Date];
}

export function SentimentLineChart({ data, topics, dateRange }: Props) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={[-10, 10]} />
        <Tooltip />
        <Legend />
        {topics.map((topic, idx) => (
          <Line
            key={topic}
            type="monotone"
            dataKey={topic}
            stroke={COLORS[idx]}
            strokeWidth={2}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### 2. **SentimentHeatmap**
```typescript
// components/charts/SentimentHeatmap.tsx
interface HeatmapCell {
  x: number;         // Framework 1 position (-10 to +10)
  y: number;         // Framework 2 position (-10 to +10)
  value: number;     // Article count
  sentiment: number; // Avg sentiment (-10 to +10)
  articles: Array<{ id: number; title: string }>;
}

interface Props {
  data: HeatmapCell[];
  framework1: Framework;
  framework2: Framework;
  timeRange?: string; // '7d', '30d', '90d'
}

export function SentimentHeatmap({ data, framework1, framework2 }: Props) {
  return (
    <div className="relative">
      <svg width={600} height={600}>
        {/* Grid cells */}
        {data.map((cell, idx) => (
          <rect
            key={idx}
            x={scaleX(cell.x)}
            y={scaleY(cell.y)}
            width={cellWidth}
            height={cellHeight}
            fill={getSentimentColor(cell.sentiment)}
            opacity={getOpacity(cell.value)}
            onMouseEnter={() => showTooltip(cell)}
          />
        ))}

        {/* Axes labels */}
        <text x={300} y={20}>{framework2.name}</text>
        <text x={20} y={300} transform="rotate(-90)">{framework1.name}</text>
      </svg>

      {/* Tooltip */}
      <HeatmapTooltip cell={hoveredCell} />
    </div>
  );
}
```

### 3. **BiasStackedArea**
```typescript
// components/charts/BiasStackedArea.tsx
interface BiasData {
  week: string;
  left: number;    // % of left-leaning articles
  center: number;  // % of center articles
  right: number;   // % of right-leaning articles
}

export function BiasStackedArea({ data }: { data: BiasData[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="week" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Area type="monotone" dataKey="left" stackId="1" stroke="#3b82f6" fill="#3b82f6" />
        <Area type="monotone" dataKey="center" stackId="1" stroke="#64748b" fill="#64748b" />
        <Area type="monotone" dataKey="right" stackId="1" stroke="#ef4444" fill="#ef4444" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

---

## 🔌 API Extensions Required

### New Backend Routes

#### 1. **Analytics Endpoints**

```python
# backend/app/routes/analytics.py

@router.get("/analytics/sentiment-over-time")
async def get_sentiment_over_time(
    user_id: int,
    topic_ids: List[int] = Query([]),
    days: int = 30,
    db: Session = Depends(get_db)
) -> List[SentimentTimePoint]:
    """
    Returns daily avg sentiment scores by topic.

    Response:
    [
      {
        "date": "2025-10-01",
        "politics": -2.3,
        "technology": 4.5,
        "climate": -1.2
      },
      ...
    ]
    """
    pass

@router.get("/analytics/bias-distribution")
async def get_bias_distribution(
    user_id: int,
    weeks: int = 4,
    db: Session = Depends(get_db)
) -> List[BiasDistribution]:
    """
    Returns weekly bias distribution.

    Response:
    [
      {
        "week": "2025-09-25",
        "left": 35,
        "center": 40,
        "right": 25
      },
      ...
    ]
    """
    pass

@router.get("/analytics/framework-heatmap")
async def get_framework_heatmap(
    framework1_id: int,
    framework2_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
) -> List[HeatmapCell]:
    """
    Returns heatmap data for two frameworks.

    Response:
    [
      {
        "x": -8,
        "y": 6,
        "article_count": 23,
        "avg_sentiment": -4.2,
        "sample_articles": [
          {"id": 123, "title": "..."},
          ...
        ]
      },
      ...
    ]
    """
    pass

@router.get("/analytics/claim-recurrence")
async def get_claim_recurrence(
    claim_text: str,
    days: int = 30,
    db: Session = Depends(get_db)
) -> ClaimRecurrence:
    """
    Tracks a claim across sources.

    Response:
    {
      "claim": "50% increase in border crossings",
      "occurrences": [
        {
          "article_id": 123,
          "source": "Reuters",
          "published_at": "2025-10-01T08:00:00Z",
          "verification_status": "verified"
        },
        ...
      ],
      "verification_summary": {
        "verified": 2,
        "disputed": 1,
        "false": 1,
        "unverified": 0
      }
    }
    """
    pass
```

#### 2. **Source Preferences**

```python
# backend/app/routes/preferences.py

@router.get("/preferences/sources")
async def get_source_preferences(
    user_id: int,
    db: Session = Depends(get_db)
) -> List[SourcePreference]:
    """
    Returns user's source subscriptions.

    Response:
    [
      {
        "source_id": 1,
        "name": "Reuters",
        "trust_score": 9.5,
        "political_lean": "center",
        "subscribed": true
      },
      ...
    ]
    """
    pass

@router.put("/preferences/sources")
async def update_source_preferences(
    user_id: int,
    source_ids: List[int],
    discovery_mode: str,  # "none", "some", "open"
    db: Session = Depends(get_db)
):
    """Updates user's source subscriptions."""
    pass

@router.put("/preferences/article-order")
async def update_article_order(
    user_id: int,
    order: str,  # "good_first", "good_last", "mixed"
    db: Session = Depends(get_db)
):
    """Sets user's good news preference."""
    pass
```

#### 3. **Challenge System**

```python
# backend/app/routes/challenges.py

@router.get("/challenges/current")
async def get_current_challenge(
    user_id: int,
    db: Session = Depends(get_db)
) -> Challenge:
    """
    Returns this week's challenge.

    Response:
    {
      "id": 42,
      "question": "Should the government regulate AI?",
      "start_date": "2025-10-07",
      "end_date": "2025-10-13",
      "user_initial_response": null,  # or 1-5 scale
      "articles": [
        {
          "article_id": 123,
          "stance": "agree",
          "relevance": 0.9
        },
        ...
      ]
    }
    """
    pass

@router.post("/challenges/{challenge_id}/respond")
async def submit_challenge_response(
    challenge_id: int,
    user_id: int,
    response: ChallengeResponse,
    db: Session = Depends(get_db)
):
    """
    Submit initial or final response.

    Request:
    {
      "stance": 3,  // 1-5 scale
      "reflection": "I changed my mind because..." (optional)
    }
    """
    pass

@router.get("/challenges/history")
async def get_challenge_history(
    user_id: int,
    db: Session = Depends(get_db)
) -> List[ChallengeHistory]:
    """
    Returns user's challenge history.

    Response:
    [
      {
        "id": 41,
        "question": "Student loan forgiveness?",
        "initial_stance": 2,
        "final_stance": 2,
        "changed": false,
        "reflection": null
      },
      ...
    ]
    """
    pass

@router.get("/challenges/{challenge_id}/reflections")
async def get_curated_reflections(
    challenge_id: int,
    db: Session = Depends(get_db)
) -> List[CuratedReflection]:
    """
    Returns curated anonymous reflections for Monday email.
    """
    pass
```

#### 4. **Article Analysis**

```python
# backend/app/routes/articles.py

@router.get("/articles/{article_id}/coverage-comparison")
async def get_coverage_comparison(
    article_id: int,
    db: Session = Depends(get_db)
) -> CoverageComparison:
    """
    Returns how other sources covered the same story.

    Response:
    {
      "cluster_id": 12,
      "primary_article": {...},
      "related_articles": [
        {
          "id": 124,
          "title": "Critics Slam...",
          "source": "Fox News",
          "political_lean": "right",
          "sentiment_score": -6,
          "similarity_score": 0.85
        },
        ...
      ]
    }
    """
    pass

@router.get("/articles/{article_id}/context")
async def get_article_context(
    article_id: int,
    db: Session = Depends(get_db)
) -> ArticleContextResponse:
    """
    Returns full context for an article.

    Response:
    {
      "background": "This issue dates back to...",
      "key_players": ["Biden", "Congress", ...],
      "timeline": [
        {"date": "2024-01-15", "event": "..."},
        ...
      ],
      "significance": "This matters because...",
      "next_developments": "Watch for..."
    }
    """
    pass
```

---

## 🗄️ Database Schema Additions

### 1. **User Preferences Extension**
```sql
-- Add columns to users table
ALTER TABLE users ADD COLUMN source_discovery_mode VARCHAR(20) DEFAULT 'some';
  -- Values: 'none', 'some', 'open'

ALTER TABLE users ADD COLUMN article_order_preference VARCHAR(20) DEFAULT 'mixed';
  -- Values: 'good_first', 'good_last', 'mixed'

ALTER TABLE users ADD COLUMN articles_per_topic_default INT DEFAULT 5;
```

### 2. **User Source Subscriptions**
```sql
CREATE TABLE user_source_subscriptions (
    user_id INT REFERENCES users(id),
    source_id INT REFERENCES sources(id),
    subscribed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, source_id)
);
```

### 3. **Challenge System Tables**
```sql
CREATE TABLE challenges (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE challenge_responses (
    id SERIAL PRIMARY KEY,
    challenge_id INT REFERENCES challenges(id),
    user_id INT REFERENCES users(id),
    initial_stance INT CHECK (initial_stance BETWEEN 1 AND 5),
    final_stance INT CHECK (final_stance BETWEEN 1 AND 5),
    reflection TEXT,
    view_changed BOOLEAN GENERATED ALWAYS AS (initial_stance != final_stance) STORED,
    submitted_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(challenge_id, user_id)
);

CREATE TABLE challenge_articles (
    challenge_id INT REFERENCES challenges(id),
    article_id INT REFERENCES articles(id),
    stance VARCHAR(20), -- 'agree', 'disagree', 'neutral'
    relevance_score FLOAT CHECK (relevance_score BETWEEN 0 AND 1),
    PRIMARY KEY (challenge_id, article_id)
);

CREATE TABLE curated_reflections (
    id SERIAL PRIMARY KEY,
    challenge_id INT REFERENCES challenges(id),
    response_id INT REFERENCES challenge_responses(id),
    is_featured BOOLEAN DEFAULT FALSE,
    featured_at TIMESTAMP
);
```

### 4. **User Topic Preferences Enhancement**
```sql
-- Add articles_per_topic column
ALTER TABLE user_topic_preferences
  ADD COLUMN articles_per_topic INT DEFAULT 5;
```

---

## 🏗️ Implementation Phases

### **Phase 1: Enhanced Preferences** (Week 1-2)
**Goal**: Full control over sources, topics, and newsletter customization

#### Tasks:
1. **Backend**:
   - [ ] Create `user_source_subscriptions` table
   - [ ] Add preference columns to `users` table
   - [ ] Implement `/preferences/sources` endpoints
   - [ ] Implement `/preferences/article-order` endpoint
   - [ ] Update newsletter service to respect preferences

2. **Frontend**:
   - [ ] Build source subscription UI
   - [ ] Add political lean aggregation to source cards
   - [ ] Implement articles-per-topic sliders
   - [ ] Add good news ordering radio buttons
   - [ ] Create preset configuration buttons

3. **Testing**:
   - [ ] Test source filtering in newsletter generation
   - [ ] Verify article ordering logic
   - [ ] Test preset configurations

---

### **Phase 2: Dashboard & Analytics** (Week 3-5)
**Goal**: Visualize sentiment, bias, and discourse patterns

#### Tasks:
1. **Backend**:
   - [ ] Implement `/analytics/sentiment-over-time` endpoint
   - [ ] Implement `/analytics/bias-distribution` endpoint
   - [ ] Implement `/analytics/framework-heatmap` endpoint
   - [ ] Optimize queries with materialized views
   - [ ] Add caching layer (Redis optional)

2. **Frontend**:
   - [ ] Create `/dashboard` page layout
   - [ ] Build `SentimentLineChart` component
   - [ ] Build `BiasStackedArea` component
   - [ ] Build `SentimentHeatmap` component
   - [ ] Add date range pickers
   - [ ] Implement topic/framework selectors

3. **Testing**:
   - [ ] Test chart rendering with various data sizes
   - [ ] Verify heatmap tooltip accuracy
   - [ ] Test date range filtering

---

### **Phase 3: Home Feed & Article Analysis** (Week 6-8)
**Goal**: Personalized feed with deep article insights

#### Tasks:
1. **Backend**:
   - [ ] Implement `/articles/{id}/coverage-comparison` endpoint
   - [ ] Implement `/articles/{id}/context` endpoint
   - [ ] Add feed filtering by user preferences
   - [ ] Implement sorting (newest, most relevant, controversial)

2. **Frontend**:
   - [ ] Create `/feed` page with filter UI
   - [ ] Build `ArticleCard` component
   - [ ] Create `/article/[id]` page layout
   - [ ] Build coverage comparison section
   - [ ] Build context timeline component
   - [ ] Add framework visualization on article page

3. **Testing**:
   - [ ] Test feed filtering logic
   - [ ] Verify coverage comparison clustering
   - [ ] Test article context rendering

---

### **Phase 4: Challenge System** (Week 9-11)
**Goal**: Engage users with viewpoint challenges

#### Tasks:
1. **Backend**:
   - [ ] Create challenge tables (migrations)
   - [ ] Implement `/challenges/current` endpoint
   - [ ] Implement `/challenges/{id}/respond` endpoint
   - [ ] Implement `/challenges/history` endpoint
   - [ ] Create challenge generation service (weekly job)
   - [ ] Implement curated reflection selection

2. **Frontend**:
   - [ ] Create `/challenge` page with response UI
   - [ ] Build reflection submission form
   - [ ] Create `/challenge/history` page
   - [ ] Add challenge notification to navbar

3. **Email**:
   - [ ] Design Monday reflection email template
   - [ ] Implement reflection email service

4. **Testing**:
   - [ ] Test challenge flow (Monday → Sunday)
   - [ ] Verify view-change detection
   - [ ] Test reflection curation

---

### **Phase 5: Advanced Analytics** (Week 12-14)
**Goal**: Claim recurrence and advanced visualizations

#### Tasks:
1. **Backend**:
   - [ ] Implement `/analytics/claim-recurrence` endpoint
   - [ ] Build claim matching algorithm (fuzzy matching)
   - [ ] Optimize statistic verification queries

2. **Frontend**:
   - [ ] Create `/analytics` page
   - [ ] Build claim recurrence timeline viz
   - [ ] Add heatmap time evolution (animation)
   - [ ] Implement framework positioning chart

3. **Testing**:
   - [ ] Test claim matching accuracy
   - [ ] Verify heatmap animation performance

---

### **Phase 6: Polish & Optimization** (Week 15-16)
**Goal**: Performance, UX, and documentation

#### Tasks:
1. **Performance**:
   - [ ] Add React Query for data caching
   - [ ] Implement virtualized lists for long feeds
   - [ ] Optimize heatmap rendering (Canvas instead of SVG)
   - [ ] Add skeleton loaders

2. **UX**:
   - [ ] Add onboarding tour for new users
   - [ ] Implement dark mode
   - [ ] Add keyboard shortcuts
   - [ ] Create mobile-responsive layouts

3. **Documentation**:
   - [ ] Write user guide
   - [ ] Create API documentation
   - [ ] Add code comments

---

## 🎨 Design System

### Color Palette
```css
/* Sentiment Colors */
--sentiment-negative: #ef4444;  /* Red */
--sentiment-neutral: #64748b;   /* Gray */
--sentiment-positive: #10b981;  /* Green */

/* Political Lean Colors */
--lean-left: #3b82f6;    /* Blue */
--lean-center: #64748b;  /* Gray */
--lean-right: #ef4444;   /* Red */

/* Credibility Colors */
--trust-high: #10b981;   /* Green (8-10) */
--trust-medium: #f59e0b; /* Orange (6-8) */
--trust-low: #ef4444;    /* Red (<6) */

/* Framework Colors */
--framework-1: #8b5cf6;  /* Purple */
--framework-2: #ec4899;  /* Pink */
```

### Typography
```css
/* Headings */
h1: text-4xl font-bold tracking-tight
h2: text-3xl font-semibold
h3: text-2xl font-semibold

/* Body */
body: text-base leading-relaxed
small: text-sm text-gray-600
```

---

## 📝 User Flows

### 1. **New User Onboarding**
```
1. Landing Page → Sign Up
2. Email Verification
3. Welcome Modal → "Let's customize your feed"
4. Topic Selection (5 topics minimum)
5. Source Selection (choose preset or manual)
6. Newsletter Preview → "Send me my first issue!"
7. Dashboard Tour
```

### 2. **Weekly Challenge Flow**
```
Monday 7am:
- Email: "This week's challenge: [Question]"
- User clicks → /challenge
- Submits initial stance

Tuesday-Saturday:
- Daily newsletter includes 1-2 challenge articles
- Mixed stances (agree/disagree)

Sunday 7am:
- Email: "Reflect on your stance"
- User submits final stance + optional reflection

Monday 7am (next week):
- Email: "Reflections from last week's challenge"
- 5-10 curated anonymous reflections
- Aggregated stats (e.g., "32% changed their view")
```

---

## 🚀 Success Metrics

### User Engagement
- **DAU/MAU ratio** (target: >30%)
- **Avg session duration** (target: >5 min)
- **Newsletter open rate** (target: >40%)

### Feature Adoption
- **Dashboard visits/week** (target: >3)
- **Challenge participation rate** (target: >50%)
- **Source customization rate** (target: >70%)

### Discourse Impact
- **View changes per challenge** (target: >25%)
- **Reflection submission rate** (target: >40%)
- **Multi-source article views** (target: >60%)

---

## 🔒 Security & Privacy

### Challenge Reflections
- Reflections are **anonymous** when curated
- Users can opt out of reflection curation
- Only featured reflections are shared

### Data Privacy
- Analytics data is **user-specific** (not shared)
- Source preferences are **private**
- Export user data on request (GDPR)

---

## 📚 External Integrations

### Bias Aggregator Links
- **AllSides**: https://www.allsides.com/media-bias/media-bias-ratings
- **Media Bias Fact Check**: https://mediabiasfactcheck.com/
- **Ad Fontes Media**: https://adfontesmedia.com/

### Implementation
```typescript
// Add to source profile page
<a
  href={`https://www.allsides.com/news-source/${source.name.toLowerCase()}`}
  target="_blank"
  className="text-blue-600 hover:underline"
>
  View {source.name} on AllSides →
</a>
```

---

## ✅ Definition of Done

### For Each Feature
- [ ] Backend endpoints implemented & tested
- [ ] Frontend components built & responsive
- [ ] TypeScript types defined
- [ ] Error handling implemented
- [ ] Loading states added
- [ ] Accessibility (WCAG AA) verified
- [ ] Documentation updated

---

## 🎯 Next Steps

1. **Review this plan** with stakeholders
2. **Prioritize phases** based on user feedback
3. **Set up project board** (GitHub Projects or Jira)
4. **Begin Phase 1** implementation

---

**Last Updated**: 2025-10-03
**Status**: Planning Complete ✅
**Estimated Timeline**: 16 weeks
