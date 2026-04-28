# Pulse News Aggregator - System Architecture

> **Related Documentation:**
> - [API Reference](../api/API.md) - Complete REST API documentation
> - [Development Setup](../development/SETUP.md) - Get the system running locally
> - [Database Schema](#database-schema) - Detailed database design below
> - [Statistics Verification V2](STATISTICS_VERIFICATION_V2_PLAN.md) - Advanced stats pipeline

## 📐 High-Level Overview

```
┌─────────────┐
│   Users     │
│  (Email +   │
│   Web UI)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│            Next.js Frontend (Port 3000)         │
│  - Signup/Login                                 │
│  - Topic Preferences                            │
│  - Newsletter Preview                           │
└────────────────────┬────────────────────────────┘
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend (Port 8000)             │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │         Routes (API Endpoints)           │  │
│  │  /health, /articles, /auth, /preferences│  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│  ┌──────────────▼───────────────────────────┐  │
│  │            Services Layer                │  │
│  │  - RSS Scraper                           │  │
│  │  - Article Extractor (trafilatura)       │  │
│  │  - AI Analyzer (Claude)                  │  │
│  │  - Framework Generator                   │  │
│  │  - Newsletter Builder                    │  │
│  │  - Email Sender (Resend)                 │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│  ┌──────────────▼───────────────────────────┐  │
│  │       APScheduler (Background Jobs)      │  │
│  │  - Scrape RSS (every 3 hours)            │  │
│  │  - Extract Articles (every 4 hours)      │  │
│  │  - Update Frameworks (daily 2am)         │  │
│  │  - Send Newsletters (daily 7am)          │  │
│  └──────────────┬───────────────────────────┘  │
└─────────────────┼───────────────────────────────┘
                  │
                  ▼
        ┌─────────────────┐
        │   PostgreSQL    │
        │   (Port 5432)   │
        └─────────────────┘
```

## 🔄 Data Flow

### 1. Article Ingestion Pipeline

```
RSS Feeds → Scraper → Database → Extractor → Full Article Content
   │                    │                          │
   │                    │                          │
   ▼                    ▼                          ▼
[8 News Sources]    [Article Table]         [AI Analyzer]
                   (status: PENDING)              │
                                                  ▼
                                          [ArticleAnalysis Table]
                                          - Summary (100 words)
                                          - Sentiment (-10 to +10)
                                          - Political lean
                                          - Key stats
                                                  │
                                                  ▼
                                          [Framework Mapper]
                                                  │
                                                  ▼
                                          [article_frameworks]
                                          (links articles to debates)
```

### 2. Framework Evolution

```
Week 1:
[10 Seed Frameworks] → Database
   (hand-curated)

Week 2+:
[100+ Articles] → AI Analysis → Cluster Analysis → New Frameworks
                                                          │
                                                          ▼
                                                   [Merge & Dedupe]
                                                          │
                                                          ▼
                                                   [Framework Table]
                                                   (growing library)
```

### 3. Newsletter Generation

```
User Preferences → Topic Selection → Article Filtering
      │                                     │
      ▼                                     ▼
[user_topic_preferences]           [Filtered Articles]
      │                                     │
      │                                     ▼
      │                            [Top 5 Articles]
      │                                     │
      └──────────────┬──────────────────────┘
                     ▼
            [Newsletter Builder]
                     │
                     ├─→ Article Summaries
                     ├─→ Bias Indicators
                     ├─→ Framework Connections
                     └─→ "The Bigger Picture" Section
                     │
                     ▼
            [Jinja2 Template]
                     │
                     ▼
            [HTML Email] → Resend API → User's Inbox
```

## 🗄️ Database Schema

### Core Tables

```
sources                              topics
├── id (PK)                         ├── id (PK)
├── name                            ├── name
├── url                             ├── description
├── rss_feed_url                    └── is_active_default
├── description                              │
├── trust_score                              │
└── is_active                                │
         │                                   │
         │         source_topics              │
         └────────┬─ source_id (FK)          │
                  └─ topic_id (FK) ───────────┘

articles                           article_analysis
├── id (PK)                        ├── id (PK)
├── source_id (FK)                 ├── article_id (FK) 1:1
├── title                          ├── summary
├── url (unique)                   ├── sentiment_score
├── author                         ├── political_lean
├── published_at                   ├── bias_indicators
├── content_text                   ├── key_stats
├── word_count                     └── processing_cost
├── extraction_method
├── topic_category
└── processing_status
         │
         │         article_frameworks
         └────────┬─ article_id (FK)
                  ├─ framework_id (FK)
                  ├─ relevance_score
                  ├─ position_on_axis
                  └─ ai_explanation
                           │
                           ▼
                    frameworks
                    ├── id (PK)
                    ├── name
                    ├── description
                    ├── axis_description
                    ├── left_position
                    ├── right_position
                    ├── article_count
                    ├── last_active
                    └── is_seed

users                              newsletters
├── id (PK)                        ├── id (PK)
├── email (unique)                 ├── user_id (FK)
├── email_verified                 ├── subject
├── hashed_password                ├── sent_at
├── subscription_tier              ├── article_ids (JSON)
└── is_active                      ├── framework_ids (JSON)
         │                         ├── email_opened
         │                         └── links_clicked
         │
         └────────┬─ user_id (FK)
                  ├─ topic_id (FK)
                  ├─ priority_level
                  └─ include_in_newsletter
                  (user_topic_preferences)
```

## ⚙️ Service Architecture

### Backend Services

#### 1. RSS Scraper Service
```python
Input:  Active sources from database
Process:
  - Fetch RSS feed
  - Parse with feedparser
  - Check for duplicates (by URL)
  - Extract metadata
Output: New Article records (status: PENDING)
Runs:   Every 3 hours
```

#### 2. Article Extractor Service
```python
Input:  Articles with status=PENDING
Process:
  - Try trafilatura (primary)
  - Fallback to readability-lxml
  - Extract full text
  - Calculate word count
Output: Updated articles with content_text
Runs:   Every 4 hours
```

#### 3. AI Analyzer Service
```python
Input:  Articles with content, no analysis
Process:
  - Batch 5 articles together
  - Send to OpenAI GPT-4o-mini API
  - Extract: summary, sentiment, lean, stats
Output: ArticleAnalysis records
Cost:   ~$0.002 per article
Runs:   Every 6 hours
```

#### 4. Framework Generator Service
```python
Input:  Recent analyzed articles
Process:
  - Map to existing frameworks
  - Calculate relevance & position
  - Weekly (Sundays): discover new frameworks
Output: ArticleFramework links
Runs:   Daily at 2:00 AM
```

#### 5. Newsletter Builder Service
```python
Input:  User preferences + recent articles
Process:
  - Filter by user topics
  - Select top 5 articles
  - Find related frameworks
  - Generate "Bigger Picture" section
  - Render Jinja2 template
  - Send via Resend API
Output: Newsletter records
Runs:   Daily at 10:20 AM PST
Rate:   3,000/month (free tier)
```

#### 6. Statistics Verification Service
```python
Input:  Articles with unverified statistics
Process:
  - Extract statistics from article text
  - Trace sources (V2 pipeline)
  - Rate source credibility
  - Check fact-checking APIs
Output: StatisticVerification records
Runs:   Every 6 hours
```

#### 7. Article Clustering Service
```python
Input:  Articles without cluster assignment
Process:
  - Compare article similarity (embedding-based)
  - Group similar articles (same story, different sources)
  - Create clusters for cross-source comparison
Output: ArticleCluster + ArticleClusterMember records
Runs:   Every 4 hours
```

#### 8. Context Generation Service
```python
Input:  High-priority articles without context
Process:
  - Generate background information
  - Identify key players
  - Create timeline
  - Explain significance
  - Use AI (OpenAI GPT-4o-mini)
Output: ArticleContext records
Runs:   Every 8 hours
Cost:   Expensive (limited to 5 articles per run)
```

## 🔐 Authentication Flow

```
User Registration:
POST /auth/register
    ↓
[Create User] → Hash password (bcrypt)
    ↓
[Send Verification Email]
    ↓
User clicks link
    ↓
POST /auth/verify → Set email_verified=true
    ↓
[User Active]

User Login:
POST /auth/login
    ↓
[Verify password]
    ↓
[Generate JWT token] → includes user_id, exp
    ↓
Return token to client
    ↓
Client sends token in Authorization header
    ↓
[Middleware validates JWT] → Allows access
```

## 🌐 API Endpoints

### Public Routes
```
GET  /health              - Health check
POST /auth/signup         - User registration
POST /auth/login          - User login
POST /auth/verify         - Email verification
GET  /articles            - Browse articles (public subset)
GET  /frameworks          - View ethical frameworks
```

### Protected Routes (require JWT)
```
GET  /auth/me             - Get current user
PUT  /preferences         - Update topic preferences
GET  /newsletters/latest  - Get latest newsletter
GET  /newsletters/history - Newsletter archive
```

### Admin Routes (require admin role)
```
GET  /admin/stats         - System statistics
POST /admin/scrape        - Trigger manual scrape
POST /admin/sources       - Add new source
PUT  /admin/sources/:id   - Update source
```

## 📊 Monitoring & Observability

### Key Metrics to Track

```
Scraping Metrics:
- Articles scraped per hour
- RSS feed failures
- Duplicate detection rate
- Average scrape duration

Extraction Metrics:
- Success rate by method (trafilatura vs readability)
- Average extraction time
- Content quality (word count distribution)
- Failed extraction reasons

AI Metrics:
- API cost per article
- Token usage (input/output)
- Batch processing efficiency
- Framework mapping accuracy

Email Metrics:
- Open rate
- Click-through rate
- Bounce rate
- Unsubscribe rate

System Health:
- Database query performance
- Job execution time
- Error rates by service
- API response times
```

### Logging Strategy

```
INFO level:
- Job starts/completions
- Article counts
- User signups

WARNING level:
- RSS feed timeouts
- Extraction fallbacks
- API rate limiting

ERROR level:
- Database connection failures
- AI API errors
- Email sending failures
```

## 🚀 Deployment Architecture

### Phase 1: MVP (Free Tier)
```
Railway + Supabase
├── Railway backend service (FastAPI, Docker)
├── Railway frontend service (TanStack Start SSR)
└── Supabase Postgres (schema-isolated app role)

External:
├── Resend (3k emails/month free)
└── OpenAI API ($5 credit)

Cost: varies by Railway/Supabase plan + usage
```

### Phase 2: Growth (DigitalOcean)
```
DigitalOcean Droplet ($12/mo)
├── Docker Compose
│   ├── FastAPI Backend
│   ├── PostgreSQL
│   └── Redis (caching)

External:
├── Resend (Paid tier ~$5/mo)
└── OpenAI API (~$10-20/mo)

Cost: $30-50/month
```

### Phase 3: Scale (Multi-server)
```
Load Balancer
├── App Server 1 (FastAPI)
├── App Server 2 (FastAPI)
└── App Server 3 (Background jobs)

Database Cluster
├── PostgreSQL Primary
├── PostgreSQL Read Replica 1
└── PostgreSQL Read Replica 2

Caching Layer
└── Redis Cluster

CDN
└── Static assets (images, CSS, JS)

Cost: $100-300/month
```

## 🔧 Tech Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI | REST API framework |
| **ORM** | SQLModel | Database models + validation |
| **Database** | PostgreSQL | Relational data storage |
| **Migrations** | Alembic | Schema version control |
| **Scheduling** | APScheduler | Background jobs |
| **Scraping** | feedparser | RSS feed parsing |
| **Extraction** | trafilatura | Article content extraction |
| **AI** | OpenAI GPT-4o-mini | Text analysis & generation |
| **Email** | Resend | Email delivery |
| **Templates** | Jinja2 | Email HTML rendering |
| **Auth** | JWT | Stateless authentication |
| **Frontend** | Next.js | React framework (SSR) |
| **Container** | Docker | Development & deployment |
| **Language** | Python 3.11 | Backend logic |
| **Language** | TypeScript | Frontend logic |

## 🎯 Scaling Considerations

### Database Optimization
- **Indexes**: Add on frequently queried fields (url, published_at, processing_status)
- **Partitioning**: Partition articles table by month if >1M records
- **Read Replicas**: For article browsing (95% reads)
- **Connection Pooling**: SQLAlchemy pool_size=20

### Caching Strategy
- **Redis**: Cache framework lists, article summaries (TTL: 1 hour)
- **HTTP Caching**: ETag headers for article endpoints
- **Database**: MATERIALIZED VIEWS for complex queries

### Rate Limiting
- **Scraping**: 1 req/sec per source
- **AI API**: Batch size=5, max 100 batches/hour
- **Email**: 50/hour (respect Resend limits)
- **Public API**: 100 req/min per IP

### Job Distribution
- **Single Server**: APScheduler (fine for <1000 users)
- **Multi-Server**: Celery + Redis (for >1000 users)
- **Job Priorities**: High (newsletter), Medium (extraction), Low (framework updates)

## 📈 Growth Roadmap

### V1.0 (MVP) - Weeks 1-5
- Core pipeline working
- Email newsletter functional
- 50 beta users
- Basic web interface

### V1.5 (Enhanced) - Weeks 6-10
- Stats verification APIs
- Improved framework mapping
- User analytics dashboard
- 500 users

### V2.0 (Monetization) - Weeks 11-16
- Premium tier (personalized map)
- Advanced filtering
- Mobile app (React Native)
- 5,000 users

### V3.0 (Scale) - Months 4-6
- Multi-language support
- Real-time updates (WebSockets)
- Community features
- 50,000 users

---

**This architecture is designed to:**
- ✅ Start simple and cheap (<$100/month)
- ✅ Scale incrementally as users grow
- ✅ Maintain code quality and testability
- ✅ Leverage AI cost-effectively
- ✅ Provide clear upgrade paths
